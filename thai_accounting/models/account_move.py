# -*- coding: utf-8 -*-
# Copyright (C) 2016-Today  itaas.co.th

from odoo import api, fields, models, _
from odoo.exceptions import UserError
import math
from datetime import datetime, date


class account_move(models.Model):
    _inherit = "account.move"


    ####### Additional field for Invoice - JA - 20/07/2020 ############
    tax_inv_generated = fields.Boolean(string='Tax Invoice Generated',copy=False)
    tax_invoice_date = fields.Date(string='Tax Invoice Date',copy=False)
    tax_inv_number = fields.Char(string='Tax Invoice Number',copy=False)
    adjust_move_id = fields.Many2one('account.move', string="Tax Journal Entry", copy=False)
    ####### Additional field for Invoice - JA - 20/07/2020 ############

    # Temporary remove by JA - 20/07/020 #################################
    # wht_reference = fields.Char(string="WHT Reference",default=False)
    # wht_generated = fields.Boolean(string='WHT Generated',default=False)
    invoice_date = fields.Date(string="Invoice/Bill Date", readonly=True, states={'draft': [('readonly', False)]})
    # remark = fields.Char(string="Payment Remark")
    # wht_personal_company = fields.Selection([('personal', 'ภงด3'), ('company', 'ภงด53'),('50-1', 'ภงด1')],string="WHT Type")
    is_closing_month = fields.Boolean(string='Closing Month')
    # Temporary remove by JA - 20/07/020 #################################


    ######################To Manage cheque payment both account.move and account.payment #####
    # this is new bank list from res.bank
    cheque_bank = fields.Many2one('res.bank', string="Bank")
    cheque_branch = fields.Char(string="Branch")
    cheque_number = fields.Char(string="Cheque Number")
    cheque_date = fields.Date(string="Cheque Date")
    ######################To Manage cheque payment both account.move and account.payment #####

    ########additional field#########
    # department_id = fields.Many2one('hr.department', string="แผนก")
    supplier_name_text = fields.Char('Partner Name (Manual)')
    supplier_address_text = fields.Char('Partner Address')
    supplier_branch_text = fields.Integer('Partner Branch (Manual)')
    supplier_taxid_text = fields.Char('Tax ID (Manual)')
    is_manual_partner = fields.Boolean(string='Partner Manual')



    def action_invoice_generate_tax_invoice(self):
        if self.type in ('out_invoice','out_refund'):
            if not self.tax_inv_number and self.journal_id.tax_invoice_sequence_id:
                if not self.tax_invoice_date:
                    self.tax_invoice_date = fields.Date.today()
                self.tax_inv_number = self.journal_id.tax_invoice_sequence_id.next_by_id(sequence_date=self.tax_invoice_date)
                self.tax_inv_generated = True
                self.create_reverse_tax()
        else:
            ######### This is purchase side########
            self.create_reverse_tax()


    def create_reverse_tax(self):
        line_ids = []
        for line in self.line_ids.filtered('tax_repartition_line_id'):
            if self.type in ('out_invoice', 'out_refund'):
                if not line.account_id.sale_tax_report:
                    tax_account_id = self.env['account.account'].search([('sale_tax_report','=',True)],limit=1)
                    if not self.journal_id.adj_journal:
                        raise UserError(_("Please setup journal to reverse tax on invoice journal"))
                else:
                    continue
            else:
                if not line.account_id.purchase_tax_report:
                    tax_account_id = self.env['account.account'].search([('purchase_tax_report', '=', True)], limit=1)
                    if not self.journal_id.adj_journal:
                        raise UserError(_("Please setup journal to reverse tax on invoice journal"))
                else:
                    continue

            original_tax_line = {
                'name': line.name,
                'amount_currency': line.amount_currency if line.currency_id else 0.0,
                'currency_id': line.currency_id.id or False,
                'debit': line.credit,
                'credit': line.debit,
                'date_maturity': self.tax_invoice_date,
                'partner_id': line.partner_id.id,
                'account_id': line.account_id.id,
                'payment_id': False,
                'tax_base_amount': line.tax_base_amount,
            }
            new_tax_line = {
                'name': tax_account_id.name,
                'amount_currency': line.amount_currency if line.currency_id else 0.0,
                'currency_id': line.currency_id.id or False,
                'debit': line.debit,
                'credit': line.credit,
                'date_maturity': self.tax_invoice_date,
                'partner_id': line.partner_id.id,
                'account_id': tax_account_id.id,
                'payment_id': False,
                'tax_base_amount': line.tax_base_amount,
            }
            line_ids.append((0, 0, original_tax_line))
            line_ids.append((0, 0, new_tax_line))

        if line_ids:
            print ('LINE')
            print (line_ids)
            move_vals = {
                'type': 'entry',
                'date': self.tax_invoice_date or date.today(),
                'ref': self.name,
                'journal_id': self.journal_id.adj_journal.id,
                'currency_id': self.currency_id.id or self.journal_id.currency_id.id or self.company_id.currency_id.id,
                'partner_id': self.partner_id.id,
                'line_ids': line_ids
            }

            move_id = self.env['account.move'].create(move_vals)
            move_id.post()
            self.adjust_move_id = move_id

    # Temporary remove by JA - 20/07/020 #################################
    # @api.multi
    # def get_invoice(self):
    #     invoice_id = self.env['account.invoice'].search([('move_id','=',self.id)])
    # print invoice_id.number
    # return invoice_id

    # @api.multi
    # def action_gen_wht(self):
    # in case need to refer specificate date, similar syntax can be applied - with_context(ir_sequence_date=move.date)
    # if self.wht_personal_company == 'personal':
    #     self.wht_reference = self.env['ir.sequence'].with_context(ir_sequence_date=self.date).next_by_code('wht3.no') or '/'
    #     self.wht_generated = True
    # elif self.wht_personal_company == 'company':
    #     self.wht_reference = self.env['ir.sequence'].with_context(ir_sequence_date=self.date).next_by_code(
    #         'wht53.no') or '/'
    #     self.wht_generated = True

    # @api.multi
    # def post(self, invoice=False):
    #     if self.company_id.country_id.name == 'Thailand':
    #         self._post_validate()
    #         for move in self:
    #             move.line_ids.create_analytic_lines()
    #             if move.name == '/':
    #                 new_name = False
    #                 journal = move.journal_id
    #
    #                 if invoice and invoice.move_name and invoice.move_name != '/':
    #                     new_name = invoice.move_name
    #                 else:
    #                     if journal.sequence_id:
    #                         If invoice is actually refund and journal has a refund_sequence then use that one or use the regular one
    # sequence = journal.sequence_id
    # if invoice and invoice.type in ['out_refund', 'in_refund'] and journal.refund_sequence:
    #     if not journal.refund_sequence_id:
    #         raise UserError(_('Please define a sequence for the credit notes'))
    #     sequence = journal.refund_sequence_id
    #
    # new_name = sequence.with_context(ir_sequence_date=move.date).next_by_id()
    # else:
    #     raise UserError(_('Please define a sequence on the journal.'))
    #
    # if new_name:
    #     move.name = new_name
    #
    #########add this line to generate witholding tax
    # for line in move.line_ids:
    #     if line.wht_type:
    #         move.action_gen_wht()
    #         break

    ####### end gen wht ###########

    # if move == move.company_id.account_opening_move_id and not move.company_id.account_bank_reconciliation_start:
    # For opening moves, we set the reconciliation date threshold
    # to the move's date if it wasn't already set (we don't want
    # to have to reconcile all the older payments -made before
    # installing Accounting- with bank statements)
    # move.company_id.account_bank_reconciliation_start = move.date

    # return self.write({'state': 'posted'})

    # else:
    #     return super(account_move,self).post(invoice)

    def roundup(self,x):
        return int(math.ceil(x / 10.0)) * 6


