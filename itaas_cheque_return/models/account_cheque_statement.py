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


    def set_to_draft(self):
        self.write({'state': 'open'})



    def action_set_confirm_return(self):
        # print 'action_set_confirm_return'
        self.action_validate()
        self.action_return()
        self.write({'state': 'return'})

    def action_return(self):
        if self.move_new_id:
            # print 'move_new_id:',self.move_new_id
            # adj_moves = self.env['account.move']
            adj_moves = self.move_new_id
            # print 'reverse_entry',adj_moves
            # adj_moves._reverse_moves(self.move_new_id.date,self.move_new_id.journal_id or False)
            if self.move_id.journal_id.adj_journal:
                journal_id =  self.move_id.journal_id.adj_journal.id
            else:
                journal_id = self.move_new_id.journal_id.id
            adj_moves._reverse_moves([{'date': self.move_new_id.date, 'ref': _('Reversal of %s') % self.move_new_id.name,'journal_id':journal_id}], cancel=True)
            self.write({'state': 'return'})





