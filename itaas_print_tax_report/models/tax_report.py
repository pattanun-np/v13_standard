# -*- coding: utf-8 -*-
# Copyright (C) 2020-today ITAAS (Dev K.Book)

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class report_sale_tax_report(models.AbstractModel):
    _name = 'report.itaas_print_tax_report.sale_tax_report_id'

    @api.model
    def _get_report_values(self, docids, data=None):
        print('def _get_report_values sale')
        company_id = self.env.company
        invoice_step = company_id.invoice_step
        if invoice_step == '1step':
            domain = [('invoice_id.type', 'in', ('out_invoice', 'out_refund')),
                      ('invoice_id.number', '!=', False),
                      ('invoice_id.state', '!=', 'draft'),
                      ('tax_id', '=', [data['form']['tax_id'][0]]),
                      ('invoice_id.date_invoice', '>=', data['form']['date_from']),
                      ('invoice_id.date_invoice', '<=', data['form']['date_to'])]
            print('1step domain: ',domain)
            # docs = self.env['account.invoice'].search(domain, order='date_invoice,number asc')
            docs = self.env['account.invoice.tax'].search(domain).mapped('invoice_id')
            docs = sorted(docs, key=lambda x: x.date_invoice and x.number)
            print('len(docs): ', len(docs))
            print('docs: ', docs)
        else:
            domain = [('invoice_id.type', 'in', ('out_invoice', 'out_refund')),
                      ('invoice_id.tax_inv_generated', '=', True),
                      ('invoice_id.tax_inv_no', '!=', False),
                      ('tax_id', '=', [data['form']['tax_id'][0]]),
                      ('invoice_id.tax_inv_date', '>=', data['form']['date_from']),
                      ('invoice_id.tax_inv_date', '<=', data['form']['date_to'])]
            print('not domain: ', domain)
            docs = self.env['account.invoice.tax'].search(domain).mapped('invoice_id')
            docs = sorted(docs, key=lambda x: x.tax_inv_date and x.tax_inv_no)
        if not docs:
            raise UserError(_('There is no invoices between this date range.'))

        return {
            'doc_ids': docids,
            'doc_model': 'account.invoice',
            'docs': docs,
            'company_id': company_id,
            'data': data['form'],
            'step': invoice_step,
        }


class report_purchase_tax_report(models.AbstractModel):
    _name = 'report.itaas_print_tax_report.purchase_tax_report_id'

    @api.model
    def _get_report_values(self, docids, data=None):
        # company_id = self.env['res.company'].sudo().browse(data['form']['company_id'][0])
        company_id = self.env.company

        domain =[('is_closing_month','=',False)]
        if data['form']['tax_id']:
            account_id = self.env['account.tax'].browse(data['form']['tax_id'][0]).account_id
            domain.append(('account_id', '=', account_id.id))
        if data['form']['date_from']:
            domain.append(('date', '>=', data['form']['date_from']))
        if data['form']['date_to']:
            domain.append(('date', '<=', data['form']['date_to']))
        print('domain: ', domain)
        docs = self.env['account.move.line'].search(domain, order='invoice_date asc')
        if not docs:
            raise UserError(_('There is no invoices between this date range.'))

        return {
            'doc_ids': docids,
            'doc_model': 'account.move.line',
            'docs': docs,
            'company_id': company_id,
            'data': data['form'],
        }