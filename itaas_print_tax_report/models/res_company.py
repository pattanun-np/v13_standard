# -*- coding: utf-8 -*-
from openerp import fields, api, models, _
from bahttext import bahttext
from openerp.exceptions import UserError
from datetime import datetime, date

class res_company(models.Model):
    _inherit ="res.company"

    purchase_order_no_form = fields.Char(string='Purchase Order No. Form')
    show_product_code_on_purchase = fields.Boolean(string='Show Code in Purchase')
    show_currency_on_purchase = fields.Boolean(string='Show Currency in Purchase')
    show_date_auto_purchase = fields.Boolean(string='Show Date Purchase')
    pnd_1kor_position = fields.Integer(string='ตำแหน่งภงด 1ก')
    pnd_1kor_special_position = fields.Integer(string='ตำแหน่งภงด 1ก Special')
    pnd_2_position = fields.Integer(string='ตำแหน่งภงด 2')
    pnd_3_position = fields.Integer(string='ตำแหน่งภงด 3')
    pnd_2kor_position = fields.Integer(string='ตำแหน่งภงด 2ก')
    pnd_3kor_position = fields.Integer(string='ตำแหน่งภงด 3ก')
    pnd_53_position = fields.Integer(string='ตำแหน่งภงด 53')





