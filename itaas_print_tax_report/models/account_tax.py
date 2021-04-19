# -*- coding: utf-8 -*-
# Copyright (C) 2016-2017  Technaureus Info Solutions(<http://technaureus.com/>).

from odoo import api, fields, models, _

class Account_Tax(models.Model):
    _inherit = 'account.tax'

    wht_personal_company = fields.Selection([('personal', 'ภงด3'), ('company', 'ภงด53'),('pnd1_kor', 'ภงด1ก'),('pnd1_kor_special', 'ภงด1ก พิเศษ'),('pnd2', 'ภงด2'),('pnd2_kor', 'ภงด2ก'),('personal_kor', 'ภงด3ก')])

class account_move(models.Model):
    _inherit = 'account.move'


class account_move_line_inherit(models.Model):
    _inherit ="account.move.line"

    tax_inv_date = fields.Date(string="Tax Inv Date", related="move_id.tax_invoice_date")
    date_vat_new = fields.Date(string="Date Vat" ,copy=False)
    ref_new = fields.Char(string="Ref" ,copy=False)
    is_special_tax = fields.Boolean(string='Special Tax')




