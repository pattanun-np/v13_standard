# -*- coding: utf-8 -*-


from odoo import models, fields, api, _
from odoo.exceptions import UserError
import datetime


class MrpConfirmation(models.TransientModel):
    _name = 'mrp.confirmation'
    _description = "MRP Confirmation"

    date_start = fields.Datetime(_('Start Date'), required=True)
    date_end = fields.Datetime(_('End Date'), compute='_compute_date_end')
    setup_duration = fields.Float(_('Setup Duration'))
    teardown_duration = fields.Float(_('Teardown Duration'))
    working_duration = fields.Float(_('Working Duration'), required=True)
    overall_duration = fields.Float(_('Overall Duration'), compute='_compute_duration')
    production_id = fields.Many2one('mrp.production', string=_('Production Order'), domain=[('routing_id', '!=', False),('state', 'in', ['planned', 'progress'])])
    product_id = fields.Many2one('product.product', _('Product'), related='production_id.product_id', readonly=True, store=True)
    tracking = fields.Selection(related='product_id.tracking', string=_('Product with Tracking'))
    final_lot_id = fields.Many2one('stock.production.lot', string=_("Lot/Serial Number"))
    workorder_id = fields.Many2one('mrp.workorder', string=_("Workorder"), domain="[('state', 'not in', ['done', 'cancel']), ('production_id','=',production_id)]")
    qty_production = fields.Float(_('Production Order Qty'), readonly=True, related ='production_id.product_qty')
    qty_output_prev_wo = fields.Float(_('Previous WO Produced Qty'), readonly=True, related ='workorder_id.qty_output_prev_wo')
    qty_produced = fields.Float(_('Produced Qty'), readonly=True, related='workorder_id.qty_produced')
    qty_producing = fields.Float(_('Quantity'), digits='Product Unit of Measure')
    product_uom_id = fields.Many2one('uom.uom', string=_('Unit of Measure'), related='production_id.product_uom_id', readonly=True)
    move_line_ids = fields.One2many('mrp.component.consumption', 'confirmation_id', string=_('Consumption Stock Moves'))
    byproducts_move_line_ids = fields.One2many('mrp.byproducts.confirmation', 'confirmation_id', string=_('By Products Stock Moves'))
    workorder_ids = fields.Many2many('mrp.workorder', string=_("Workorders"), readonly=True)
    user_id = fields.Many2one('res.users', string=_('User'), required=True, default=lambda self: self.env.user, check_company=True)
    company_id = fields.Many2one('res.company', _('Company'), required=True, default=lambda self: self.env.company.id)
    milestone = fields.Boolean(_('Milestone'), related='workorder_id.milestone')
    move_lines = fields.Boolean(_('move lines indicator'), compute='_compute_move_lines', store=True)
    byproducts_move_lines = fields.Boolean(_('byproducts move lines indicator'), compute='_compute_byproducts_move_lines', store=True)

    @api.depends('workorder_id')
    def _compute_move_lines(self):
        self.move_lines = False
        if self.workorder_id.raw_workorder_line_ids:
            self.move_lines = True
        return True

    @api.depends('workorder_id')
    def _compute_byproducts_move_lines(self):
        self.byproducts_move_lines = False
        if self.workorder_id.finished_workorder_line_ids:
            self.byproducts_move_lines = True
        return True

    @api.depends('overall_duration', 'date_start')
    def _compute_date_end(self):
        for record in self:
            record.date_end = False
            conf_duration = 0.0
            if record.overall_duration:
                conf_duration = datetime.timedelta(minutes=record.overall_duration)
                record.date_end = record.date_start + conf_duration
                if record.workorder_id.workcenter_id.resource_id:
                    calendar = record.workorder_id.workcenter_id.resource_calendar_id
                    conf_duration = record.overall_duration / 60
                    record.date_end = calendar.plan_hours(conf_duration, record.date_start, True)
        return True

    @api.depends('setup_duration', 'teardown_duration', 'working_duration')
    def _compute_duration(self):
        for record in self:
            record.overall_duration = 0.0
            record.overall_duration = record.setup_duration + record.teardown_duration + record.working_duration
        return True

    @api.onchange('production_id')
    def onchange_production_id(self):
        workorder_domain = [('state', 'not in', ['done', 'cancel'])]
        if self.production_id:
            workorder_domain += [('production_id', '=', self.production_id.id)]
        workorder_ids = self.env['mrp.workorder'].search(workorder_domain)
        if workorder_ids:
            if self.workorder_id and self.workorder_id.id not in workorder_ids.ids:
                self.workorder_id = False
        self.workorder_ids = workorder_ids
        return {'domain': {'workorder_id': [('id', 'in', workorder_ids.ids)]}}

    @api.onchange('workorder_id')
    def onchange_workorder_id(self):
        if self.workorder_id.prev_work_order_id.date_actual_finished_wo:
            self.date_start = self.workorder_id.prev_work_order_id.date_actual_finished_wo
        else:
            self.date_start = self.workorder_id.date_planned_start_wo or self.production_id.date_start_wo or fields.Datetime.now()
        if self.workorder_id.operation_id.milestone:
            self.qty_producing = self.qty_production - self.qty_produced
        else:
            self.qty_producing = self.qty_output_prev_wo - self.qty_produced

    @api.onchange('workorder_id', 'qty_producing')
    def onchange_workorder_id_qty_producing(self):
        self.working_duration = self.workorder_id.operation_id.time_cycle * self.qty_producing or 0.0
        self.setup_duration = self.workorder_id.workcenter_id.time_start or 0.0
        self.teardown_duration = self.workorder_id.workcenter_id.time_stop or 0.0

    def do_confirm(self):
        if not self.qty_producing == self.qty_production and not self.workorder_id.workcenter_id.partial_confirmation:
            raise UserError(_('partial confirmation is not allowed'))
        if (self.qty_producing + self.qty_produced) > self.qty_production:
            raise UserError( _('It is not possible to produce more than production order quantity'))
        if (self.qty_producing + self.qty_produced) > self.qty_output_prev_wo and not self.workorder_id.operation_id.milestone:
            raise UserError(_('It is not possible to produce more than %s') % self.qty_output_prev_wo)
        if self.workorder_id.operation_id.milestone:
            workorders = self.production_id.	workorder_ids
            sequence_milestone = self.workorder_id.operation_id.sequence
            prev_workorders = [x for x in workorders if x.	operation_id.sequence < sequence_milestone]
            if any(prev_workorder.state == 'progress' for prev_workorder in prev_workorders):
                    raise UserError(_('previous workorders in progress'))
            for prev_workorder in prev_workorders:
                if prev_workorder.state in ('ready','pending'):
                    prev_workorder.state = 'cancel'
        self.workorder_id.finished_lot_id = self.final_lot_id
        self.workorder_id.qty_producing = self.qty_producing
        if self.workorder_id.state in ['ready', 'pending', 'progress']:
            self.workorder_id.button_start()
        time_id = self.env['mrp.workcenter.productivity'].search([('workorder_id','=',self.workorder_id.id),('date_end','=',False)], limit=1)
        if time_id:
            time_values = {'overall_duration': self.overall_duration,
                        'setup_duration': self.setup_duration,
                        'teardown_duration': self.teardown_duration,
                        'working_duration': self.working_duration,
                        'date_start': self.date_start,
                        'date_end': self.date_end,
                        'user_id': self.user_id.id,
                        }
            time_id.write(time_values)
        for move in self.move_line_ids:
            stock_move_line_id = self.env['mrp.workorder.line'].search([('raw_workorder_id', '=', self.workorder_id.id),('product_id', '=', move.product_id.id)], limit=1)
            if stock_move_line_id:
                move_line_values = {'lot_id': move.lot_id.id,
                            'qty_done': move.qty_done,
                            }
                stock_move_line_id.write(move_line_values)
        for move in self.byproducts_move_line_ids:
            stock_move_line_id = self.env['mrp.workorder.line'].search([('finished_workorder_id', '=', self.workorder_id.id),('product_id', '=', move.product_id.id)], limit=1)
            if stock_move_line_id:
                move_line_values = {'lot_id': move.lot_id.id,
                            'qty_done': move.qty_done,
                            }
                stock_move_line_id.write(move_line_values)
        self.workorder_id.record_production()
        return True

    @api.model
    def default_get(self, fields):
        default = super().default_get(fields)
        active_id = self.env.context.get('active_id', False)
        if active_id:
            default['production_id'] = active_id
        return default

    def populate_components(self):
        for record in self:
            if record.move_line_ids:
                record.move_line_ids.unlink()
            if record.byproducts_move_line_ids:
                record.byproducts_move_line_ids.unlink()
            if record.workorder_id:
                if record.qty_producing == 0.0:
                    raise UserError(_('set quantity to be confirmed'))
                else:
                    record.workorder_id.qty_producing = record.qty_producing
                    record.workorder_id._apply_update_workorder_lines()
                for move in record.workorder_id.raw_workorder_line_ids:
                    id_created= self.env['mrp.component.consumption'].create({
                        'confirmation_id' : record.id,
                        'workorder_id' : record.workorder_id.id,
                        'product_id' : move.product_id.id,
                        'lot_id' : move.lot_id.id,
                        'qty_done' : move.qty_to_consume,
                    })
                finished_product_move_line = self.env['mrp.workorder.line'].search([('finished_workorder_id', '=', self.workorder_id.id),('product_id', '=', self.product_id.id)], limit=1)
                byproducts_stock_moves = record.workorder_id.finished_workorder_line_ids - finished_product_move_line
                for move in byproducts_stock_moves:
                    id_created= self.env['mrp.byproducts.confirmation'].create({
                        'confirmation_id' : record.id,
                        'workorder_id' : record.workorder_id.id,
                        'product_id' : move.product_id.id,
                        'lot_id' : move.lot_id.id,
                        'qty_done' : move.qty_to_consume,
                    })
        return self._reopen_form()

    def _reopen_form(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new'
        }

    def action_generate_serial(self):
        self.ensure_one()
        product_produce_wiz = self.env.ref('mrp.view_mrp_product_produce_wizard', False)
        self.final_lot_id = self.env['stock.production.lot'].create({
            'product_id': self.product_id.id,
            'company_id': self.production_id.company_id.id
        })
        return self._reopen_form()

