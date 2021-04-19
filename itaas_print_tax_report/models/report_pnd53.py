# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from datetime import datetime, timedelta
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT
from odoo import api, fields, models
import math

class report_report_pnd53(models.AbstractModel):
    _name = 'report.itaas_print_tax_report.report_pnd53_id'

    sale_tax = fields.Float()
    purchase_tax = fields.Float()

    #def _get_header_info(self, date_from, date_to, company_id, pp30_1, pp30_1point1, pp30_1point2, pp30_2, pp30_2point1,
    #                    pp30_2point2):
    def _get_header_info(self, date_from, date_to, company_id):
        print('test')
        return {
            'date_from': datetime.strptime(date_from, DEFAULT_SERVER_DATE_FORMAT).strftime('%Y-%m-%d'),
            'date_to': datetime.strptime(date_to, DEFAULT_SERVER_DATE_FORMAT).strftime('%Y-%m-%d'),
            'company_vat': company_id.vat,
            'company_branch': company_id.branch_no,
            'company_name': company_id.name,
            'company_building': company_id.building,
            'company_roomnumber': company_id.roomnumber,
            'company_floornumber': company_id.floornumber,
            'company_village': company_id.village,
            'company_house_number': company_id.house_number,
            'company_moo_number': company_id.moo_number,
            'company_soi_number': company_id.soi_number,
            'company_street': company_id.street,
            'company_tumbon': company_id.street2,
            'company_city' : company_id.city,
            'company_province': company_id.state_id.name,
            'company_code': company_id.zip,
            'company_phone': company_id.phone
        }

    def _get_tax_month(self, date_from, date_to, company_id,type):
        print('vvvvvvvvvv')
        print(date_from)
        print(date_to)
        print(company_id)
        print(type)

        total_amount = 0
        total_wht_amount = 0
        total_item = 0
        total_page = 0
        # wht tax calculation
        domain = [('wht_type.name','=',type),('wht_tax','!=',False)]
        domain.append(('date', '>=', date_from))
        domain.append(('date', '<=', date_to))
        domain.append(('company_id', '=', company_id.id))
        line_ids = self.env['account.move.line'].search(domain)
        # print domain
        if line_ids:
            for line in line_ids:
                # print(line.wht_type.name)
                amt_percent = 0
                if line.wht_tax.name == 'Company Withholding Tax 1% (Transportation)':
                    amt_percent = 1
                elif line.wht_tax.name == 'Company Withholding Tax 1.5% (Service)':
                    amt_percent = 1.5
                elif line.wht_tax.name == 'Company Withholding Tax 2% (Advertising)':
                    amt_percent = 2
                elif line.wht_tax.name == 'Company Withholding Tax 3% (Service)':
                    amt_percent = 3
                elif line.wht_tax.name == 'Company Withholding Tax 5% (Rental)':
                    amt_percent = 5
                elif line.wht_tax.name == 'Personal Withholding Tax 1% (Transportation)':
                    amt_percent = 1
                elif line.wht_tax.name == 'Personal Withholding Tax 1.5% (Service)':
                    amt_percent = 1.5
                elif line.wht_tax.name == 'Personal Withholding Tax 2% (Advertising)':
                    amt_percent = 2
                elif line.wht_tax.name == 'Personal Withholding Tax 3% (Service)':
                    amt_percent = 3
                elif line.wht_tax.name == 'Personal Withholding Tax 5% (Rental)':
                    amt_percent = 5
                elif line.wht_tax.name == 'Withholding Income Tax 1% (Transportation)':
                    amt_percent = 1
                elif line.wht_tax.name == 'Withholding Income Tax 1.5% (Service)':
                    amt_percent = 1.5
                elif line.wht_tax.name == 'Withholding Income Tax 2% (Advertising)':
                    amt_percent = 2
                elif line.wht_tax.name == 'Withholding Income Tax 3% (Service)':
                    amt_percent = 3
                elif line.wht_tax.name == 'Withholding Income Tax 5% (Rental)':
                    amt_percent = 5

                #if amt percent is 1,2,3,5
                if amt_percent:
                    total_item +=1
                    # calculate total paid
                    total_wht_amount += line.credit
                    # print line.credit
                    # print total_wht_amount
                    total_amount += (line.credit * 100) / amt_percent

        else:
            total_amount = 0
            total_wht_amount = 0

        total_page = int(math.ceil(total_item / 6.0))

        print (total_amount)
        print (total_wht_amount)
        print (total_item)
        print (total_page)
        print('=================')
        return {
            'total_amount': total_amount,
            'total_wht_amount': total_wht_amount,
            'total_item': total_item,
            'total_page':total_page,
        }




    @api.model
    def _get_report_values(self, docids, data=None):
        # print "xxxx"
        company_id = self.env.company
        # docs = self.env['account.move.line'].search([('name','=','Output VAT'),('company_id','=',1)])
        header_info = self._get_header_info(data['date_from'], data['date_to'], company_id)
        tax_info = self._get_tax_month(data['date_from'], data['date_to'], company_id,
                                       data['report_type'])

        return {
            'doc_ids': docids,
            'doc_model': 'account.move.line',
            'data': data,
            'get_header_info': header_info,
            'get_tax_info' : tax_info,
            # 'docs': docs,
        }