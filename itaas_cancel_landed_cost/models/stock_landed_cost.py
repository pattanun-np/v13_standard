# -*- coding: utf-8 -*-
# Copyright (C) 2019-present  Technaureus Info Solutions(<http://www.technaureus.com/>).

from odoo import models, fields, api
from openerp import api, fields, models, _
from openerp.osv import expression
from openerp.tools import float_is_zero
from openerp.tools import float_compare, float_round
from openerp.tools.misc import formatLang
from openerp.exceptions import UserError, ValidationError
from datetime import datetime, date


import time
import math


class stock_landed_cost(models.Model):
    _inherit = "stock.landed.cost"

    def button_cancel_after_validate(self):
        # print 'action_set_confirm_return'
        stock_valuation_layer_ids = self.env['stock.valuation.layer'].search([('stock_landed_cost_id','=',self.id)],limit=1)
        stock_valuation_layer_ids.unlink()
        if self.account_move_id:
            self.account_move_id.button_cancel()
            self.account_move_id.with_context(force_delete=True).unlink()
        return self.write({'state': 'cancel'})


