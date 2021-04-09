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
from dateutil.relativedelta import relativedelta

import time
import math


class stock_move(models.Model):
    _inherit = "stock.move"

    def update_account_entry_action_done_all(self):
        stove_move_ids = self.env['stock.move'].search([('product_id.valuation', '=', 'real_time'),('product_id.type','=','product')])
        for stock_move in stove_move_ids:
            if stock_move._is_in() or stock_move._is_out():
                stock_move.update_account_entry_action_done()

    def update_account_entry_action_done(self):
        am_id = self.env['account.move'].search([('stock_move_id','=',self.id)],limit=1)
        if not am_id:
            # print ('Create Account Entry:')
            # print(self.id)
            # print(self.name)
            # Init a dict that will group the moves by valuation type, according to `move._is_valued_type`.
            valued_moves = {valued_type: self.env['stock.move'] for valued_type in self._get_valued_types()}
            for move in self:
                if float_is_zero(move.quantity_done, precision_rounding=move.product_uom.rounding):
                    continue
                for valued_type in self._get_valued_types():
                    if getattr(move, '_is_%s' % valued_type)():
                        valued_moves[valued_type] |= move
                        continue

            # AVCO application
            #valued_moves['in'].product_price_update_before_done()

            #res = super(stock_move, self)._action_done(cancel_backorder=cancel_backorder)

            # '_action_done' might have created an extra move to be valued
            for move in self:
                for valued_type in self._get_valued_types():
                    if getattr(move, '_is_%s' % valued_type)():
                        valued_moves[valued_type] |= move
                        continue

            stock_valuation_layers = self.env['stock.valuation.layer'].sudo()
            # Create the valuation layers in batch by calling `moves._create_valued_type_svl`.
            for valued_type in self._get_valued_types():
                todo_valued_moves = valued_moves[valued_type]
                if todo_valued_moves:
                    todo_valued_moves._sanity_check_for_valuation()
                    stock_valuation_layers |= getattr(todo_valued_moves, '_create_%s_svl' % valued_type)()
                    continue

            for svl in stock_valuation_layers.with_context(active_test=False):
                if not svl.product_id.valuation == 'real_time':
                    continue
                if svl.currency_id.is_zero(svl.value):
                    continue

                # print ('--DO--')
                svl.stock_move_id._account_entry_move(svl.quantity, svl.description, svl.id, svl.value)

    def _create_account_move_line(self, credit_account_id, debit_account_id, journal_id, qty, description, svl_id, cost):
        self.ensure_one()
        date = self._context.get('force_period_date')
        # print ('DATE---')
        if not date:
            # print ('NO date')
            super(stock_move, self).with_context(force_period_date=self.date + relativedelta(hours=+7))._create_account_move_line(credit_account_id,debit_account_id,journal_id,qty,description,svl_id,cost)
        else:
            # print ('yes date')
            super(stock_move, self)._create_account_move_line(credit_account_id,debit_account_id,journal_id,qty,description,svl_id,cost)

        # super(stock_move, self)._create_account_move_line(credit_account_id, debit_account_id, journal_id, qty,
        #                                                   description, svl_id, cost)


        # self.ensure_one()
        # AccountMove = self.env['account.move'].with_context(default_journal_id=journal_id)
        #
        # move_lines = self._prepare_account_move_line(qty, cost, credit_account_id, debit_account_id, description)
        # if move_lines:
        #     date = self._context.get('force_period_date', fields.Date.context_today(self))
        #     new_account_move = AccountMove.sudo().create({
        #         'journal_id': journal_id,
        #         'line_ids': move_lines,
        #         'date': date,
        #         'ref': description,
        #         'stock_move_id': self.id,
        #         'stock_valuation_layer_ids': [(6, None, [svl_id])],
        #         'type': 'entry',
        #     })
        #     new_account_move.post()