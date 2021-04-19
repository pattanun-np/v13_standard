# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import timedelta
import datetime


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    date_planned_start_wo = fields.Datetime(string="Scheduled Start Date", readonly=True)
    date_planned_finished_wo = fields.Datetime(string="Scheduled End Date", readonly=True)
    date_actual_start_wo = fields.Datetime('Start Date', copy=False, readonly=True, compute="get_actual_dates", store=True)
    date_actual_finished_wo = fields.Datetime('End Date', copy=False, readonly=True, compute="get_actual_dates", store=True)


    def schedule_workorders(self):
        max_date_finished = False
        date_start = False
        for production in self:
            production.date_planned_start_wo = False
            production.date_planned_finished_wo = False
            for workorder in production.workorder_ids:
                if not workorder.prev_work_order_id:
                    workorder.date_planned_start_wo = production.date_start_wo or fields.Datetime.now()
                    if workorder.workcenter_id.resource_id:
                        calendar = workorder.workcenter_id.resource_calendar_id
                        workorder.date_planned_start_wo = calendar.plan_hours(0.0, workorder.date_planned_start_wo, True)
                    production.date_planned_start_wo = workorder.date_planned_start_wo
                else:
                    if not workorder.sequence == workorder.prev_work_order_id.sequence:
                        workorder.date_planned_start_wo = max_date_finished or workorder.prev_work_order_id.date_planned_finished_wo
                    else:
                        workorder.date_planned_start_wo = workorder.prev_work_order_id.date_planned_start_wo
                workorder.forwards_scheduling()
                if workorder.prev_work_order_id:
                    max_date_finished = max(workorder.date_planned_finished_wo, workorder.prev_work_order_id.date_planned_finished_wo)
                else:
                    max_date_finished = workorder.date_planned_finished_wo
            production.date_planned_finished_wo = max_date_finished
        return True

    def button_plan(self):
        res = super().button_plan()
        for production in self:
            production.schedule_workorders()
            for workorder in production.workorder_ids:
                date_planned = workorder.date_planned_start_wo or production.date_planned_start_wo or fields.Datetime.now()
                id_created= self.env['mrp.workcenter.capacity'].create({
                    'workcenter_id': workorder.workcenter_id.id,
                    'workorder_id': workorder.id,
                    'product_id': production.product_id.id,
                    'product_qty': production.product_qty,
                    'product_uom_id': production.product_uom_id.id,
                    'date_planned': date_planned,
                    'active': True,
                    'wc_available_capacity': workorder.workcenter_id.wc_capacity,
                    'wo_capacity_requirements': workorder.wo_capacity_requirements,
                })
        return res

    def button_reschedule_workorders(self):
        for production in self:
            production.schedule_workorders()
            for workorder in production.workorder_ids:
                wo_capacity_id = self.env['mrp.workcenter.capacity'].search([('workorder_id', '=', workorder.id)], limit=1)
                if wo_capacity_id:
                    wo_capacity_id.date_planned = workorder.date_planned_finished_wo
        return True

    @api.depends('state')
    def get_actual_dates(self):
        for record in self:
            record.date_actual_start_wo = False
            record.date_actual_finished_wo = False
            first_wo_id = []
            last_wo_id = []
            if record.state == "done" and record.workorder_ids:
                workorders = self.env['mrp.workorder'].search([('production_id', '=', record.id),('state', '=', 'done')])
                time_records = self.env['mrp.workcenter.productivity'].search([('workorder_id', 'in', workorders.ids)])
                if time_records:
                    record.date_actual_start_wo = time_records.sorted('date_start')[0].date_start
                    record.date_actual_finished_wo = time_records.sorted('date_end')[-1].date_end
        return True

    @api.depends('move_raw_ids.state', 'move_finished_ids.state', 'workorder_ids', 'workorder_ids.state', 'qty_produced', 'move_raw_ids.quantity_done', 'product_qty')
    def _compute_state(self):
        super()._compute_state()
        for production in self:
            # stato per ordine parzialmente confermato e consumi effettuati
            if all(move.state in ['cancel', 'done'] for move in production.move_raw_ids) and production.product_qty > production.qty_produced and production.qty_produced > 0.0:
                production.state = 'progress'
            # stato reservation per movimenti di consumo effettuati
            if all(move.state in ['cancel', 'done'] for move in production.move_raw_ids):
                production.reservation_state = 'assigned'
            # stato per ordine pienamente confermato e consumi pending
            if any(move.state not in ['cancel', 'done'] for move in production.move_raw_ids) and production.qty_produced >= production.product_qty:
                production.state = 'progress'

    def _action_cancel(self):
        res = super()._action_cancel()
        for production in self:
            wo_capacity_ids = self.env['mrp.workcenter.capacity'].search([('workorder_id', 'in', production.workorder_ids.ids)])
            for wo_capacity_id in wo_capacity_ids:
                wo_capacity_id.active = False
            if production.product_qty > production.qty_produced:
                production.product_qty = production.qty_produced
        return res

    def action_closing(self):
        if self.post_visible:
            self.post_inventory()
        self._action_cancel()
        return True
