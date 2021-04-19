# -*- coding: utf-8 -*-
# Copyright (C) 2016-Today (ITAAS)

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

class ResPartner(models.Model):
    _inherit = 'res.partner'

    branch_no = fields.Char(string='Branch',default='00000')
    customer_no_vat = fields.Boolean(string='Customer No TAX-ID',default=False)