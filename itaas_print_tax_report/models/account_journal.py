# -*- coding: utf-8 -*-
# Copyright (C) 2016-2017  Technaureus Info Solutions(<http://technaureus.com/>).

from odoo import api, fields, models, _

class Account_journal(models.Model):
    _inherit = 'account.journal'

    type_vat = fields.Selection([('tax', 'Tax'), ('not_deal', 'Not Due')],string='Type Vat')