class MRPComponentConsumption(models.TransientModel):
    _name = 'mrp.component.consumption'
    _description = "MRP Component Consumption"

    confirmation_id = fields.Many2one('mrp.confirmation', string=_('Confirmation Reference'), index=True, required=True, ondelete='cascade')
    workorder_id = fields.Many2one('mrp.workorder', string=_("Workorder"), related='confirmation_id.workorder_id', store=True)
    product_id = fields.Many2one('product.product', _('Product'))
    tracking = fields.Selection(related='product_id.tracking', string=_('Product with Tracking'))
    lot_id = fields.Many2one('stock.production.lot', string=_('Lot/Serial Number'))
    qty_done = fields.Float(_('Consumed Quantity'), default=0.0, digits='Product Unit of Measure')
    product_uom_id = fields.Many2one('uom.uom', _('Unit of Measure'), related='product_id.uom_id')
    company_id = fields.Many2one('res.company', _('Company'), required=True, default=lambda self: self.env.company.id)


class MRPByProductsConfirmation(models.TransientModel):
    _name = 'mrp.byproducts.confirmation'
    _description = "MRP By Products Confirmation"

    confirmation_id = fields.Many2one('mrp.confirmation', string=_('Confirmation Reference'), index=True, required=True, ondelete='cascade')
    workorder_id = fields.Many2one('mrp.workorder', string=_("Workorder"), related='confirmation_id.workorder_id', store=True)
    product_id = fields.Many2one('product.product', _('Product'))
    tracking = fields.Selection(related='product_id.tracking', string=_('Product with Tracking'))
    lot_id = fields.Many2one('stock.production.lot', string=_('Lot/Serial Number'))
    qty_done = fields.Float(_('Confirmed Quantity'), default=0.0, digits='Product Unit of Measure')
    product_uom_id = fields.Many2one('uom.uom', _('Unit of Measure'), related='product_id.uom_id')
    company_id = fields.Many2one('res.company', _('Company'), required=True, default=lambda self: self.env.company.id)