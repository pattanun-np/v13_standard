# -*- coding: utf-8 -*-
# Copyright (C) 2016-Today  itaas.co.th

from odoo import api, fields, models, _

class Account_Tax(models.Model):
    _inherit = 'account.tax'

    wht = fields.Boolean(string="WHT")
    wht_type = fields.Many2one('account.wht.type', string='WHT Type')
    tax_report = fields.Boolean(string="Tax Report")
    tax_no_refund = fields.Boolean(string="Tax No Refund")
