# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from datetime import datetime,timedelta,date

from odoo import api, fields, models ,_
from odoo.exceptions import UserError
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT



class report_sale_tax_report(models.AbstractModel):
    _name = 'report.itaas_print_tax_report.sale_tax_report_id'

    def get_amount_multi_currency(self,move_id):
        total_amount = 0.0
        tax_amount = 0.0
        for line in move_id.line_ids:
            total_amount += abs(line.debit)
            if line.account_id.sale_tax_report:
                tax_amount += abs(line.balance)
        return total_amount, tax_amount

    @api.model
    def _get_report_values(self, docids, data=None):
        print ('------_get_report_values ----> sales---')
        company_id = self.env.company
        operating_unit_id = False
        docs = False
        move_ids = {}
        doc = []
        domain = [('invoice_date','>=',data['date_from']),('invoice_date','<=',data['date_to']),
                  ('state','in',('posted','cancel')),('type','in',('out_invoice','out_refund'))]
        docs = self.env['account.move'].search(domain)
        print('Domain:',domain)
        print ('docs:',docs)
        date = datetime.today()
        amount_untaxed = 0
        amount_tax = 0
        amount_total = 0
        sum_untaxed = 0
        for move_id in docs:
            line_vat = move_id.invoice_line_ids.filtered(lambda x: x.tax_ids)
            if line_vat:
                if move_id.journal_id.type_vat == 'tax':
                    date = move_id.invoice_date
                elif move_id.journal_id.type_vat == 'not_deal':
                    date = move_id.tax_invoice_date

                if move_id.currency_id.name == 'THB':
                    print('aaaaa')
                    amount_untaxed = move_id.amount_untaxed
                    amount_tax = move_id.amount_tax
                    amount_total = move_id.amount_total
                else:
                    rate = 0
                    if move_id.currency_id.rate_ids:
                        rate = move_id.currency_id.rate_ids[0].rate
                    amount_untaxed = move_id.amount_untaxed / rate
                    amount_tax = move_id.amount_tax / rate
                    amount_total = move_id.amount_total / rate


                    print('asasas')

                move_ids={
                    'date': date.strftime("%d/%m/%Y"),
                    'name': move_id.name,
                    'partner': move_id.partner_id,
                    'vat': move_id.partner_id.vat,
                    'branch': move_id.partner_id.branch_no,
                    'amount_untaxed':amount_untaxed,
                    'amount_tax': amount_tax,
                    'amount_total': amount_total,
                    'move_id': move_id,
                    'state': move_id.state,
                    'type': move_id.type
                }
                doc.append(move_ids)
                print('doc:', doc)
        doc.sort(key=lambda k: (k['date'] , k['name']))
        print('move_ids:',doc)
        print('doc:',doc)
        return {
            'doc_ids': docids,
            'doc_model': 'account.move',
            'docs': doc,
            'company_id': company_id,
            'data': data,
        }


