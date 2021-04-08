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


class Account_Cheque_Statement_return(models.Model):
    _inherit = "account.cheque.statement"

    state = fields.Selection(
        selection_add=[('return', 'Return')],
    )

    @api.multi
    def set_to_draft(self):
        self.write({'state': 'open'})



    @api.multi
    def action_set_confirm_return(self):
        print 'action_set_confirm_return'
        self.action_validate()
        self.action_return()
        self.write({'state': 'return'})

    @api.multi
    def action_return(self):
        if self.move_new_id:
            print 'move_new_id:',self.move_new_id
            adj_moves = self.env['account.move']
            adj_moves = self.move_new_id
            print 'reverse_entry',adj_moves
            adj_moves.reverse_moves(self.move_new_id.date,self.move_new_id.journal_id or False)
            self.write({'state': 'return'})





