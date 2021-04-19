# -*- coding: utf-8 -*-


from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import timedelta
from datetime import datetime


class MrpWorkorder(models.Model):
    _inherit = 'mrp.workorder'

    qty_output_prev_wo = fields.Float(_('Previous WO Produced Quantity'), digits='Product Unit of Measure', compute="_compute_prev_work_order")
    prev_work_order_id = fields.Many2one('mrp.workorder', _('Previous Work Order'), compute="_compute_prev_work_order")
    date_actual_start_wo = fields.Datetime(_('Actual Start Date'), compute='_compute_dates_actual', store=True)
    date_actual_finished_wo = fields.Datetime(_('Actual Finished Date'), compute='_compute_dates_actual', store=True)
    milestone = fields.Boolean(_('Milestone'), related='operation_id.milestone')
    date_planned_start = fields.Datetime(_('Planned Start Date'))
    date_planned_start_wo = fields.Datetime(_('Scheduled Start Date'), readonly=True, states={'ready': [('readonly', False)],'pending': [('readonly', False)]})
    date_planned_finished_wo = fields.Datetime(_('Scheduled Finished Date'), readonly=True, states={'ready': [('readonly', False)],'pending': [('readonly', False)]})
    duration_expected = fields.Float(readonly=True, states={'ready': [('readonly', False)],'pending': [('readonly', False)]})
    sequence = fields.Integer('Sequence', related='operation_id.sequence', store=True)
    hours_uom = fields.Many2one('uom.uom', _('Hours'), compute="_get_uom_hours")


    def _get_uom_hours(self):
        uom = self.env.ref('uom.product_uom_hour', raise_if_not_found=False)
        for record in self:
            if uom:
                record.hours_uom = uom.id
        return True

    @api.depends('state')
    def _compute_prev_work_order(self):
        for workorder in self:
            prev_work_order = self.search([('next_work_order_id', '=', workorder.id)], limit=1)
            workorder.prev_work_order_id = prev_work_order
            product_qty = workorder.production_id.product_qty
            if prev_work_order:
                workorder.qty_output_prev_wo = prev_work_order.qty_produced
            else:
                workorder.qty_output_prev_wo = product_qty
        return True

    def button_start(self):
        if  self.production_availability != 'assigned' and not self.workcenter_id.start_without_stock:
            raise UserError(_('It is not possible to start workorder without material availability'))
        if not self.qty_producing == self.qty_production and not self.workcenter_id.partial_confirmation:
            raise UserError(_('partial confirmation is not allowed'))
        if (self.qty_producing + self.qty_produced) > self.qty_production:
            raise UserError( _('It is not possible to produce more than production order quantity'))
        if (self.qty_producing + self.qty_produced) > self.qty_output_prev_wo and not self.operation_id.milestone:
            raise UserError(_('It is not possible to produce more than %s') % self.qty_output_prev_wo)
        super().button_start()
        return True

    @api.depends('time_ids','state')
    def _compute_dates_actual(self):
        date_start = False
        date_end = False
        for workorder in self:
            if workorder.state == 'done' and workorder.time_ids:
                date_start =  workorder.time_ids.sorted('date_start')[0].date_start
                date_end = workorder.time_ids.sorted('date_end')[-1].date_end
            workorder.date_actual_start_wo = date_start
            workorder.date_actual_finished_wo = date_end
        return True

    def record_production(self):
        super().record_production()
        for workorder in self:
            wo_capacity_id = self.env['mrp.workcenter.capacity'].search([('workorder_id', '=', workorder.id)],limit=1)
            if wo_capacity_id:
                wo_capacity_id.active = False
                wo_capacity_id.wo_capacity_requirements = 0.0
            if workorder.operation_id.milestone:
                workorders = workorder.production_id.	workorder_ids
                sequence_milestone = workorder.operation_id.sequence
                prev_workorders = [x for x in workorders if x.operation_id.sequence < sequence_milestone]
                if any(prev_workorder.state == 'progress' for prev_workorder in prev_workorders):
                    raise UserError(_('previous workorders in progress'))
                for prev_workorder in prev_workorders:
                    if prev_workorder.state in ('ready','pending'):
                        prev_workorder.state = 'cancel'
                    wo_capacity_id = self.env['mrp.workcenter.capacity'].search([('workorder_id', '=', prev_workorder.id)],limit=1)
                    if wo_capacity_id:
                        wo_capacity_id.active = False
        return True

    def write(self, vals):
        res = super().write(vals)
        for workorder in self:
            wo_capacity_id = self.env['mrp.workcenter.capacity'].search([('workorder_id', '=', workorder.id)],limit=1)
            if wo_capacity_id:
                date_planned = workorder.date_planned_start_wo or workorder.production_id.date_planned_start_wo or fields.Datetime.now()
                wo_capacity_id.date_planned = date_planned
        return res

    def backwards_scheduling(self):
        for workorder in self:
            time_delta = workorder.duration_expected
            workorder.date_planned_start_wo = workorder.date_planned_finished_wo - timedelta(minutes=time_delta)
            if workorder.workcenter_id.resource_id:
                calendar = workorder.workcenter_id.resource_calendar_id
                duration_expected = - workorder.duration_expected / 60
                workorder.date_planned_start_wo = calendar.plan_hours(duration_expected, workorder.date_planned_finished_wo, True)

    def forwards_scheduling(self):
        for workorder in self:
            time_delta = workorder.duration_expected
            workorder.date_planned_finished_wo = workorder.date_planned_start_wo + timedelta(minutes=time_delta)
            if workorder.workcenter_id.resource_id:
                calendar = workorder.workcenter_id.resource_calendar_id
                duration_expected = workorder.duration_expected / 60
                workorder.date_planned_finished_wo = calendar.plan_hours(duration_expected, workorder.date_planned_start_wo, True)