# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_compare


class stock_move(models.Model):
    _inherit = 'stock.move'

    rm_fg_cal_qty = fields.Float(string='RM qty already cal to FG')
    cost_already_recorded = fields.Boolean(string='Cost already record',default=False)
    #don't use yet.
    # max_fg_qty = fields.Integer(string='Max FG Qty')

class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    
    analytic_account_id = fields.Many2one('account.analytic.account', string=_('Analytic Account'), readonly=True, states={'draft': [('readonly', False)]})
    
    prod_std_cost = fields.Float(digits='Product Price', string=_('Current Standard Cost'), compute='calculate_planned_costs', store=True, 
        group_operator="avg")
    cur_std_mat_cost = fields.Float(digits='Product Price', string=_('Planned Material Unit Cost'), compute='calculate_planned_costs', store=True, 
        group_operator="avg")
    cur_std_lab_cost = fields.Float(digits='Product Price', string=_('Planned Direct Variable Unit Cost'), compute='calculate_planned_costs', store=True, 
        group_operator="avg")
    cur_std_fixed_cost = fields.Float(digits='Product Price', string=_('Planned Direct Fixed Unit Cost'), compute='calculate_planned_costs', store=True, 
        group_operator="avg")
    cur_std_direct_cost = fields.Float(digits='Product Price', string=_('Planned Direct Unit Cost'), compute='calculate_planned_costs', store=True, 
        group_operator="avg")
    cur_std_byproduct_amount = fields.Float(digits='Product Price', string=_('Planned ByProduct Amount'), compute='calculate_planned_by_product_amount', store=True)
        
    mat_cost = fields.Float(digits='Product Price', string=_('Actual Material Cost'), compute='calculate_material_cost', store=True)
    mat_cost_unit = fields.Float(digits='Product Price', string=_('Actual Material Unit Cost'), compute='calculate_material_cost', store=True, group_operator="avg")
    lab_cost = fields.Float(digits='Product Price', string=_('Actual Direct Variable Cost'), compute='calculate_actual_costs', store=True)
    lab_cost_unit = fields.Float(digits='Product Price', string=_('Actual Direct Variable Unit Cost'), compute='calculate_actual_costs', store=True, 
        group_operator="avg")
    fixed_cost = fields.Float(digits='Product Price', string=_('Actual Direct Fixed Cost'), compute='calculate_actual_costs', store=True)
    fixed_cost_unit = fields.Float(digits='Product Price', string=_('Actual Direct Fixed Unit Cost'), compute='calculate_actual_costs', store=True, 
        group_operator="avg")
    direct_cost = fields.Float(digits='Product Price', string=_('Actual Full Direct Cost'), compute='calculate_actual_costs', store=True)
    direct_cost_unit = fields.Float(digits='Product Price', string=_('Actual Full Direct Unit Cost'), compute='calculate_actual_costs', store=True, group_operator="avg")
    by_product_amount = fields.Float(digits='Product Price', string=_('Actual ByProduct Amount'), compute='calculate_actual_by_product_amount', store=True)
    by_product_unit_amount = fields.Float(digits='Product Price', string=_('Actual ByProduct Unit Amount'), compute='calculate_actual_by_product_amount', store=True, 
        group_operator="avg")
    
    delta_mat_cost = fields.Float(digits='Product Price', string=_('Delta Material Unit Cost'), compute='calculate_delta_unit_costs', store=True)
    delta_lab_cost = fields.Float(digits='Product Price', string=_('Delta Direct Variable Unit Cost'), compute='calculate_delta_unit_costs', store=True)
    delta_fixed_cost = fields.Float(digits='Product Price', string=_('Delta Direct Fixed Unit Cost'), compute='calculate_delta_unit_costs', store=True)
    delta_direct_cost = fields.Float(digits='Product Price', string=_('Delta Direct Unit Cost'), compute='calculate_delta_unit_costs', store=True)
    delta_byproduct = fields.Float(digits='Product Price', string=_('Delta ByProduct Amount'), compute='calculate_delta_unit_costs', store=True)
    
    wip_amount = fields.Float(digits='Product Price', string=_('WIP Amount'), compute='calculate_wip_amount', store=True)
    
    currency_id = fields.Many2one('res.currency', string='Currency', default=lambda self: self.env.user.company_id.currency_id.id)

    is_material_consume = fields.Boolean(string='Material Consumed First',default=True) #if post as odoo standard

    @api.depends('move_raw_ids.state', 'move_finished_ids.state', 'workorder_ids', 'workorder_ids.state',
                 'qty_produced', 'move_raw_ids.quantity_done', 'product_qty')
    def _compute_state(self):
        for production in self:
            if production.is_material_consume and production.move_finished_ids.filtered(
                lambda m: m.state not in ('cancel', 'done') and m.product_id.id == production.product_id.id) \
                and (production.qty_produced >= production.product_qty) \
                and (not production.routing_id or all(
                wo_state in ('cancel', 'done') for wo_state in production.workorder_ids.mapped('state'))):
                production.state = 'to_close'

            else:
                super(MrpProduction, production)._compute_state()


    def button_mark_done(self):
        self.ensure_one()
        res = super(MrpProduction, self).button_mark_done()
        self.check_wip_to_fg_diff_amount()
        return res

    def check_wip_to_fg_diff_amount(self):
        for production_id in self:
            move_finished_ids = production_id.move_finished_ids.filtered(lambda x: x.state =='done' and x.quantity_done > 0)
            #last record with production product is FG
            sum_account_credit = sum_account_debit = 0
            if move_finished_ids:
                am = self.env['account.move'].search([('stock_move_id','=',move_finished_ids[0].id)],limit=1)
                # print (aml.id)

                for aml_id in am.line_ids:
                    if aml_id.credit:

                        sum_account_credit = sum(aml.credit for aml in self.env['account.move.line'].search([('manufacture_order_id','=',production_id.id),('credit','!=',0),('account_id','=',aml_id.account_id.id)]))
                        sum_account_debit = sum(aml.debit for aml in self.env['account.move.line'].search(
                            [('manufacture_order_id', '=', production_id.id), ('debit', '!=', 0),
                             ('account_id', '=', aml_id.account_id.id)]))

                        if float_compare(sum_account_debit - sum_account_credit, 0.00, precision_digits=2) < 0:
                            val_move = {
                                'journal_id': aml_id.move_id.journal_id.id,
                                'date': aml_id.date,
                                'ref': "Difference WIP and FG",
                                'company_id': aml_id.company_id.id,
                            }
                            id_created_header = self.env['account.move'].create(val_move)
                            val_debit = {
                                'move_id': id_created_header.id,
                                'account_id': aml_id.account_id.id,
                                'credit': 0.00,
                                'debit': sum_account_credit - sum_account_debit,
                                'name': "Difference WIP and FG",
                                'manufacture_order_id': production_id.id,

                            }
                            self.env['account.move.line'].with_context(check_move_validity=False).create(val_debit)
                            val_credit = {
                                'move_id': id_created_header.id,
                                'account_id': production_id.company_id.wip_fg_difference_account_id.id,
                                'credit': sum_account_credit - sum_account_debit,
                                'debit': 0.00,
                                'name': "Difference WIP and FG",
                                'manufacture_order_id': production_id.id,
                            }
                            self.env['account.move.line'].with_context(check_move_validity=False).create(val_credit)
                            id_created_header.post()

                        elif float_compare(sum_account_debit - sum_account_credit, 0.00, precision_digits=2) > 0:
                            val_move = {
                                'journal_id': aml_id.move_id.journal_id.id,
                                'date': aml_id.date,
                                'ref': "Difference WIP and FG",
                                'company_id': aml_id.company_id.id,
                            }
                            id_created_header = self.env['account.move'].create(val_move)

                            val_credit = {
                                'move_id': id_created_header.id,
                                'account_id': aml_id.account_id.id,
                                'credit': sum_account_debit - sum_account_credit,
                                'debit': 0.0,
                                'name': "Difference WIP and FG",
                                'manufacture_order_id': production_id.id,

                            }
                            self.env['account.move.line'].with_context(check_move_validity=False).create(val_credit)
                            val_debit = {
                                'move_id': id_created_header.id,
                                'account_id': production_id.company_id.wip_fg_difference_account_id.id,
                                'credit':0.00,
                                'debit': sum_account_debit - sum_account_credit,
                                'name': "Difference WIP and FG",
                                'manufacture_order_id': production_id.id,
                            }
                            self.env['account.move.line'].with_context(check_move_validity=False).create(val_debit)

                            id_created_header.post()

    def post_inventory(self):
        for order in self:
            # print (x)
            order.consume_material_to_wip()
            super(MrpProduction, order).post_inventory()

            # for wo in order.workorder_ids:
            #     wo._direct_cost_postings()
        # print (x)
        return True

    def _cal_price(self, consumed_moves):
        for order in self:
            super(MrpProduction, order)._cal_price(consumed_moves)
            all_finished_move = self.move_finished_ids.filtered(
                lambda x: x.state not in ('done', 'cancel') and x.quantity_done > 0)

            finished_move = self.move_finished_ids.filtered(
                lambda x: x.product_id == self.product_id and x.state not in ('done', 'cancel') and x.quantity_done > 0)
            # print('-FINI?SH MVE')
            # print(finished_move)
            # print (finished_move.quantity_done)

            qty_done = finished_move.product_uom._compute_quantity(finished_move.quantity_done,
                                                                   finished_move.product_id.uom_id)

            if finished_move:
                factor = order.product_uom_id._compute_quantity(finished_move.quantity_done,order.bom_id.product_uom_id) / order.bom_id.product_qty
                # move_ids = []
                moves_done_ids = order.move_raw_ids.filtered(lambda x: x.state == 'done' and not x.cost_already_recorded)
                print (moves_done_ids)
                print ('-CAL PRICE')
                value = 0.00 #cost of fg from stock move of rm
                for bom_line in order.bom_id.bom_line_ids:
                    move_qty = bom_line.product_qty * factor
                    pending_qty = move_qty
                    print (moves_done_ids.filtered(lambda x: x.product_id == bom_line.product_id))
                    for move in moves_done_ids.filtered(lambda x: x.product_id == bom_line.product_id):
                        # print ('FG QTY' + str(qty_done))
                        # print ('Factor:' + str(factor))
                        # print ('RM QTY' + str(move_qty))
                        # print ('VALUE:')
                        # print (-move.stock_valuation_layer_ids.value)

                        if pending_qty < move.product_uom_qty - move.rm_fg_cal_qty:
                            # print ('CASE:1')
                            # print ('Pending Qty:' + str(pending_qty))
                            # print (move.rm_fg_cal_qty)
                            # print (move.product_uom_qty)
                            # print ('---------')
                            move.write({'rm_fg_cal_qty': move.rm_fg_cal_qty + pending_qty})
                            value += ((-move.stock_valuation_layer_ids.value) / move.product_uom_qty) * pending_qty
                            pending_qty = 0
                        elif pending_qty == move.product_uom_qty - move.rm_fg_cal_qty:
                            # print('CASE:2')
                            # print('Pending Qty:' + str(pending_qty))
                            # print(move.rm_fg_cal_qty)
                            # print(move.product_uom_qty)
                            # print('---------')
                            move.write({'rm_fg_cal_qty': move.rm_fg_cal_qty + pending_qty})
                            value += ((-move.stock_valuation_layer_ids.value) / move.product_uom_qty) * pending_qty
                            move.write({'cost_already_recorded': True})
                            pending_qty = 0

                        else:
                            # print('CASE:3')
                            # print('Pending Qty Before:' + str(pending_qty))
                            print(move.product_uom_qty)
                            print(move.rm_fg_cal_qty)
                            available_qty = move.product_uom_qty - move.rm_fg_cal_qty
                            # print('Available:' + str(available_qty))
                            pending_qty = pending_qty - available_qty

                            # print('Pending Qty After:' + str(pending_qty))
                            # print('---------')
                            move.write({'rm_fg_cal_qty': move.product_uom_qty})
                            move.write({'cost_already_recorded': True})
                            value += ((-move.stock_valuation_layer_ids.value) / move.product_uom_qty) * available_qty

                        # print ('Value:' + str(value))
                        # print ('Pending End Move:' + str(pending_qty))
                        if not pending_qty:
                            break


                work_order_cost_unit_per_fg = 0
                finished_move.ensure_one()
                for work_order in self.workorder_ids:

                    time_lines = work_order.time_ids.filtered(lambda x: x.date_end and x.cost_already_recorded)
                    duration = sum(time_lines.mapped('duration'))
                    all_value_by_duration = (duration / 60.0) * work_order.workcenter_id.costs_hour
                    # print ('WO Duration')
                    # print (all_value_by_duration)
                    # print (work_order.value_post)
                    # print (work_order.qty_produced)
                    # print (work_order.qty_post)
                    pending_value_to_post = all_value_by_duration - work_order.value_post
                    pending_fg_to_post = work_order.qty_produced - work_order.qty_post
                    # print(work_order.name)
                    # print (pending_value_to_post)
                    # print (pending_fg_to_post)
                    work_order_cost_unit = pending_value_to_post / pending_fg_to_post #per work order
                    work_order_cost_unit_per_fg += work_order_cost_unit #per fg post
                    # print ('work_center_cost_unit:' + str(work_order_cost_unit))
                    work_order.write({'qty_post': work_order.qty_post + qty_done})
                    work_order.write({'value_post': work_order.value_post + (work_order_cost_unit * qty_done)})
                    # print (x)

                if finished_move.product_id.cost_method in ('fifo', 'average'):
                    qty_done = finished_move.product_uom._compute_quantity(finished_move.quantity_done,
                                                                           finished_move.product_id.uom_id)
                    extra_cost = self.extra_cost * qty_done
                    print ('CAL VALUE')
                    # print (value)
                    # print (work_order_cost_unit_per_fg)
                    print (value + (work_order_cost_unit_per_fg * qty_done) + extra_cost)
                    finished_move.price_unit = (value + (work_order_cost_unit_per_fg * qty_done) + extra_cost) / qty_done

                    # print (finished_move.price_unit)

                #for by product
                if self.bom_id.byproduct_ids:
                    total_by_product_cost = 0
                    # fg_price_unit =
                    pending_fg_price_unit = finished_move.price_unit

                    total_volume = sum(move.product_id.volume * move.product_uom_qty for move in all_finished_move)

                    for by_product_id in self.bom_id.byproduct_ids:
                        # print ('by PRODUCT ID')
                        # print(by_product_id)
                        by_product_moves = self.move_finished_ids.filtered(
                            lambda x: x.product_id == by_product_id.product_id and x.state not in (
                            'done', 'cancel') and x.quantity_done > 0)
                        if by_product_moves:
                            for move in by_product_moves:
                                if move.product_id.cost_method in (
                                'fifo', 'average') and move.product_id.volume and total_volume:
                                    by_product_cost = (move.product_id.volume * move.product_uom_qty / total_volume) * finished_move.price_unit
                                else:
                                    by_product_cost = move.product_id.standard_price

                                pending_fg_price_unit -= by_product_cost
                                move.price_unit = by_product_cost

                                total_by_product_cost += by_product_cost

                    if finished_move:
                        finished_move.ensure_one()
                        if finished_move.product_id.cost_method in ('fifo', 'average'):
                            finished_move.price_unit = pending_fg_price_unit

    def consume_material_to_wip(self):
        for order in self:
            if not order.is_material_consume:
                continue
            else:
                moves_not_to_do = order.move_raw_ids.filtered(lambda x: x.state == 'done')
                moves_to_do = order.move_raw_ids.filtered(lambda x: x.state not in ('done', 'cancel'))
                for move in moves_to_do.filtered(lambda m: m.product_qty == 0.0 and m.quantity_done > 0):
                    move.product_uom_qty = move.quantity_done
                # MRP do not merge move, catch the result of _action_done in order
                # to get extra moves.
                # print ('--MOVE TO DO')
                # print (moves_not_to_do)
                # print (moves_to_do)
                moves_to_do._action_done()


                ######### additional moves_to_do
                moves_to_do = order.move_raw_ids.filtered(lambda x: x.state == 'done') - moves_not_to_do
                print (moves_to_do)
                #########
                # order._cal_price(moves_to_do)


                order.workorder_ids.mapped('raw_workorder_line_ids').unlink()
                order.action_assign()

                # remove FG
                # moves_to_finish = moves_to_finish._action_done()
                # order.workorder_ids.mapped('finished_workorder_line_ids').unlink()
                moves_to_finish = order.move_finished_ids.filtered(lambda x: x.state not in ('done', 'cancel'))
                consume_move_lines = moves_to_do.mapped('move_line_ids')
                for moveline in moves_to_finish.mapped('move_line_ids'):
                    # print ('-UPDATe MOVE TO FINISH and Consume--')
                    if moveline.move_id.has_tracking != 'none' and moveline.product_id == order.product_id or moveline.lot_id in consume_move_lines.mapped(
                            'lot_produced_ids'):
                        if any([not ml.lot_produced_ids for ml in consume_move_lines]):
                            raise UserError(_('You can not consume without telling for which lot you consumed it'))
                        # Link all movelines in the consumed with same lot_produced_ids false or the correct lot_produced_ids
                        filtered_lines = consume_move_lines.filtered(lambda ml: moveline.lot_id in ml.lot_produced_ids)
                        moveline.write({'consume_line_ids': [(6, 0, [x for x in filtered_lines.ids])]})
                    else:
                        # Link with everything
                        moveline.write({'consume_line_ids': [(6, 0, [x for x in consume_move_lines.ids])]})

            for wo in order.workorder_ids:
                wo._direct_cost_postings()



    @api.depends('state')
    def calculate_wip_amount(self):
        wipamount = 0.0
        for production in self:
            if production.state != 'done':
                finished_move_ids = self.move_finished_ids.filtered(lambda x: x.state =='done' and x.quantity_done > 0)
                finish_cost = sum(move.price_unit * move.product_uom_qty for move in finished_move_ids)

                all_wipamount = production.mat_cost + production.lab_cost + production.fixed_cost
                wipamount = all_wipamount - finish_cost

            production.wip_amount = wipamount
        return True
    
    @api.depends('product_id','bom_id','routing_id', 'cur_std_byproduct_amount')
    def calculate_planned_costs(self):
        costmat = 0.0
        costlab = 0.0
        costfixed = 0.0
        for production in self:
            result, result2 = production.bom_id.explode(production.product_id, 1)
            for sbom, sbom_data in result2:
                costmat += sbom.product_id.standard_price * sbom_data['qty']
            if production.routing_id:
                for activity in production.routing_id.operation_ids:
                    costlab += (activity.time_cycle/60) * activity.workcenter_id.costs_hour
                    costfixed += (activity.workcenter_id.time_stop + activity.workcenter_id.time_start) * activity.workcenter_id.cost_hour_fixed / 60
            production.prod_std_cost = production.product_id.standard_price
            production.cur_std_mat_cost = costmat
            production.cur_std_lab_cost = costlab
            production.cur_std_fixed_cost = costfixed
            production.cur_std_direct_cost = costlab + costfixed + costmat - production.cur_std_byproduct_amount
        return True
        
    @api.depends('move_finished_ids.state','bom_id')     
    def calculate_planned_by_product_amount(self):
        byproductamount = 0.0
        for production in self:
            for byproduct_id in production.bom_id.byproduct_ids:
                byproductamount += byproduct_id.product_id.standard_price * byproduct_id.product_qty
            production.cur_std_byproduct_amount = byproductamount
        return True

    @api.depends('move_raw_ids','qty_produced')
    def calculate_material_cost(self):
        matprice = 0.0
        matamount = 0.0
        qty_produced = 1.0
        for production in self:
            for move in production.move_raw_ids:
                matamount += move.product_id.standard_price * move.quantity_done
            if production.product_id  and not production.product_qty == 0.0:
                if production.qty_produced == 0.0:
                    qty_produced = production.product_qty
                else:
                    qty_produced = production.qty_produced
            matprice = matamount / qty_produced
            production.mat_cost = matamount
            production.mat_cost_unit = matprice 
        return True

    @api.depends('move_finished_ids.state','qty_produced')     
    def calculate_actual_by_product_amount(self):
        receiptamount = 0.0
        qty_produced = 1.0
        for production in self:
            if production.bom_id.byproduct_ids:
                moves = production.move_finished_ids.filtered(lambda r: r.state == 'done')
                for move in moves:
                    receiptamount += move.product_id.standard_price * move.quantity_done
                if receiptamount:
                    ######### by product amount compute from all finish cost - standard cost of main product
                    production.by_product_amount = receiptamount - production.prod_std_cost * production.qty_produced
            else:
                production.by_product_amount = 0.0
            if production.product_id  and not production.product_qty == 0.0:
                if production.qty_produced == 0.0:
                    qty_produced = production.product_qty
                else:
                    qty_produced = production.qty_produced
            production.by_product_unit_amount = production.by_product_amount / qty_produced
        return True

    @api.depends('workorder_ids.time_ids', 'qty_produced', 'mat_cost_unit', 'mat_cost', 'by_product_amount')
    def calculate_actual_costs(self):
        labcost = 0.0
        labamount = 0.0
        fixcost = 0.0
        fixedamount = 0.0
        qty_produced = 1.0
        for production in self:
            for workorder in production.workorder_ids:
                labtime = 0.0
                fixedtime = 0.0
                for time in workorder.time_ids:
                    if time.overall_duration:
                        labtime += time.working_duration
                        fixedtime += time.setup_duration + time.teardown_duration
                    else:
                        labtime += time.duration
                labamount += labtime * workorder.workcenter_id.costs_hour / 60
                fixedamount += fixedtime * workorder.workcenter_id.cost_hour_fixed / 60
            if production.product_id and not production.product_qty == 0.0:
                if production.qty_produced == 0.0:
                    qty_produced = production.product_qty
                else:
                    qty_produced = production.qty_produced
            labcost = labamount / qty_produced
            fixcost = fixedamount / qty_produced
        production.lab_cost = labamount 
        production.lab_cost_unit = labcost
        production.fixed_cost = fixedamount
        production.fixed_cost_unit = fixcost
        production.direct_cost = fixedamount + labamount + production.mat_cost - production.by_product_amount
        production.direct_cost_unit = labcost + fixcost + production.mat_cost_unit - production.by_product_unit_amount
        return True
    
    @api.depends('mat_cost_unit','lab_cost_unit','direct_cost_unit')
    def calculate_delta_unit_costs(self):
        for production in self:
            production.delta_mat_cost = - (production.cur_std_mat_cost - production.mat_cost_unit)
            production.delta_lab_cost = - (production.cur_std_lab_cost - production.lab_cost_unit)
            production.delta_fixed_cost = - (production.cur_std_fixed_cost - production.fixed_cost_unit)
            production.delta_direct_cost = - (production.cur_std_direct_cost - production.direct_cost_unit)
            production.delta_byproduct = - (production.cur_std_byproduct_amount - production.by_product_unit_amount)
        return True