class account_wht_type(models.Model):
    _name = 'account.wht.type'
    _description = "Account WHT Type"

    name = fields.Char(string='WHT Type')

class AccountMoveLine(models.Model):
    _inherit = "account.move.line"
    _order = 'is_debit desc, date desc, id desc'

    # wht_type = fields.Selection([('1%','1%'),('2%','2%'),('3%','3%'),('5%','5%')],string="WHT",default=False)
    wht_tax = fields.Many2one('account.tax', string="WHT", default=False)
    wht_type = fields.Many2one('account.wht.type',string='WHT Type',)
    wht_reference = fields.Char(string="WHT Reference")

    invoice_date = fields.Date(string='Invoice/Bill Date',related='move_id.invoice_date',store=True)
    # department_id = fields.Many2one('hr.department', string="Department")
    # ref = fields.Char(related='move_id.ref', string='Reference', store=True, copy=False, index=True)
    # sale_tax_report = fields.Boolean(string='รายงานภาษีขาย', related='account_id.sale_tax_report')
    # purchase_tax_report = fields.Boolean(string='รายงานภาษีซื้อ', related='account_id.purchase_tax_report')
    amount_before_tax = fields.Float(string='Amt Before Tax')
    is_closing_month = fields.Boolean(string='Closing Month', related='move_id.is_closing_month', store=True)
    is_debit = fields.Boolean(string='Is Debit', compute='get_is_debit_credit', store=True)
    # wht_payment_type = fields.Selection([('1','1'),('2','2')],string='WHT Payment Type',default='1')

    @api.depends('debit', 'credit')
    def get_is_debit_credit(self):
        for line in self:
            if line.debit:
                line.is_debit = True
            else:
                line.is_debit = False

    # @api.model_create_multi
    # def create(self, vals_list):
    # print ('1111')
    # if self.company_id.country_id.name == 'Thailand':
    #     print(vals_list)
    #     for vals in vals_list:
    #         MoveObj = self.env['account.move']
    #         if vals.get('move_id', False):
    #             move = MoveObj.browse(vals_list['move_id'])
    #             if not vals.get('ref', False):
    #                 vals['ref'] = move.ref
    #             if not vals.get('partner_id', False):
    #                 vals['partner_id'] = move.partner_id.id
    #
    # return super(AccountMoveLine, self).create(vals_list)

    def roundup(self,x):
        return int(math.ceil(x / 10.0)) * 10

    def roundupto(self,x):
        # print x
        # print int(math.ceil(x / 7.0)) * 7
        return int(math.ceil(x / 7.0)) * 7





    
