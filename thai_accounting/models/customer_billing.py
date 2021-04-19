# -*- coding: utf-8 -*-
# Copyright (C) 2016-Today (ITAAS)

from odoo import api, fields, models, _
from odoo.tools import float_is_zero, float_compare
from odoo.tools.misc import formatLang
import json
from odoo.exceptions import UserError
from odoo.tools import email_re, email_split, email_escape_char, float_is_zero, float_compare, \
    pycompat, date_utils

# mapping invoice type to journal type
TYPE2JOURNAL = {
    'out_invoice': 'sale',
    'in_invoice': 'purchase',
    'out_refund': 'sale',
    'in_refund': 'purchase',
}



class AccountMove(models.Model):
    _inherit = 'account.move'

    billing_number = fields.Char(string="Billing",default='',copy=False)
    billing_id = fields.Many2one('customer.billing',string="Billing Number",copy=False)

class CustomerBilling(models.Model):
    _name = 'customer.billing'
    _inherit = ['mail.thread']
    _description = "Customer Billing"

    @api.model
    def _default_journal(self):
        if self._context.get('default_journal_id', False):
            return self.env['account.journal'].browse(self._context.get('default_journal_id'))
        inv_type = self._context.get('type', 'out_invoice')
        inv_types = inv_type if isinstance(inv_type, list) else [inv_type]
        company_id = self._context.get('company_id', self.env.user.company_id.id)
        domain = [
            ('type', 'in', [TYPE2JOURNAL[ty] for ty in inv_types if ty in TYPE2JOURNAL]),
            ('company_id', '=', company_id),
        ]
        return self.env['account.journal'].search(domain, limit=1)
    
    @api.model
    def _default_currency(self):
        journal = self._default_journal()
        return journal.currency_id or journal.company_id.currency_id
    
    # @api.one
    @api.depends('invoice_ids')
    def _compute_amount(self):
        amount_untaxed = 0
        amount_tax = 0
        for inv in self.invoice_ids:
            if inv.invoice_payment_state == 'not_paid':
                if inv.type in ('out_invoice','in_invoice'):
                    amount_untaxed += inv.amount_untaxed
                    amount_tax += inv.amount_tax
                else:
                    amount_untaxed -= inv.amount_untaxed
                    amount_tax -= inv.amount_tax

        self.amount_untaxed = amount_untaxed
        self.amount_tax = amount_tax
        self.amount_total = amount_untaxed + amount_tax

        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }
        
    # @api.one
    @api.depends('invoice_ids','invoice_ids.amount_residual_signed',)
    def _compute_residual(self):
        for billing in self:
            billing.residual = sum(inv.amount_residual_signed for inv in billing.invoice_ids)
            if billing.invoice_ids and not billing.residual:
                billing.state = 'paid'
            
    name = fields.Char(string='Reference', index=True,
        readonly=True, states={'draft': [('readonly', False)]}, copy=False, default='New')

    # To prepare receipt document from billing
    # rec_pre_no = fields.Char(string='Receipt Pre Number.', readonly=True, copy=False)
    # rec_pre_date = fields.Date(string='Receive Pre Date', help='Receive Pre Number generated date.', readonly=True,
    #                            copy=False)
    # rec_pre_generated = fields.Boolean(string='Receive Pre Number Generated', default=False, copy=False)
    date_billing = fields.Date(string='Billing Date',
        readonly=True, states={'draft': [('readonly', False)]}, index=True,
        default=lambda self: self._context.get('date', fields.Date.context_today(self)), copy=False)
    desc = fields.Char('Description', readonly=True, states={'draft': [('readonly', False)]})
    partner_id = fields.Many2one('res.partner', string='Customer', change_default=True,
        required=True, readonly=True, states={'draft': [('readonly', False)]},
        track_visibility='always')
    comment = fields.Text('Additional Information', readonly=True, states={'draft': [('readonly', False)]})
    state = fields.Selection([
            ('draft','Draft'),
            ('validate', 'Validated'),
            ('confirm', 'Confirmed'),
            ('paid', 'Paid'),
            ('cancel', 'Cancelled'),
        ], string='Status', index=True, default='draft', track_visibility='onchange', copy=False,
        help=" * The 'Draft' status is used when a user is encoding a new and unconfirmed Customer billing.\n"
             " * The 'Confirmed' status is used when user create customer billing, a billing number is generated. Its in confirm status till user does not pay the bill amount.\n"
             " * The 'Paid' status is set automatically when the invoices is paid. Its related journal entries may or may not be reconciled.\n"
             " * The 'Cancelled' status is used when user cancel billing.")
    invoice_ids = fields.Many2many('account.move', 'billing_invoice_rel', string='Invoices',
        readonly=True, states={'draft': [('readonly', False)]}, copy=True)


    user_id = fields.Many2one('res.users', string='Salesperson', track_visibility='onchange',
        readonly=True, states={'draft': [('readonly', False)]},
        default=lambda self: self.env.user)
    type = fields.Selection([
            ('out_invoice','Customer Invoice'),
            ('out_refund','Customer Refund'),
            ('in_invoice', 'Supplier Invoice'),
            ('in_refund', 'Supplier Refund'),
        ], readonly=False, index=True, change_default=True, default='out_invoice', track_visibility='always')
    customer_supplier = fields.Selection([
        ('customer','customer'),
        ('supplier','supplier'),
    ],string="customer or supplier")
    currency_id = fields.Many2one('res.currency', string='Currency',
        required=True, readonly=True, states={'draft': [('readonly', False)]},
        default=_default_currency, track_visibility='always')
    company_id = fields.Many2one('res.company', string='Company', change_default=True,
        required=True, readonly=True, states={'draft': [('readonly', False)]},
        default=lambda self: self.env['res.company']._company_default_get('account.invoice'))
    company_currency_id = fields.Many2one('res.currency', related='company_id.currency_id', readonly=True)
    amount_untaxed = fields.Monetary(string='Untaxed Amount', currency_field='currency_id',
        store=True, readonly=True, compute='_compute_amount', track_visibility='always')
    amount_tax = fields.Monetary(string='Tax', currency_field='currency_id',
        store=True, readonly=True, compute='_compute_amount')
    amount_total = fields.Monetary(string='Total', currency_field='currency_id',
        store=True, readonly=True, compute='_compute_amount')


    residual = fields.Monetary(string='Amount Due', currency_field='currency_id',
        compute='_compute_residual', store=False, help="Remaining amount due.")

    # payments_widget = fields.Text(compute='_get_payment_info_JSON')
    payments_widget = fields.Text(string='Payment Widget')
    # payment_move_line_ids = fields.Many2many('account.move.line', string='Payments', compute='_compute_payments',
    #                                          store=True)
    payment_move_line_ids = fields.Many2many('account.move.line', string='Payments')

    auto_load = fields.Boolean(string="Auto Load Due Invoice", default=False)

    date_receipt = fields.Date(string='Receipt Date',default=fields.Date.today())



    # @api.one
    # @api.depends('state')
    # def _compute_payments(self):
    #     # print "come here"
    #     payment_lines = []
    #     if self.invoice_ids:
    #         for line in self.invoice_ids[0].line_ids:
    #             payment_lines.extend(filter(None, [rp.credit_move_id.id for rp in line.matched_credit_ids]))
    #             payment_lines.extend(filter(None, [rp.debit_move_id.id for rp in line.matched_debit_ids]))
    #         self.payment_move_line_ids = self.env['account.move.line'].browse(list(set(payment_lines)))

    # @api.one
    # @api.depends('payment_move_line_ids.amount_residual')
    # def _get_payment_info_JSON(self):
    #     # print "get json info"
    #     amount = 0.0
    #     amount_currency = 0.0
    #     self.payments_widget = json.dumps(False)
    #     if self.payment_move_line_ids:
    #         info = {'title': _('Less Payment'), 'outstanding': False, 'content': []}
    #         currency_id = self.currency_id
    #         for payment in self.payment_move_line_ids:
    #             payment_currency_id = False
    #             if self.type in ('out_invoice', 'in_refund'):
    #                 if self.invoice_ids:
    #                     for invoice in self.invoice_ids:
    #                         amount += sum(
    #                             [p.amount for p in payment.matched_debit_ids if p.debit_move_id in invoice.move_id.line_ids])
    #                         amount_currency += sum([p.amount_currency for p in payment.matched_debit_ids if
    #                                                p.debit_move_id in invoice.move_id.line_ids])
    #                         if payment.matched_debit_ids:
    #                             payment_currency_id = all([p.currency_id == payment.matched_debit_ids[0].currency_id for p in
    #                                                        payment.matched_debit_ids]) and payment.matched_debit_ids[
    #                                                       0].currency_id or False
    #             elif self.type in ('in_invoice', 'out_refund'):
    #                 if self.invoice_ids:
    #                     for invoice in self.invoice_ids:
    #                         amount += sum(
    #                             [p.amount for p in payment.matched_credit_ids if p.credit_move_id in invoice.move_id.line_ids])
    #                         amount_currency += sum([p.amount_currency for p in payment.matched_credit_ids if
    #                                                p.credit_move_id in invoice.move_id.line_ids])
    #                         if payment.matched_credit_ids:
    #                             payment_currency_id = all([p.currency_id == payment.matched_credit_ids[0].currency_id for p in
    #                                                        payment.matched_credit_ids]) and payment.matched_credit_ids[
    #                                                       0].currency_id or False
    #             # get the payment value in invoice currency
    #             if payment_currency_id and payment_currency_id == self.currency_id:
    #                 amount_to_show = amount_currency
    #             else:
    #                 amount_to_show = payment.company_id.currency_id.with_context(date=payment.date).compute(amount,
    #                                                                                                         self.currency_id)
    #             if float_is_zero(amount_to_show, precision_rounding=self.currency_id.rounding):
    #                 continue
    #             payment_ref = payment.move_id.name
    #             if payment.move_id.ref:
    #                 payment_ref += ' (' + payment.move_id.ref + ')'
    #
    #             info['content'].append({
    #                 'name': payment.name,
    #                 'journal_name': payment.journal_id.name,
    #                 'amount': amount_to_show,
    #                 'currency': currency_id.symbol,
    #                 'digits': [69, currency_id.decimal_places],
    #                 'position': currency_id.position,
    #                 'date': payment.date,
    #                 'payment_id': payment.id,
    #                 'move_id': payment.move_id.id,
    #                 'ref': payment_ref,
    #             })
    #             # info = {'title': _('Less Payment'), 'outstanding': False, 'content': self._get_payments_vals()}
    #             # self.payments_widget = json.dumps(info, default=date_utils.json_default)
    #
    #         self.payments_widget = json.dumps(info,default=date_utils.json_default)

    @api.onchange('partner_id')
    @api.depends('partner_id')
    def onchange_partner_id(self):
        print ('------onchange_partner_id----')

        if self.type == 'out_invoice':
            if self.auto_load:
                inv_ids = self.env['account.move'].search([('state','=','posted'),('invoice_payment_state','=','not_paid'),('billing_id','=',False),('type','in',('out_invoice','out_refund')),
                                                          ('partner_id','=',self.partner_id.id),('invoice_date_due','<=',self.date_billing),('company_id','=',self.company_id.id)])
                inv_ids = [inv.id for inv in inv_ids]
                self.invoice_ids = [(6, 0, inv_ids)]
            self.customer_supplier = 'customer'

        elif self.type == 'in_invoice':
            # print "y"
            if self.auto_load:
                inv_ids = self.env['account.move'].search(
                    [('state', '=', 'open'), ('type', '=', 'in_invoice'), ('billing_id', '=', False),
                     ('partner_id', '=', self.partner_id.id), ('date_due','<=',self.date_billing),('company_id', '=', self.company_id.id)])
                inv_ids = [inv.id for inv in inv_ids]
                self.invoice_ids = [(6, 0, inv_ids)]
            self.customer_supplier = 'supplier'


        
    @api.model
    def create(self, vals):
        if not vals.get('name'):
            if vals.get('type') == 'out_invoice':
                vals['name'] = self.env['ir.sequence'].next_by_code('customer.billing')
            elif vals.get('type') == 'in_invoice':
                vals['name'] = self.env['ir.sequence'].next_by_code('supplier.billing')

        return super(CustomerBilling, self).create(vals)

    # @api.multi
    def validate_billing(self):
        for inv_id in self.invoice_ids:
            # if inv_id.billing_id != False:
            #     raise UserError(_("Invoice %s ถูกสร้างใน Billing %s") % (inv_id.number, inv_id.billing_id.name))
            # else:
            inv_id.write({'billing_id': self.id})
        self.write({'state': 'validate'})

    # @api.multi
    def confirm_billing(self):
        self.write({'state': 'confirm'})
    
    # @api.multi
    def action_cancel(self):
        for inv_id in self.invoice_ids:
            inv_id.write({'billing_id': False})
        self.write({'state': 'cancel'})
        
    # @api.multi
    def action_cancel_draft(self):
        for inv_id in self.invoice_ids:
            inv_id.write({'billing_id': False})
        self.write({'state': 'draft'})
        
    # @api.multi
    def action_print(self):
        self.ensure_one()
        return self.env.ref('thai_accounting.report_billing').report_action(self)
        # return self.env['report'].get_action(self, 'thai_accounting.report_billing')

    # @api.multi
    def action_generate_rec_pre(self):
        rec_pre_no = self.env['ir.sequence'].next_by_code('rec.pre.no') or 'New'
        self.write({'rec_pre_no': rec_pre_no,
                    'rec_pre_date': fields.Date.context_today(self),
                    'rec_pre_generated': True})

    # @api.multi
    def unlink(self):
        if self.state not in ('draft','cancel'):
            raise UserError(_("You can delete only billing in draft and cancel state"))
        return super(CustomerBilling, self).unlink()


