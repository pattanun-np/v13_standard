# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
# import datetime
from datetime import datetime
from datetime import date
from odoo.exceptions import UserError


class mrpworkcenterproductivity(models.Model):
    _inherit = 'mrp.workcenter.productivity'

    state = fields.Selection([('new','New'),('done','Done')],default='new')
    # max_fg_qty = fields.Integer(string='Max FG Qty')

# class stock

class MrpWorkorder(models.Model):
    _inherit = 'mrp.workorder'

    qty_post = fields.Integer(string='Posted Quantity')
    value_post = fields.Float(string='Value Posted')
    # is_allow_continue
    rework_qty = fields.Integer(string='Rework QTY')
    done_rework_qty = fields.Integer(string='Done Rework QTY')
    is_rework = fields.Boolean(string='Is Rework',default=False)


    def button_rework_start(self):
        self.ensure_one()

        # Need a loss in case of the real time exceeding the expected
        # timeline = self.env['mrp.workcenter.productivity']
        # if self.duration < self.duration_expected:
        #     loss_id = self.env['mrp.workcenter.productivity.loss'].search([('loss_type', '=', 'productive')],
        #                                                                   limit=1)
        #     if not len(loss_id):
        #         raise UserError(_(
        #             "You need to define at least one productivity loss in the category 'Productivity'. Create one from the Manufacturing app, menu: Configuration / Productivity Losses."))
        # else:
        #     loss_id = self.env['mrp.workcenter.productivity.loss'].search([('loss_type', '=', 'performance')],
        #                                                                   limit=1)
        #     if not len(loss_id):
        #         raise UserError(_(
        #             "You need to define at least one productivity loss in the category 'Performance'. Create one from the Manufacturing app, menu: Configuration / Productivity Losses."))


        self.write({'state': 'progress'})
        self.write({'is_rework': True})
        return True




    # super(models.model) to not allow system do other write in any inherit model
    def write(self, values):
        if 'production_id' in values:
            raise UserError(_('You cannot link this work order to another manufacturing order.'))
        if 'workcenter_id' in values:
            for workorder in self:
                if workorder.workcenter_id.id != values['workcenter_id']:
                    if workorder.state in ('progress', 'done', 'cancel'):
                        raise UserError(
                            _('You cannot change the workcenter of a work order that is in progress or done.'))
                    workorder.leave_id.resource_id = self.env['mrp.workcenter'].browse(
                        values['workcenter_id']).resource_id
        # if (list(values.keys()) != ['time_ids'] or list(values.keys()) != ['time_ids']) and any(workorder.state == 'done' for workorder in self):
        #     raise UserError(_('You can not change the finished work order.'))

        if 'date_planned_start' in values or 'date_planned_finished' in values:
            for workorder in self:
                start_date = fields.Datetime.to_datetime(
                    values.get('date_planned_start')) or workorder.date_planned_start
                end_date = fields.Datetime.to_datetime(
                    values.get('date_planned_finished')) or workorder.date_planned_finished
                if start_date and end_date and start_date > end_date:
                    raise UserError(_(
                        'The planned end date of the work order cannot be prior to the planned start date, please correct this to save the work order.'))
                # Update MO dates if the start date of the first WO or the
                # finished date of the last WO is update.
                if workorder == workorder.production_id.workorder_ids[0] and 'date_planned_start' in values:
                    workorder.production_id.with_context(force_date=True).write({
                        'date_planned_start': fields.Datetime.to_datetime(values['date_planned_start'])
                    })
                if workorder == workorder.production_id.workorder_ids[-1] and 'date_planned_finished' in values:
                    workorder.production_id.with_context(force_date=True).write({
                        'date_planned_finished': fields.Datetime.to_datetime(values['date_planned_finished'])
                    })
        return super(models.Model, self).write(values)

    def record_production(self):
        self.end_previous()
        if self.is_rework:
            self.write({'is_rework': False})
            self.write({'done_rework_qty': self.rework_qty})
            self.write({'rework_qty': 0})
            self.write({'state':'done'})
            self.production_id.consume_material_to_wip()
            return True

        super(MrpWorkorder, self).record_production()

        for wo in self:
            if not wo.is_last_unfinished_wo:
                wo.production_id.consume_material_to_wip()
        return True


    # @api.constrains('state')
    # def get_actual_posting(self):
    #     for record in self:
    #         if record.state in [('done'), ('cancel')]:
    #             print ('-111')
    #             record._direct_cost_postings()
    #             print('-222')
    #     return True

    # production direct cost posting
    def _direct_cost_postings(self):
        total_working_duration = 0.0
        total_other_duration = 0.0
        amount = 0.0
        final_date = False
        for record in self:
            # print ('ST1')
            desc_wo = record.production_id.name + '-' + record.workcenter_id.name + '-' + record.name
            last_time = self.env['mrp.workcenter.productivity'].search([('workorder_id', '=', record.id)], order=	"date_end desc", limit=1)
            if last_time:
                # print('ST2')
                final_date = last_time.date_end
                if final_date:
                    final_date = final_date.date()
            else:
                # print('ST3')
                final_date = date.today()

            # print('ST4')
            analytic_account = record.production_id.analytic_account_id.id or record.workcenter_id.analytic_account_id.id
            # print('ST5')
            for time in record.time_ids.filtered(lambda x: x.state !='done'):
                if time.overall_duration:
                    total_working_duration += time.working_duration
                    total_other_duration += time.setup_duration + time.teardown_duration
                else:
                    total_working_duration += time.duration

                time.write({'state': 'done'})

            # print('ST6')

            amount = round(((total_working_duration * record.workcenter_id.costs_hour) + (total_other_duration * record.workcenter_id.cost_hour_fixed))/ 60, 2)
            # print('ST7')
            if amount:
                if record.workcenter_id.wc_type == "H":
                    # print('ST8')
                    # print (record.production_id.company_id)
                    # with_context(force_company=cost.company_id.id)
                    account_id = record.production_id.company_id.labour_cost_account_id

                else:
                    # print('ST9')
                    # print(record.production_id.company_id)
                    account_id = record.production_id.company_id.machine_run_cost_account_id

                # print('ST10')
                # print (account_id)
                id_created_header = self.env['account.move'].create({
                    'journal_id' : record.production_id.company_id.manufacturing_journal_id.id,
                    'date': final_date,
                    'ref' : "Direct Costs",
                    'company_id': record.workcenter_id.company_id.id,
                })
                # print('ST11')
                val_id_credit_item = {
                    'move_id' : id_created_header.id,
                    'account_id': account_id.id,
                    'product_id': record.production_id.product_id.id,
                    'name' : desc_wo,
                    'quantity': record.qty_produced,
                    'product_uom_id': record.production_id.product_uom_id.id,
                    'credit': amount,
                    'debit': 0.0,
                    'manufacture_order_id': record.production_id.id,
                }
                # print (val_id_credit_item)

                id_credit_item = self.env['account.move.line'].with_context(check_move_validity=False).create(val_id_credit_item)

                # print('ST12')
                # print (record.production_id.product_id.property_stock_production)
                # print(record.production_id.product_id.property_stock_production.valuation_in_account_id)

                account_id = record.production_id.product_id.property_stock_production.with_context(force_company=record.production_id.company_id.id).valuation_in_account_id

                if not account_id:
                    account_id = record.production_id.product_id.categ_id.property_stock_account_input_categ_id

                val_id_debit_item = {
                    'move_id' : id_created_header.id,
                    'account_id': account_id.id,
                    'analytic_account_id' : analytic_account,
                    'product_id': record.production_id.product_id.id,
                    'name' : desc_wo,
                    'quantity': record.qty_produced,
                    'product_uom_id': record.production_id.product_uom_id.id,
                    'credit': 0.0,
                    'debit': amount,
                    'manufacture_order_id': record.production_id.id,
                }

                # print(val_id_debit_item)

                id_debit_item= self.env['account.move.line'].with_context(check_move_validity=False).create(val_id_debit_item)

                # print ('--DIRECT ')
                # print (id_credit_item)
                # print(id_debit_item)

                id_created_header.post()
        return True