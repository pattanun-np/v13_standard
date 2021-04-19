# -*- coding: utf-8 -*-
# Copyright (C) 2016-Today  itaas.co.th

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_is_zero, float_compare
import odoo.addons.decimal_precision as dp
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

class refund_record_ids(models.Model):
    _name = 'payment.refund.record'

    invoice_id = fields.Many2one('account.move', string='Invoice')
    amount = fields.Float(string='Payment Amount')
    date = fields.Date(string='Date')
    payment_id = fields.Many2one('account.payment', string='Payment')

class account_payment(models.Model):
    _inherit = "account.payment"

    payment_option = fields.Selection(
        [('full', 'Full Payment without Deduction'), ('partial', 'Full Payment with Deduction')],
        default='full', required=True, string='Payment Option')

    post_diff_acc = fields.Selection([('single', 'Single Account'), ('multi', 'Multiple Accounts')], default='single',
                                     string='Post Difference In To')
    writeoff_multi_acc_ids = fields.One2many('writeoff.accounts', 'payment_id', string='Write Off Accounts')

    ###########REMOVE ########################################
    purchase_or_sale = fields.Selection([('purchase', 'Purchase'), ('sale', 'Sale')])
    payment_cut_off_amount = fields.Float(string='Cut Off Payment Amount', digits='Account',
                                          readonly=True, compute="get_payment_cut_off_amount")
    current_account_id = fields.Many2one('account.account', string='Current Account', compute='get_current_account_id')
    is_change_account = fields.Boolean(string='Change Account')
    payment_account_id = fields.Many2one('account.account', string='New Account')
    ###########--------#######################################
    amount_untaxed = fields.Monetary(string='Full Amount')
    require_write_off = fields.Boolean(string='Require write off account')
    remark = fields.Char(string='Payment Remark')
    ###########REMOVE ########################################
    wht = fields.Boolean(string="WHT")
    ################## About Cheque###############
    bank_cheque = fields.Boolean(string='Is Cheque', related='journal_id.bank_cheque')
    cheque_bank = fields.Many2one('res.bank', string="Bank")
    cheque_branch = fields.Char(string="Branch")
    cheque_number = fields.Char(string="Cheque Number")
    cheque_date = fields.Date(string="Cheque Date")
    cheque_reg_id = fields.Many2one('account.cheque.statement', string='Cheque Record')
    ################## About Cheque###############
    payment_refund_ids = fields.One2many('payment.refund.record','payment_id',string='Refund')

    all_invoice_count = fields.Integer(compute="_compute_reconciled_invoice_ids")

    @api.model
    def default_get(self, default_fields):

        # remove this due to default_get not only do default but also check invoice and cn could not mix together#
        # rec = super(account_payment, self).default_get(default_fields)                                         #
        ##########################################################################################################

        payment_type = self._context.get('default_payment_type')
        partner_type = self._context.get('default_partner_type')

        rec = {'move_name': False, 'payment_option': 'full', 'state': 'draft', 'writeoff_label': 'Write-Off','post_diff_acc': 'single','currency_id': self.env.user.company_id.currency_id.id,'payment_date':datetime.today(),'payment_difference_handling':'open','state':'draft'}
        if payment_type:
            rec.update({
                'payment_type': payment_type,
            })
        if partner_type:
            rec.update({
                'partner_type': partner_type,
            })


        active_ids = self._context.get('active_ids') or self._context.get('active_id')
        active_model = self._context.get('active_model')

        # Check for selected invoices ids
        if not active_ids or active_model != 'account.move':
            return rec

        invoices = self.env['account.move'].browse(active_ids).filtered(
            lambda move: move.is_invoice(include_receipts=True))

        # Check all invoices are open
        if not invoices or any(invoice.state != 'posted' for invoice in invoices):
            raise UserError(_("You can only register payments for open invoices"))

        #################################REMOVE THIS CONDITION by JA###################################
        # Check if, in batch payments, there are not negative invoices and positive invoices
        # dtype = invoices[0].type
        # for inv in invoices[1:]:
        #     if inv.type != dtype:
        #         if ((dtype == 'in_refund' and inv.type == 'in_invoice') or
        #                 (dtype == 'in_invoice' and inv.type == 'in_refund')):
        #             raise UserError(
        #                 _("You cannot register payments for vendor bills and supplier refunds at the same time."))
        #         if ((dtype == 'out_refund' and inv.type == 'out_invoice') or
        #                 (dtype == 'out_invoice' and inv.type == 'out_refund')):
        #             raise UserError(
        #                 _("You cannot register payments for customer invoices and credit notes at the same time-1."))
        ###############################################################################################
        amount = self._compute_payment_amount(invoices, invoices[0].currency_id, invoices[0].journal_id,
                                              rec.get('payment_date') or fields.Date.today())


        rec.update({
            'currency_id': invoices[0].currency_id.id,
            'amount': abs(amount),
            'payment_type': 'inbound' if amount > 0 else 'outbound',
            'partner_id': invoices[0].commercial_partner_id.id,
            'partner_type': MAP_INVOICE_TYPE_PARTNER_TYPE[invoices[0].type],
            'communication': invoices[0].invoice_payment_ref or invoices[0].ref or invoices[0].name,
            'invoice_ids': [(6, 0, invoices.ids)],
        })
        return rec



    def action_register_payment(self):
        active_ids = self.env.context.get('active_ids')
        if not active_ids:
            return ''
        print ('-------CONTEXT action_register_payment')
        print (self.env.context)

        return {
            'name': _('Register Payment'),
            'res_model': len(active_ids) == 1 and 'account.payment' or 'account.register.payment',
            'view_mode': 'form',
            'view_id': len(active_ids) != 1 and self.env.ref('thai_accounting.view_account_register_payment_form_multi').id or self.env.ref('account.view_account_payment_invoice_form').id,
            'context': self.env.context,
            'target': 'new',
            'type': 'ir.actions.act_window',
        }

    def post(self):
        for rec in self:
            if rec.invoice_ids.filtered(lambda x: x.type in ('out_refund','in_refund')):
                refund_move_ids = rec.invoice_ids.filtered(lambda x: x.type in ('out_refund', 'in_refund'))
                for refund_move in refund_move_ids:
                    val = {
                        'invoice_id': refund_move.id,
                        'amount': refund_move.amount_residual,
                        'date': rec.payment_date,
                        'payment_id': rec.id,
                    }
                    print ('VAL REFUND RECORD')
                    print (val)
                    self.env['payment.refund.record'].create(val)

        res = super(account_payment, self).post()
        return res


    @api.depends('move_line_ids.matched_debit_ids', 'move_line_ids.matched_credit_ids')
    def _compute_reconciled_invoice_ids(self):
        super(account_payment, self)._compute_reconciled_invoice_ids()
        for rec in self:
            if rec.invoice_ids:
                rec.all_invoice_count = len(rec.invoice_ids)
            else:
                rec.all_invoice_count = 0

    def _get_invoice_payment_amount(self, inv):

        if inv.type in ('out_invoice','in_invoice'):
            amount = super(account_payment, self)._get_invoice_payment_amount(inv)

            for data in inv._get_reconciled_info_JSON_values():
                print ('DATA--')
                print (data)
                payment_refund_id = self.payment_refund_ids.filtered(lambda x: x.invoice_id.id == data['move_id'])
                if not data['account_payment_id'] and payment_refund_id:
                    amount += data['amount']
        else:
            amount = 0
            payment_refund_id = self.payment_refund_ids.filtered(lambda x: x.invoice_id == inv)
            if payment_refund_id:
                amount = payment_refund_id.amount * MAP_INVOICE_TYPE_PAYMENT_SIGN[inv.type]



        return amount



    def button_invoices_and_refund(self):
        return {
            'name': _('Paid Invoices'),
            'view_mode': 'tree,form',
            'res_model': 'account.move',
            'view_id': False,
            'views': [(self.env.ref('account.view_move_tree').id, 'tree'),
                      (self.env.ref('account.view_move_form').id, 'form')],
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', [x.id for x in self.invoice_ids])],
            'context': {'create': False},
        }


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
        print ('-------DIFF--')
        print(self.payment_difference)
        print(amount)
        if float_compare(float(abs(self.payment_difference)), float(abs(amount)), precision_digits=precision) != 0:
            print ('REQUIRE=TRUE')
            self.require_write_off = True
        else:
            print('REQUIRE=FALSE')
            self.require_write_off = False


    @api.onchange('payment_option')
    def onchange_payment_option(self):
        if self.payment_option == 'full':
            self.payment_difference_handling = 'open'
            self.post_diff_acc = 'single'
        else:
            self.payment_difference_handling = 'reconcile'
            self.post_diff_acc = 'multi'

        if self.invoice_ids[0].type in ['in_invoice', 'out_refund']:
            self.purchase_or_sale = 'purchase'
        else:
            self.purchase_or_sale = 'sale'

    #when add write off then new pay amount will be calculated by deduct from diff amount
    @api.onchange('writeoff_multi_acc_ids')
    # @api.multi
    def onchange_writeoff_multi_accounts(self):
        if self.writeoff_multi_acc_ids:
            diff_amount = sum([line.amount for line in self.writeoff_multi_acc_ids])
            self.amount = self.invoice_ids and self.invoice_ids[0].amount_residual - diff_amount
            self.amount_untaxed = sum([invoice.amount_untaxed for invoice in self.invoice_ids])
            # print "onchange_writeoff_multi_accounts(self):"
            # print self.amount_untaxed



    def _get_move_vals(self, journal=None):
        """ Return dict to create the payment move
        """
        journal = journal or self.journal_id
        if not journal.sequence_id:
            raise UserError(_('Configuration Error !'), _('The journal %s does not have a sequence, please specify one.') % journal.name)
        if not journal.sequence_id.active:
            raise UserError(_('Configuration Error !'), _('The sequence of journal %s is deactivated.') % journal.name)

        if self.move_name:
            name = self.move_name
        else:
            name = journal.with_context(ir_sequence_date=self.payment_date).sequence_id.next_by_id()

        wht_personal_company = False
        print ('---WRITE OFF--')
        print (self.writeoff_multi_acc_ids)

        if self.writeoff_multi_acc_ids:
            for woff_payment in self.writeoff_multi_acc_ids:
                if woff_payment.writeoff_account_id.wht and woff_payment.amt_percent and self.payment_type == 'outbound':
                    wht_personal_company = woff_payment.wht_personal_company


        return {
            'name': name,
            'date': self.payment_date,
            'ref': self.communication or '',
            'remark': self.remark,
            'cheque_bank': self.cheque_bank.id,
            'cheque_branch': self.cheque_branch,
            'cheque_number': self.cheque_number,
            'cheque_date': self.cheque_date,
            'company_id': self.company_id.id,
            'journal_id': journal.id,
            'wht_personal_company' : wht_personal_company,
        }

    #############call from account.payment post()############
    def _prepare_payment_moves(self):
        res = super(account_payment, self)._prepare_payment_moves()
        print('--RES BEFORE--')
        print(res)
        for payment in self:
            line_ids_new = []
            company_currency = payment.company_id.currency_id
            print ('WRITE OFF INFO')
            print (payment.writeoff_multi_acc_ids)
            if payment.payment_difference_handling == 'reconcile' and payment.writeoff_multi_acc_ids:
                print ('---GOT---writeoff_multi_acc_ids--')
                for line in (res[0]['line_ids']):

                    ###########Remove odoo standard write off as detection from write off account id, this will be ignore due to they use multi write off instead##
                    ##########JA - 22/07/2020 ########
                    if (line[2]['account_id']):
                        line_ids_new.append(line)

                for write_off_line in payment.writeoff_multi_acc_ids:
                    print ('WRITE OFF LINE--')
                    print (write_off_line.name)
                    print(write_off_line.amount)
                    print (write_off_line.wht_type)
                    print (write_off_line.writeoff_account_id.id)
                    if payment.currency_id == company_currency:
                        write_off_balance = 0.0
                        currency_id = False
                    else:
                        write_off_balance = payment.currency_id._convert(write_off_line.amount, company_currency,
                                                                         payment.company_id, payment.payment_date)
                        currency_id = payment.currency_id.id

                    if payment.partner_type == 'customer':
                        print ('---CUSTOMER--write-off')
                        line_ids_new.append((0, 0, {
                            'name': write_off_line.name,
                            'amount_currency': write_off_balance,
                            'currency_id': currency_id,
                            'debit': -write_off_line.amount < 0.0 and write_off_line.amount or 0.0,
                            'credit': -write_off_line.amount > 0.0 and -write_off_line.amount or 0.0,
                            'date_maturity': payment.payment_date,
                            'partner_id': payment.partner_id.commercial_partner_id.id,
                            'account_id': write_off_line.writeoff_account_id.id,
                            'payment_id': payment.id,
                            'wht_tax': write_off_line.deduct_item_id.id or False,
                            'wht_type': write_off_line.wht_type.id or False,
                            'amount_before_tax': write_off_line.amount_untaxed or 0.00,
                        }))
                    else:
                        line_ids_new.append((0, 0, {
                            'name': write_off_line.name,
                            'amount_currency': write_off_balance,
                            'currency_id': currency_id,
                            'debit': -write_off_line.amount > 0.0 and -write_off_line.amount or 0.0,
                            'credit': -write_off_line.amount < 0.0 and write_off_line.amount or 0.0,
                            'date_maturity': payment.payment_date,
                            'partner_id': payment.partner_id.commercial_partner_id.id,
                            'account_id': write_off_line.writeoff_account_id.id,
                            'payment_id': payment.id,
                            'wht_tax': write_off_line.deduct_item_id.id or False,
                            'wht_type': write_off_line.wht_type.id or False,
                            'amount_before_tax': write_off_line.amount_untaxed or 0.00,
                        }))
                print ('--LINS NEW--')
                print (line_ids_new)
                res[0]['line_ids'] = line_ids_new
            res[0]['narration'] = payment.remark
        return res


    ############# Add payment cancel condition to cheque - by JA 08/10/2020 ##############

    def cancel(self):
        print
        "NEW Cancel"
        for rec in self:
            ############ This is for multiple check in one payment
            if rec.cheque_reg_id:
                # print ('--CHECK FOR ONE PAYMENT')
                ############ JA - 03/07/2020 #############
                if rec.cheque_reg_id.state != 'confirm':
                    rec.cheque_reg_id.sudo().action_cancel()
                    rec.cheque_reg_id.sudo().unlink()
                else:
                    raise UserError(_('เช็คได้ผ่านแล้ว กรุณาตรวจสอบก่อนยกเลิก'))
                ############ JA - 03/07/2020 #############


            ########## record wht reference number before cancel ###########
            ######### 22/06/2020 ###########################################
            for move_line in rec.move_line_ids:
                if move_line.wht_reference:
                    write_off_line = rec.writeoff_multi_acc_ids.filtered(
                        lambda x: x.wht_personal_company == move_line.wht_personal_company and not float_compare(
                            x.amount, move_line.credit, 2))
                    # print write_off_line
                    if write_off_line:
                        write_off_line.wht_reference = move_line.wht_reference
            ######### 22/06/2020 ###########################################

            super(account_payment, self).cancel()


