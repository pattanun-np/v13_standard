# -*- coding: utf-8 -*-
# Copyright (C) 2020-today ITAAS (Dev K.Book)

from odoo import fields, api, models, _
from bahttext import bahttext
from odoo.exceptions import UserError
from datetime import datetime, date



class StockLocation(models.Model):
    _inherit = 'stock.location'

    is_multi_in_account = fields.Boolean('Is Multi Stock In Account')
    multi_input_ids = fields.One2many('location.multi.input', 'location_id', 'Multi Stock Input Account')

    is_multi_out_account = fields.Boolean('Is Multi Stock Out Account')
    multi_output_ids = fields.One2many('location.multi.output', 'location_id', 'Multi Stock Output Account')


class LocationMultiInput(models.Model):
    _name = 'location.multi.input'

    location_id = fields.Many2one('stock.location','Stock Location', required=True, ondelete='cascade', index=True,
                               copy=False)
    account_activity_type_id = fields.Many2one('account.activity.type','Activity Type',required=True)
    stock_account_input_location_id = fields.Many2one(
        'account.account', 'Stock Input Account', company_dependent=True,
        domain="[('company_id', '=', allowed_company_ids[0]), ('deprecated', '=', False)]", check_company=True,
        help="""When doing automated inventory valuation, counterpart journal items for all incoming stock moves will be posted in this account,
                    unless there is a specific valuation account set on the source location. This is the default value for all products in this category.
                    It can also directly be set on each product.""",required=True)
    remark = fields.Char('Remark')


class LocationMultiOutput(models.Model):
    _name = 'location.multi.output'

    location_id = fields.Many2one('stock.location', 'Stock Location', required=True, ondelete='cascade', index=True,
                               copy=False)
    account_activity_type_id = fields.Many2one('account.activity.type','Activity Type', required=True)
    stock_account_output_location_id = fields.Many2one(
        'account.account', 'Stock Output Account', company_dependent=True,
        domain="[('company_id', '=', allowed_company_ids[0]), ('deprecated', '=', False)]", check_company=True,
        help="""When doing automated inventory valuation, counterpart journal items for all outgoing stock moves will be posted in this account,
                    unless there is a specific valuation account set on the destination location. This is the default value for all products in this category.
                    It can also directly be set on each product.""",required=True)
    remark = fields.Char('Remark')