#start This is to generate purchase tax report
class report_purchase_tax_report(models.AbstractModel):
    _name = 'report.itaas_print_tax_report.purchase_tax_report_id'

    @api.model
    def _get_report_values(self, docids, data=None):
        company_id = self.env.company
        move_line_ids = {}
        doc = []
        ######################### CASE #1 #################
        domain = [('account_id.purchase_tax_report','=',True),('date','>=',data['date_from']),('date','<=',data['date_to']),
                  ('move_id.state','=','posted'),('date_maturity','=',False),('move_id.type','in',('in_invoice','in_refund','entry'))
            ,('exclude_from_invoice_tab','=',True)]
        print('domain:',domain)
        docs = self.env['account.move.line'].search(domain)
        print('docs_purchase:',docs)
        for move_line_id in docs:
            if move_line_id.date_vat_new:
                date = move_line_id.date_vat_new
            else:
                date = move_line_id.tax_inv_date

            if not date:
                raise UserError(_("Please check date for item %s" % move_line_id.move_id.name))

            if move_line_id.ref_new:
                ref = move_line_id.ref_new
            else:
                ref = move_line_id.ref


            if not ref:
                raise UserError(_("Please check ref for item %s" % move_line_id.move_id.name))

            if move_line_id.tax_base_amount:
                amount_untaxed = move_line_id.tax_base_amount
            else:
                amount_untaxed = move_line_id.amount_before_tax

            move_line_ids={
                'date': date,
                'ref': ref,
                'partner': move_line_id.partner_id,
                'vat': move_line_id.partner_id.vat,
                'branch': move_line_id.partner_id.branch_no,
                'amount_untaxed': amount_untaxed,
                'debit': move_line_id.debit,
                'credit': move_line_id.credit,
                'note': move_line_id.move_id.name,
                'type': move_line_id.move_id.type
            }
            doc.append(move_line_ids)
        if doc:
            doc.sort(key=lambda k: (k['date'], k['ref']))
        # =================================================================================
        # print('===================================CASE#2==========================================')
        domain = [('account_id.purchase_tax_report', '=', True), ('date_maturity', '>=', data['date_from']),
                  ('date_maturity', '<=', data['date_to']),('move_id.state', '=', 'posted'),
                  ('date_maturity', '!=', False),('exclude_from_invoice_tab','=',True)]
        print('domain:', domain)
        docs = self.env['account.move.line'].search(domain)
        # docs =  docs.filtered(lambda l: l.date_maturity != l.date)
        print('docs:',docs)
        for move_line_id in docs:
            if move_line_id.date_vat_new:
                date_t2 = move_line_id.date_vat_new
                # date_t2 = move_line_id.date_vat_new.strftime("%d/%m/%Y")
            else:
                date_t2 = move_line_id.tax_inv_date
                # date_t2 = move_line_id.tax_inv_date.strftime("%d/%m/%Y")

            if not date_t2:
                raise UserError(_("Please check date for item %s" % move_line_id.move_id.name))

            if move_line_id.ref_new:
                ref = move_line_id.ref_new
            else:
                ref = move_line_id.ref

            if not ref:
                raise UserError(_("Please check ref for item %s" % move_line_id.move_id.name))

            if move_line_id.tax_base_amount:
                amount_untaxed = move_line_id.tax_base_amount
            else:
                amount_untaxed = move_line_id.amount_before_tax

            move_line_ids={
                'date': date_t2,
                'ref': ref,
                'partner': move_line_id.partner_id,
                'vat': move_line_id.partner_id.vat,
                'branch': move_line_id.partner_id.branch_no,
                'amount_untaxed': amount_untaxed,
                'debit': move_line_id.debit,
                'credit': move_line_id.credit,
                'note': move_line_id.move_id.name,
                'type': move_line_id.move_id.type
            }
            doc.append(move_line_ids)
        if doc:
            doc.sort(key=lambda k: (k['date'], k['ref']),reverse=False)

        # print('=====================================CASE#3========================================')
        domain = [('account_id.purchase_tax_report', '=', True), ('date', '>=', data['date_from']),
                  ('date', '<=', data['date_to']),
                  ('move_id.state', '=', 'posted'), ('date_maturity', '=', False),
                  ('move_id.type', 'in', ('in_invoice', 'in_refund', 'entry'))
            , ('exclude_from_invoice_tab', '=', False),('is_special_tax', '=', True)]
        print('domain:', domain)
        docs = self.env['account.move.line'].search(domain)
        # docs =  docs.filtered(lambda l: l.date_maturity != l.date)
        print('docs:', docs)
        for move_line_id in docs:
            if move_line_id.date_vat_new:
                date_t2 = move_line_id.date_vat_new
                # date_t2 = move_line_id.date_vat_new.strftime("%d/%m/%Y")
            else:
                date_t2 = move_line_id.tax_inv_date
                # date_t2 = move_line_id.tax_inv_date.strftime("%d/%m/%Y")

            if not date_t2:
                raise UserError(_("Please check date for item %s" % move_line_id.move_id.name))
            if move_line_id.ref_new:
                ref = move_line_id.ref_new
            else:
                ref = move_line_id.ref

            if not ref:
                raise UserError(_("Please check ref for item %s" % move_line_id.move_id.name))

            if move_line_id.tax_base_amount:
                amount_untaxed = move_line_id.tax_base_amount
            else:
                amount_untaxed = move_line_id.amount_before_tax

            move_line_ids = {
                'date': date_t2,
                'ref': ref,
                'partner': move_line_id.partner_id,
                'vat': move_line_id.partner_id.vat,
                'branch': move_line_id.partner_id.branch_no,
                'amount_untaxed': amount_untaxed,
                'debit': move_line_id.debit,
                'credit': move_line_id.credit,
                'note': move_line_id.move_id.name,
                'type': move_line_id.move_id.type
            }
            doc.append(move_line_ids)
        if doc:
            doc.sort(key=lambda k: (k['date'], k['ref']), reverse=False)


        return {
            'doc_ids': docids,
            'doc_model': 'account.move',
            'docs': doc,
            'company_id': company_id,
            'data': data,
        }
