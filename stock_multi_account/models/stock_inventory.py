# -*- coding: utf-8 -*-
# Copyright (C) 2020-today ITAAS (Dev K.Book)

from odoo import fields, api, models, _
from bahttext import bahttext
from odoo.exceptions import UserError
from datetime import datetime, date




class stock_inventory(models.Model):
    _inherit = 'stock.inventory'

    account_activity_type_id = fields.Many2one('account.activity.type', 'Activity Type')


