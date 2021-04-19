# -*- coding: utf-8 -*-
# Copyright (C) 2020-today ITAAS (Dev K.Book)

from odoo import fields, api, models, _
from bahttext import bahttext
from odoo.exceptions import UserError
from datetime import datetime, date

class StockPickingType(models.Model):
    _inherit = 'stock.picking.type'

    account_activity_type_id = fields.Many2one('account.activity.type','Activity Type',)

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    account_activity_type_id = fields.Many2one('account.activity.type','Activity Type')


