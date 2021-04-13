# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class MrpWorkcenter(models.Model):
    _inherit = 'mrp.workcenter'


    partial_confirmation = fields.Boolean(_('Partial Confirmation'), default=True)
    start_without_stock = fields.Boolean(_('No Material Availability'), default=False)