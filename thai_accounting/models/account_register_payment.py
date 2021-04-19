# -*- coding: utf-8 -*-
# Copyright (C) 2016-Today  itaas.co.th

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_is_zero, float_compare
import odoo.addons.decimal_precision as dp
from itertools import groupby
from collections import defaultdict
from datetime import datetime, date

MAP_INVOICE_TYPE_PARTNER_TYPE = {
    'out_invoice': 'customer',
    'out_refund': 'customer',
    'in_invoice': 'supplier',
    'in_refund': 'supplier',
}
# Since invoice amounts are unsigned, this is how we know if money comes in or goes out
MAP_INVOICE_TYPE_PAYMENT_SIGN = {
    'out_invoice': 1,
    'in_refund': 1,
    'in_invoice': -1,
    'out_refund': -1,
}

class account_register_payment(models.Model):
    _name = 'account.register.payment'
    _description = 'Register Payment'

    payment_date = fields.Date(required=True, default=fields.Date.context_today)
    journal_id = fields.Many2one('account.journal', required=True, domain=[('type', 'in', ('bank', 'cash'))])
    payment_method_id = fields.Many2one('account.payment.method', string='Payment Method Type', required=True,
                                        help="Manual: Get paid by cash, check or any other method outside of Odoo.\n"
                                        "Electronic: Get paid automatically through a payment acquirer by requesting a transaction on a card saved by the customer when buying or subscribing online (payment token).\n"
                                        "Check: Pay bill by check and print it from Odoo.\n"
                                        "Batch Deposit: Encase several customer checks at once by generating a batch deposit to submit to your bank. When encoding the bank statement in Odoo, you are suggested to reconcile the transaction with the batch deposit.To enable batch deposit, module account_batch_payment must be installed.\n"
                                        "SEPA Credit Transfer: Pay bill from a SEPA Credit Transfer file you submit to your bank. To enable sepa credit transfer, module account_sepa must be installed ")
    invoice_ids = fields.Many2many('account.move', 'account_invoice_payment_rel_register', 'payment_id', 'invoice_id', string="Invoices", copy=False, readonly=True)
    group_payment = fields.Boolean(help="Only one payment will be created by partner (bank)/ currency.",default=True)

    ############## add require for payment ###############
    payment_type = fields.Selection(
        [('outbound', 'Send Money'), ('inbound', 'Receive Money'), ('transfer', 'Internal Transfer')],
        string='Payment Type', require=False, readonly=True, states={'draft': [('readonly', False)]})
    payment_option = fields.Selection(
        [('full', 'Full Payment without Deduction'), ('partial', 'Full Payment with Deduction')],
        default='full', required=True, string='Payment Option')
    post_diff_acc = fields.Selection([('single', 'Single Account'), ('multi', 'Multiple Accounts')], default='single',
                                     string='Post Difference In To')
    writeoff_multi_acc_ids = fields.One2many('writeoff.accounts', 'payment_wizard_id', string='Write Off Accounts')
    # wht = fields.Boolean(string="WHT")
    payment_difference_handling = fields.Selection([('open', 'Keep open'), ('reconcile', 'Mark invoice as fully paid')],
                                                   default='open', string="Payment Difference", copy=False)
    payment_difference = fields.Float(compute='_compute_payment_difference', readonly=True)
    writeoff_account_id = fields.Many2one('account.account', string="Difference Account",
                                          domain=[('deprecated', '=', False)], copy=False)

    ####
    # purchase_or_sale = fields.Selection([('purchase', 'Purchase'), ('sale', 'Sale')])
    #######
    amount = fields.Float(string='Payment Amount')
    currency_id = fields.Many2one('res.currency', string='Currency', default=lambda self: self.env.company.currency_id)
    amount_untaxed = fields.Float(string='Payment Untaxed Amount')
    remark = fields.Char(string="Payment Remark")
    bank_cheque = fields.Boolean(string='Is Cheque', related='journal_id.bank_cheque')
    # this is new bank list from res.bank
    cheque_bank = fields.Many2one('res.bank', string="Bank")
    cheque_branch = fields.Char(string="Branch")
    cheque_number = fields.Char(string="Cheque Number")
    cheque_date = fields.Date(string="Cheque Date")
    require_write_off_account = fields.Boolean(string='Require write off account')
    current_account_id = fields.Many2one('account.account', string='Current Account', compute='get_current_account_id')
    is_change_account = fields.Boolean(string='Change Account')
    payment_account_id = fields.Many2one('account.account', string='New Account')

    @api.model
    def default_get(self, fields):
        rec = super(account_register_payment, self).default_get(fields)
        print ('-REC---')
        print (rec)
        active_ids = self._context.get('active_ids')
        if not active_ids:
            return rec
        invoices = self.env['account.move'].browse(active_ids)

        # Check all invoices are open
        if any(invoice.state != 'posted' or invoice.invoice_payment_state != 'not_paid' or not invoice.is_invoice() for invoice in invoices):
            raise UserError(_("You can only register payments for open invoices"))

        if any(inv.company_id != invoices[0].company_id for inv in invoices):
            raise UserError(_("You can only register at the same time for payment that are all from the same company"))
        # Check the destination account is the same
        destination_account = invoices.line_ids.filtered(lambda line: line.account_internal_type in ('receivable', 'payable')).mapped('account_id')
        if len(destination_account) > 1:
            raise UserError(_('There is more than one receivable/payable account in the concerned invoices. You cannot group payments in that case.'))
        if 'invoice_ids' not in rec:
            rec['invoice_ids'] = [(6, 0, invoices.ids)]
        if 'journal_id' not in rec:
            rec['journal_id'] = self.env['account.journal'].search([('company_id', '=', self.env.company.id), ('type', 'in', ('bank', 'cash'))], limit=1).id
        if 'payment_method_id' not in rec:
            amount = self.env['account.payment']._compute_payment_amount(invoices, invoices[0].currency_id,
                                                                         invoices[0].journal_id,
                                                                         datetime.today().date())
            if amount >= 0:
                domain = [('payment_type', '=', 'inbound')]
                rec['payment_type'] = 'inbound'
            else:
                domain = [('payment_type', '=', 'outbound')]
                rec['payment_type'] = 'outbound'
            rec['payment_method_id'] = self.env['account.payment.method'].search(domain, limit=1).id

        total_untaxed = sum(inv.amount_untaxed * MAP_INVOICE_TYPE_PAYMENT_SIGN[inv.type] for inv in invoices)
        rec['amount_untaxed'] = abs(total_untaxed)
        print ('FINAL REC')
        print (rec)
        return rec

    @api.onchange('journal_id', 'invoice_ids')
    def _onchange_journal(self):
        active_ids = self._context.get('active_ids')
        invoices = self.env['account.move'].browse(active_ids)
        if self.journal_id and invoices:
            if invoices[0].is_inbound():
                domain_payment = [('payment_type', '=', 'inbound'), ('id', 'in', self.journal_id.inbound_payment_method_ids.ids)]
            else:
                domain_payment = [('payment_type', '=', 'outbound'), ('id', 'in', self.journal_id.outbound_payment_method_ids.ids)]
            domain_journal = [('type', 'in', ('bank', 'cash')), ('company_id', '=', invoices[0].company_id.id)]
            return {'domain': {'payment_method_id': domain_payment, 'journal_id': domain_journal}}
        return {}

    def _prepare_payment_vals(self, invoices):
        '''Create the payment values.

        :param invoices: The invoices/bills to pay. In case of multiple
            documents, they need to be grouped by partner, bank, journal and
            currency.
        :return: The payment values as a dictionary.
        '''
        # amount = self.env['account.payment']._compute_payment_amount(invoices, invoices[0].currency_id, self.journal_id, self.payment_date)
        amount = self.amount
        writeoff_multi_ids = []
        for writeoff_multi in self.writeoff_multi_acc_ids:
            writeoff_multi_ids.append(writeoff_multi.id)

        print ('Payment TYPE--')
        print (self.payment_type)

        values = {
            'journal_id': self.journal_id.id,
            'payment_method_id': self.payment_method_id.id,
            'payment_date': self.payment_date,
            'communication': " ".join(i.invoice_payment_ref or i.ref or i.name for i in invoices),
            'invoice_ids': [(6, 0, invoices.ids)],
            'payment_type': self.payment_type,
            'amount': abs(amount),
            'currency_id': invoices[0].currency_id.id,
            'partner_id': invoices[0].commercial_partner_id.id,
            'partner_type': MAP_INVOICE_TYPE_PARTNER_TYPE[invoices[0].type],
            'partner_bank_account_id': invoices[0].invoice_partner_bank_id.id,
            'payment_account_id': self.payment_account_id.id,
            'post_diff_acc': self.post_diff_acc,
            'remark':self.remark,
            'payment_difference_handling': self.payment_difference_handling,
            'payment_difference': self.payment_difference,
            'writeoff_multi_acc_ids': [(4, writeoff_multi.id, None) for writeoff_multi in
                                       self.writeoff_multi_acc_ids],
            'amount_untaxed': self.amount_untaxed,
            'remark': self.remark,
            'cheque_bank': self.cheque_bank.id,
            'cheque_branch': self.cheque_branch,
            'cheque_number': self.cheque_number,
            'cheque_date': self.cheque_date,
        }

        # _prepare_payment_vals

        return values




    def get_payments_vals(self):
        '''Compute the values for payments.

        :return: a list of payment values (dictionary).
        '''
        grouped = defaultdict(lambda: self.env["account.move"])
        for inv in self.invoice_ids:
            if self.group_payment:
                grouped[(inv.commercial_partner_id, inv.currency_id, inv.invoice_partner_bank_id, MAP_INVOICE_TYPE_PARTNER_TYPE[inv.type])] += inv
            else:
                grouped[inv.id] += inv
        return [self._prepare_payment_vals(invoices) for invoices in grouped.values()]

    def create_payments(self):
        '''Create payments according to the invoices.
        Having invoices with different commercial_partner_id or different type
        (Vendor bills with customer invoices) leads to multiple payments.
        In case of all the invoices are related to the same
        commercial_partner_id and have the same type, only one payment will be
        created.

        :return: The ir.actions.act_window to show created payments.
        '''
        Payment = self.env['account.payment']
        detail = self.get_payments_vals()
        print ('--DETAIL---')
        print (detail)
        payments = Payment.create(self.get_payments_vals())
        payments.post()

        action_vals = {
            'name': _('Payments'),
            'domain': [('id', 'in', payments.ids), ('state', '=', 'posted')],
            'res_model': 'account.payment',
            'view_id': False,
            'type': 'ir.actions.act_window',
        }
        if len(payments) == 1:
            action_vals.update({'res_id': payments[0].id, 'view_mode': 'form'})
        else:
            action_vals['view_mode'] = 'tree,form'
        return action_vals





    @api.depends('journal_id')
    def get_current_account_id(self):
        if self.payment_type in ('outbound',
                                 'transfer') and self.journal_id.default_debit_account_id.id:
            self.current_account_id = self.journal_id.default_debit_account_id.id
        else:
            self.current_account_id = self.journal_id.default_credit_account_id.id

    @api.onchange('payment_difference')
    def check_require_write_off_account(self):
        amount = 0
        if self.writeoff_multi_acc_ids:
            for payment in self.writeoff_multi_acc_ids:
                amount += payment.amount
        precision = self.env['decimal.precision'].precision_get('Product Price')

        if float_compare(float(abs(self.payment_difference)), float(amount), precision_digits=precision) != 0:
            self.require_write_off_account = True
        else:
            self.require_write_off_account = False

    @api.depends('amount', 'payment_date')
    def _compute_payment_difference(self):
        context = dict(self._context or {})
        active_model = context.get('active_model')
        active_ids = context.get('active_ids')
        invoice_ids = self.env[active_model].browse(active_ids)
        total_invoice_amount = self.env['account.payment']._compute_payment_amount(invoice_ids, invoice_ids[0].currency_id, self.journal_id,
                                                                     self.payment_date)

        if len(invoice_ids) == 0:
            return
        if invoice_ids[0].type in ['in_invoice', 'out_refund']:
            # print ('supplier')
            # print (self.amount)
            # print (total_invoice_amount)
            # print (self.payment_difference)
            self.payment_difference = self.amount - abs(total_invoice_amount)
            # print (self.payment_difference)
        else:
            # print('customer')
            # print(total_invoice_amount)
            # print(self.amount)
            # print(self.payment_difference)
            self.payment_difference = total_invoice_amount - self.amount
            # print (self.payment_difference)

    @api.onchange('payment_option')
    def onchange_payment_option(self):
        if self.payment_option == 'full':
            self.payment_difference_handling = 'open'
            self.post_diff_acc = 'single'
        else:
            self.payment_difference_handling = 'reconcile'
            self.post_diff_acc = 'multi'

#     # calculate writeoff amount
    @api.onchange('writeoff_multi_acc_ids')
    def onchange_writeoff_multi_accounts(self):
        diff_amount = 0
        context = dict(self._context or {})
        active_model = context.get('active_model')
        active_ids = context.get('active_ids')
        invoice_ids = self.env[active_model].browse(active_ids)
        if self.writeoff_multi_acc_ids:
            print ('writeoff_multi_acc_ids')
            diff_amount = sum([line.amount for line in self.writeoff_multi_acc_ids])
            print (diff_amount)

            total_invoice_amount = self.env['account.payment']._compute_payment_amount(invoice_ids,
                                                                                       invoice_ids[0].currency_id,
                                                                                       self.journal_id,
                                                                                       self.payment_date)
            print (total_invoice_amount)

            self.amount = abs(total_invoice_amount) - diff_amount
        else:

            total_invoice_amount = self.env['account.payment']._compute_payment_amount(invoice_ids,
                                                                                       invoice_ids[0].currency_id,
                                                                                       self.journal_id,
                                                                                       self.payment_date)
            print(total_invoice_amount)
            self.amount = abs(total_invoice_amount) - diff_amount
