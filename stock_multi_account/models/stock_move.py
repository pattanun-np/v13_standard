# -*- coding: utf-8 -*-
# Copyright (C) 2020-today ITAAS (Dev K.Book)

from odoo import fields, api, models, _
from bahttext import bahttext
from odoo.exceptions import UserError
from datetime import datetime, date

class StockPickingType(models.Model):
    _inherit = 'stock.picking.type'

    account_activity_type_id = fields.Many2one('account.activity.type','Activity Type',)


# ------------------------------------------- compute correct account --------
class stock_move(models.Model):
    _inherit = 'stock.move'

    def _get_accounting_data_for_valuation(self):
        journal_id, acc_src, acc_dest, acc_valuation = super(stock_move, self)._get_accounting_data_for_valuation()
        print ('ACCOUNT DATA--')
        print (journal_id)
        print(acc_src)
        print (acc_dest)
        print (acc_valuation)
        # return journal_id, acc_src, acc_dest, acc_valuation
        for move in self:
            account_activity_type_id = self.env.context.get('account_activity_type_id')
            #1-move-in
            #2-move-out
            #3-production-in
            #4-production-out
            #5-inventory-in
            #6-inventory-out
            if move.picking_id: ##this is stock movement
                if move.picking_id.account_activity_type_id:
                    account_activity_type_id = move.picking_id.account_activity_type_id

                if self._is_in():
                    print ('CASE#1')
                    if move.product_id and move.product_id.categ_id.is_multi_input:

                        if not account_activity_type_id:
                            account_activity_type_id = move.picking_id.picking_type_id.account_activity_type_id

                        activity_line_id = move.product_id.categ_id.multi_input_ids.filtered(lambda a: a.account_activity_type_id == account_activity_type_id)
                        if activity_line_id:

                            #replace current one to new one by activity
                            acc_src = activity_line_id.stock_account_input_categ_id.id

                elif self._is_out():
                    print('CASE#2')
                    if move.product_id and move.product_id.categ_id.is_multi_output:
                        if not account_activity_type_id:
                            account_activity_type_id = move.picking_id.picking_type_id.account_activity_type_id

                        activity_line_id = move.product_id.categ_id.multi_output_ids.filtered(
                            lambda a: a.account_activity_type_id == account_activity_type_id)
                        # print(acc_src)
                        # print(acc_dest)
                        if activity_line_id:
                            acc_dest = activity_line_id.stock_account_output_categ_id.id



            elif move.production_id: ##this is production
                print ('--PRODUCTION')
                if self._is_in():
                    print('CASE#3')
                    if move.product_id and move.product_id.categ_id.is_multi_input:
                        if not account_activity_type_id:
                            account_activity_type_id = move.production_id.picking_type_id.account_activity_type_id

                        activity_line_id = move.product_id.categ_id.multi_input_ids.filtered(
                            lambda a: a.account_activity_type_id == account_activity_type_id)
                        if activity_line_id:
                            # replace current one to new one by activity
                            acc_src = activity_line_id.stock_account_input_categ_id.id

                elif self._is_out():
                    print('CASE#4')
                    if move.product_id and move.product_id.categ_id.is_multi_output:
                        if not account_activity_type_id:
                            account_activity_type_id = move.production_id.picking_type_id.account_activity_type_id

                        activity_line_id = move.product_id.categ_id.multi_output_ids.filtered(
                            lambda a: a.account_activity_type_id == account_activity_type_id)
                        # print(acc_src)
                        # print(acc_dest)
                        if activity_line_id:
                            acc_dest = activity_line_id.stock_account_output_categ_id.id

            elif move.inventory_id: #this is from inventory adjustment
                print ('--ADjust')
                if self._is_in():
                    print ('CASE#5') #from adjust to internal, then it is in
                    if move.inventory_id.account_activity_type_id and move.location_id.is_multi_in_account:
                        activity_line_id = move.location_id.multi_input_ids.filtered(lambda a: a.account_activity_type_id == move.inventory_id.account_activity_type_id)
                        # print(acc_src)
                        # print(acc_dest)
                        if activity_line_id:
                            #replace current one to new one by activity
                            acc_src = activity_line_id.stock_account_input_location_id.id

                        # print(acc_src)
                        # print(acc_dest)

                elif self._is_out():
                    print('CASE#6') #from internal to adjust, then it is out
                    if move.inventory_id.account_activity_type_id and move.location_dest_id.is_multi_out_account:
                        activity_line_id = move.location_dest_id.multi_output_ids.filtered(lambda a: a.account_activity_type_id == move.inventory_id.account_activity_type_id)
                        # print(acc_src)
                        # print(acc_dest)
                        if activity_line_id:
                            acc_dest = activity_line_id.stock_account_output_location_id.id

                        # print (acc_src)
                        # print(acc_dest)
                        # print ('MULTI OUTPUT')

        return journal_id, acc_src, acc_dest, acc_valuation

