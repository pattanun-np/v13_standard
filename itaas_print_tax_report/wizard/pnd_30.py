# -*- coding: utf-8 -*-
# Copyright (C) 2016-2017  Technaureus Info Solutions(<http://technaureus.com/>).

from odoo import models, fields, api, _
from datetime import datetime
#from StringIO import StringIO
from io import BytesIO
import base64
from odoo.exceptions import UserError
from odoo.tools import misc
import xlwt
from decimal import *
from dateutil.relativedelta import relativedelta
import calendar
from io import StringIO


class account_move(models.Model):
    _inherit = 'account.move'


    def company_data(self):
        print('vvvvvv')

    def purchase_data(self):
        # print(self.date_from)
        data_purchase = {}
        amount = 0
        purchase_tax = self.env['account.move.line'].search(
            [('account_id.purchase_tax_report', '=', True), ('move_id.state', '!=', 'draft')])
        # print(purchase_tax.tax_base_amount)
        # purchase_tax_last = purchase_tax[len(purchase_tax) - 1]
        if purchase_tax.mapped('debit'):
            amount = sum(purchase_tax.mapped('debit')) * (-1)
        else:
            amount = sum(purchase_tax.mapped('credit'))
        amount_before_tax = sum(purchase_tax.mapped('amount_before_tax'))
        data_purchase = {
            'amount': abs(amount),
            'amount_before_tax': amount_before_tax,
            # 'purchase_tax_last': purchase_tax_last,
        }
        return data_purchase

    def sale_data(self):
        data_sale = {}
        amount = 0
        sale_tax = self.env['account.move.line'].search(
            [('account_id.sale_tax_report', '=', True), ('move_id.state', '!=', 'draft')])
        if sale_tax.mapped('debit'):
            amount = sum(sale_tax.mapped('debit')) * (-1)
        else:
            amount = sum(sale_tax.mapped('credit'))
        amount_before_tax = sum(sale_tax.mapped('amount_before_tax'))
        data_sale = {
            'amount': abs(amount),
            'amount_before_tax': amount_before_tax,
        }
        return data_sale



class pnd30_report_tax(models.TransientModel):
    _name = 'pnd30.report.tax'

    date_from = fields.Date(string='Date From',required=True)
    date_to = fields.Date(string='Date To',required=True)
    fax_for = fields.Boolean(string='ยื่นปรกติ')
    fax_1 = fields.Boolean(string='แยกยื่น')
    fax_2 = fields.Boolean(string='ยื่นรวม')
    previous_balance = fields.Float(string='ภาษีที่ชำระเกินยกมา')



    # @api.model
    # def _get_report_values(self, docids, data=None):
    #     model = self.env.context.get('active_model')
    #     docs = self.env[model].browse(self.env.context.get('active_id'))
    #     print(docids)
    #     print('=vvv=v=v=v==v')
    #     doc_model = 'account.move'
    #     domain = []
    #     if data:
    #         print('vvvv')
    #
    #     docargs = {
    #         'doc_ids': docids,
    #         'doc_model': doc_model,
    #         'data': data,
    #         'docs': docs,
    #     }
    #     return docargs

    def print_pnd30_report(self):
        data = {'date_from': self.date_from, 'date_to': self.date_to}
        print('================')
        print(data)
        print('================')

        if data['date_from'] and data['date_to'] :
            return self.env.ref('itaas_print_tax_report.action_tax_30_report_id').report_action(self, data=data)