class writeoff_accounts(models.Model):
    _name = 'writeoff.accounts'
    _description = "Multi write off record"

    deduct_item_id = fields.Many2one('account.tax', string='Deduction Item')
    writeoff_account_id = fields.Many2one('account.account', string="Difference Account",
                                          domain=[('deprecated', '=', False)], copy=False, required="1")
    wht = fields.Boolean(string="WHT", related='writeoff_account_id.wht', default=False)
    # wht_tax = fields.Many2one('account.tax', string="WHT", default=False)
    wht_type = fields.Many2one('account.wht.type', string='WHT Type', )
    name = fields.Char('Description')
    amount_untaxed = fields.Float(string='Full Amount')
    amt_percent = fields.Float(string='Amount(%)', digits=(16, 2))
    amount = fields.Float(string='Payment Amount', digits=(16, 2), required=True)
    currency_id = fields.Many2one('res.currency', string='Currency', required=True,
                                  default=lambda self: self.env.user.company_id.currency_id)

    payment_id = fields.Many2one('account.payment', string='Payment Record')
    wht_reference = fields.Char(string='WHT Reference')

    # new for payment wizard only.
    payment_wizard_id = fields.Many2one('account.register.payment', string='Payment Record')
    # payment_billing_id = fields.Many2one('register.billing.payments', string='Payment Record')
    # department_id = fields.Many2one('hr.department', string='Department')

    @api.onchange('writeoff_account_id')
    # @api.multi
    def _onchange_writeoff_account_id(self):
        if self.writeoff_account_id:
            self.name = self.writeoff_account_id.name

    @api.onchange('amt_percent','amount_untaxed')
    def _onchange_amt_percent(self):
        if self.amount_untaxed and self.amt_percent:
            self.amount = self.amount_untaxed * self.amt_percent / 100

    @api.onchange('deduct_item_id')
    # @api.multi
    def _onchange_deduct_item_id(self):
        if self.payment_wizard_id:
            self.amount_untaxed = self.payment_wizard_id.amount_untaxed
        #
        #     # new for payment billing only
        # if self.payment_billing_id:
        #     payment_vals = self.payment_billing_id.get_payment_vals()
        #     self.amount_untaxed = payment_vals['amount_untaxed']


        if self.deduct_item_id:
            tax_account_line_id = self.deduct_item_id.invoice_repartition_line_ids.filtered(lambda x: x.repartition_type == 'tax')
            if tax_account_line_id:
                account_id = tax_account_line_id.account_id.id
            else:
                account_id = False
            self.writeoff_account_id = account_id
            self.amt_percent = self.deduct_item_id.amount
            self.name = self.deduct_item_id.name
            self.wht_type = self.deduct_item_id.wht_type
            self.amount = self.amount_untaxed * self.deduct_item_id.amount / 100


