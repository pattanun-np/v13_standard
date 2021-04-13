# -*- coding: utf-8 -*-
# Copyright (C) 2020-today ITAAS (Dev K.Book)

from odoo import fields, api, models, _
from bahttext import bahttext
from odoo.exceptions import UserError
from datetime import datetime, date
from collections import defaultdict
from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_is_zero

class StockLandedCost(models.Model):
    _inherit = 'stock.landed.cost'

    manufacturing_ids = fields.Many2many('mrp.production', string='Manufacturing')


    def button_validate(self):
        for cost in self:
            if cost.manufacturing_ids:
                if any(cost.state != 'draft' for cost in self):
                    raise UserError(_('Only draft landed costs can be validated'))
                if not all(cost.manufacturing_ids for cost in self):
                    raise UserError(_('Please define the Manufacturing order on which those additional costs should apply.'))
                cost_without_adjusment_lines = self.filtered(lambda c: not c.valuation_adjustment_lines)
                if cost_without_adjusment_lines:
                    cost_without_adjusment_lines.compute_landed_cost()
                if not self._check_sum():
                    raise UserError(_('Cost and adjustments lines do not match. You should maybe recompute the landed costs.'))

                for cost in self:
                    move = self.env['account.move']
                    move_vals = {
                        'journal_id': cost.account_journal_id.id,
                        'date': cost.date,
                        'ref': cost.name,
                        'line_ids': [],
                        'type': 'entry',
                    }
                    valuation_layer_ids = []
                    cost_to_add_byproduct = defaultdict(lambda: 0.0)
                    for line in cost.valuation_adjustment_lines.filtered(lambda line: line.move_id):
                        remaining_qty = sum(line.move_id.stock_valuation_layer_ids.mapped('remaining_qty'))
                        linked_layer = line.move_id.stock_valuation_layer_ids[:1]

                        # Prorate the value at what's still in stock
                        cost_to_add = (remaining_qty / line.move_id.product_qty) * line.additional_landed_cost
                        if not cost.company_id.currency_id.is_zero(cost_to_add):
                            valuation_layer = self.env['stock.valuation.layer'].create({
                                'value': cost_to_add,
                                'unit_cost': 0,
                                'quantity': 0,
                                'remaining_qty': 0,
                                'stock_valuation_layer_id': linked_layer.id,
                                'description': cost.name,
                                'stock_move_id': line.move_id.id,
                                'product_id': line.move_id.product_id.id,
                                'stock_landed_cost_id': cost.id,
                                'company_id': cost.company_id.id,
                            })
                            linked_layer.remaining_value += cost_to_add
                            valuation_layer_ids.append(valuation_layer.id)
                        # Update the AVCO
                        product = line.move_id.product_id
                        if product.cost_method == 'average':
                            cost_to_add_byproduct[product] += cost_to_add
                        # `remaining_qty` is negative if the move is out and delivered proudcts that were not
                        # in stock.
                        qty_out = 0
                        if line.move_id._is_in():
                            qty_out = line.move_id.product_qty - remaining_qty
                        elif line.move_id._is_out():
                            qty_out = line.move_id.product_qty
                        move_vals['line_ids'] += line._create_accounting_entries(move, qty_out)

                    # batch standard price computation avoid recompute quantity_svl at each iteration
                    products = self.env['product.product'].browse(p.id for p in cost_to_add_byproduct.keys())
                    for product in products:  # iterate on recordset to prefetch efficiently quantity_svl
                        if not float_is_zero(product.quantity_svl, precision_rounding=product.uom_id.rounding):
                            product.with_context(force_company=cost.company_id.id).sudo().standard_price += cost_to_add_byproduct[product] / product.quantity_svl

                    move_vals['stock_valuation_layer_ids'] = [(6, None, valuation_layer_ids)]
                    move = move.create(move_vals)
                    cost.write({'state': 'done', 'account_move_id': move.id})
                    move.post()

                    if cost.vendor_bill_id and cost.vendor_bill_id.state == 'posted' and cost.company_id.anglo_saxon_accounting:
                        all_amls = cost.vendor_bill_id.line_ids | cost.account_move_id.line_ids
                        for product in cost.cost_lines.product_id:
                            accounts = product.product_tmpl_id.get_product_accounts()
                            input_account = accounts['stock_input']
                            all_amls.filtered(lambda aml: aml.account_id == input_account and not aml.full_reconcile_id).reconcile()
                return True
            else:
                return super(StockLandedCost,self).button_validate()


    def get_valuation_lines(self):
        lines = []
        if self.picking_ids and not self.manufacturing_ids:
            print ('------1111111111')
            return super(StockLandedCost,self).get_valuation_lines()

        elif self.manufacturing_ids:
            for move in self.mapped('manufacturing_ids').mapped('finished_move_line_ids'):
                # it doesn't make sense to make a landed cost for a product that isn't set as being valuated in real time at real cost
                if move.product_id.valuation != 'real_time' or move.product_id.cost_method not in ('fifo', 'average') or move.state == 'cancel':
                    continue
                vals = {
                    'product_id': move.product_id.id,
                    'move_id': move.move_id.id,
                    'quantity': move.qty_done,
                    'former_cost': move.move_id.stock_valuation_layer_ids.mapped('value')[0],
                    'weight': move.product_id.weight * move.product_qty,
                    'volume': move.product_id.volume * move.product_qty
                }
                lines.append(vals)

            if not lines and self.mapped('picking_ids'):
                raise UserError(_("You cannot apply landed costs on the chosen transfer(s). Landed costs can only be applied for products with automated inventory valuation and FIFO or average costing method."))
            return lines

    def compute_landed_cost(self):
        if self.manufacturing_ids and not self.picking_ids:
            AdjustementLines = self.env['stock.valuation.adjustment.lines']
            AdjustementLines.search([('cost_id', 'in', self.ids)]).unlink()

            digits = self.env['decimal.precision'].precision_get('Product Price')
            towrite_dict = {}
            for cost in self.filtered(lambda cost: cost.manufacturing_ids):
                total_qty = 0.0
                total_cost = 0.0
                total_weight = 0.0
                total_volume = 0.0
                total_line = 0.0
                all_val_line_values = cost.get_valuation_lines()
                for val_line_values in all_val_line_values:
                    for cost_line in cost.cost_lines:
                        val_line_values.update({'cost_id': cost.id, 'cost_line_id': cost_line.id})
                        print(val_line_values)
                        self.env['stock.valuation.adjustment.lines'].create(val_line_values)

                    total_qty += val_line_values.get('quantity', 0.0)
                    total_weight += val_line_values.get('weight', 0.0)
                    total_volume += val_line_values.get('volume', 0.0)

                    former_cost = val_line_values.get('former_cost', 0.0)
                    # round this because former_cost on the valuation lines is also rounded
                    total_cost += tools.float_round(former_cost, precision_digits=digits) if digits else former_cost

                    total_line += 1

                for line in cost.cost_lines:
                    value_split = 0.0
                    for valuation in cost.valuation_adjustment_lines:
                        value = 0.0
                        if valuation.cost_line_id and valuation.cost_line_id.id == line.id:
                            if line.split_method == 'by_quantity' and total_qty:
                                per_unit = (line.price_unit / total_qty)
                                value = valuation.quantity * per_unit
                            elif line.split_method == 'by_weight' and total_weight:
                                per_unit = (line.price_unit / total_weight)
                                value = valuation.weight * per_unit
                            elif line.split_method == 'by_volume' and total_volume:
                                per_unit = (line.price_unit / total_volume)
                                value = valuation.volume * per_unit
                            elif line.split_method == 'equal':
                                value = (line.price_unit / total_line)
                            elif line.split_method == 'by_current_cost_price' and total_cost:
                                per_unit = (line.price_unit / total_cost)
                                value = valuation.former_cost * per_unit
                            else:
                                value = (line.price_unit / total_line)

                            if digits:
                                value = tools.float_round(value, precision_digits=digits, rounding_method='UP')
                                fnc = min if line.price_unit > 0 else max
                                value = fnc(value, line.price_unit - value_split)
                                value_split += value

                            if valuation.id not in towrite_dict:
                                towrite_dict[valuation.id] = value
                            else:
                                towrite_dict[valuation.id] += value
            for key, value in towrite_dict.items():
                AdjustementLines.browse(key).write({'additional_landed_cost': value})
            return True
        else:
            return super(StockLandedCost, self).compute_landed_cost()