class report_report_pnd30_id(models.AbstractModel):
    _name = 'report.itaas_print_tax_report.report_pnd30_id'

    def sale_data(self,date_form,date_to):
        data_sale = {}
        amount = 0

        # company_id = self.env.user.company_id
        company_id = self.env.company
        operating_unit_id = False
        docs = False
        move_ids = {}
        doc = []
        domain = [('invoice_date', '>=', date_form), ('invoice_date', '<=', date_to),
                  ('state', 'in', ('posted', 'cancel')), ('type', 'in', ('out_invoice', 'out_refund'))]
        docs = self.env['account.move'].search(domain)
        # print('Domain:', domain)
        # print('docs:', docs)
        date = datetime.today()
        amount_untaxed = 0
        amount_tax = 0
        amount_total = 0
        sum_untaxed = 0
        amount_total_tax = amount_total_untaxed = amount_untaxed_no_vat = 0
        for move_id in docs:
            print('move_id:',move_id)
            line_vat = move_id.invoice_line_ids.filtered(lambda x: x.tax_ids)
            if line_vat:
                if move_id.journal_id.type_vat == 'tax':
                    date = move_id.invoice_date
                elif move_id.journal_id.type_vat == 'not_deal':
                    date = move_id.tax_invoice_date

                if move_id.currency_id.name == 'THB':
                    # print('aaaaa')

                    amount_untaxed = move_id.amount_untaxed
                    amount_tax = move_id.amount_tax
                    # amount_total = move_id.amount_total

                else:
                    rate = 0
                    if move_id.currency_id.rate_ids:
                        rate = move_id.currency_id.rate_ids[0].rate
                    amount_untaxed = move_id.amount_untaxed / rate
                    amount_tax = move_id.amount_tax / rate
                    # amount_total = move_id.amount_total / rate

                    # print('asasas')

                if move_id.state != 'cancel':
                    if move_id.type == 'out_refund':
                        amount_total_tax += amount_tax *(-1)
                        amount_total_untaxed += amount_untaxed*(-1)

                        if move_id.amount_untaxed and not move_id.amount_tax:
                            amount_untaxed_no_vat += amount_untaxed*(-1)


                    else:
                        amount_total_tax += amount_tax
                        amount_total_untaxed += amount_untaxed

                        if move_id.amount_untaxed and not move_id.amount_tax:
                            amount_untaxed_no_vat += amount_untaxed



        data_sale = {
            'amount_untaxed_no_vat':  amount_untaxed_no_vat,
            'amount': abs(amount_total_tax),
            'amount_before_tax': amount_total_untaxed,
        }
        return data_sale


    def purchase_data(self,date_form,date_to):
        print('purchase_date')
        data_purchase = {}
        amount = 0
        amount_total_tax = amount_total_untaxed = 0
        domain = [('account_id.purchase_tax_report', '=', True), ('date', '>=', date_form),
                  ('date', '<=', date_to),
                  ('move_id.state', '=', 'posted'), ('date_maturity', '=', False),
                  ('move_id.type', 'in', ('in_invoice', 'in_refund', 'entry'))
            , ('exclude_from_invoice_tab', '=', True)]
        # print('domain:', domain)
        docs = self.env['account.move.line'].search(domain)
        # print('docs_purchase:', docs)
        for move_line_id in docs:
            if move_line_id.date_vat_new:
                date = move_line_id.date_vat_new
            else:
                date = move_line_id.tax_inv_date
            if move_line_id.ref_new:
                ref = move_line_id.ref_new
            else:
                ref = move_line_id.ref

            if move_line_id.debit:
                amount_total_tax += move_line_id.debit
                amount_total_untaxed += move_line_id.tax_base_amount
            else:
                amount_total_untaxed -= move_line_id.tax_base_amount
                amount_total_tax -= move_line_id.credit

        domain = [('account_id.purchase_tax_report', '=', True), ('date_maturity', '>=', date_form),
                      ('date_maturity', '<=', date_to), ('move_id.state', '=', 'posted'),
                      ('date_maturity', '!=', False), ('exclude_from_invoice_tab', '=', True)]

        docs = self.env['account.move.line'].search(domain)
        for move_line_id in docs:
            print('move_line_id:',move_line_id)

            if move_line_id.date_vat_new:
                date = move_line_id.date_vat_new
            else:
                date = move_line_id.tax_inv_date
            if move_line_id.ref_new:
                ref = move_line_id.ref_new
            else:
                ref = move_line_id.ref

            if move_line_id.debit:
                amount_total_tax += move_line_id.debit
                amount_total_untaxed += move_line_id.tax_base_amount
            else:
                amount_total_untaxed -= move_line_id.tax_base_amount
                amount_total_tax -= move_line_id.credit

        domain = [('account_id.purchase_tax_report', '=', True), ('date', '>=', date_form),
                  ('date', '<=',date_to),
                  ('move_id.state', '=', 'posted'), ('date_maturity', '=', False),
                  ('move_id.type', 'in', ('in_invoice', 'in_refund', 'entry'))
            , ('exclude_from_invoice_tab', '=', False), ('is_special_tax', '=', True)]
        docs = self.env['account.move.line'].search(domain)

        for move_line_id in docs:
            if move_line_id.date_vat_new:
                date = move_line_id.date_vat_new
            else:
                date = move_line_id.tax_inv_date
            if move_line_id.ref_new:
                ref = move_line_id.ref_new
            else:
                ref = move_line_id.ref

            if move_line_id.debit:
                amount_total_tax += move_line_id.debit
                if move_line_id.tax_base_amount:
                    amount_total_untaxed += move_line_id.tax_base_amount
                else:
                    amount_total_untaxed += move_line_id.amount_before_tax
            else:
                amount_total_tax -= move_line_id.credit
                if move_line_id.tax_base_amount:
                    amount_total_untaxed -= move_line_id.tax_base_amount
                else:
                    amount_total_untaxed -= move_line_id.amount_before_tax





        data_purchase = {
            'amount': abs(amount_total_tax),
            'amount_before_tax': amount_total_untaxed,
        }
        print('=========+END============')

        return data_purchase


    @api.model
    def _get_report_values(self, docids, data=None):
        print('GET_REPORT_VALUESE')
        # company_id = self.env.user.company_id
        company_id = self.env.company
        print(company_id.name)
        print(company_id.zip)
        date_to = data['date_to']
        purchase = self.purchase_data(data['date_from'],data['date_to'])
        sale = self.sale_data(data['date_from'],data['date_to'])

        model = self.env.context.get('active_model')
        docs = self.env[model].browse(self.env.context.get('active_id'))
        print('purchase:',purchase)
        print('sale:',sale)
        return {
            'doc_ids': docids,
            'doc_model': 'account.move',
            'docs': docs,
            'company_id': company_id,
            'purchase': purchase,
            'sale': sale,
            'data': data,
            'date_to':date_to,
        }





