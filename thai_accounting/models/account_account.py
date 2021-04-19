# -*- coding: utf-8 -*-
# Copyright (C) 2016-2017  Technaureus Info Solutions(<http://technaureus.com/>).

from odoo import api, fields, models, _
from odoo.tools.misc import formatLang
import time
from odoo.exceptions import UserError

class account_account(models.Model):
    _inherit = "account.account"

    wht = fields.Boolean(string='Witholding Tax')
    wht_income = fields.Boolean(string='Witholding Income Tax')
    bank_fee = fields.Boolean(string='ค่าธรรมเนียม')
    diff_little_money = fields.Boolean(string='เศษสตางค์')
    sale_tax_report = fields.Boolean(string='รายงานภาษีขาย')
    purchase_tax_report = fields.Boolean(string='รายงานภาษีซื้อ')
    is_cheque = fields.Boolean(string='Account for Cheque')


