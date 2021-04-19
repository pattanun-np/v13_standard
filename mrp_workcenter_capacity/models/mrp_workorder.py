# -*- coding: utf-8 -*-


from odoo import models, fields, api, _


class MrpWorkOrder(models.Model):
    _inherit = 'mrp.workorder'

    wc_available_capacity = fields.Float(_('WC Weekly Available Capacity'), related='workcenter_id.wc_capacity', store='True', group_operator="avg")
    wo_capacity_requirements = fields.Float(_('WO Capacity Requirements'), compute='_wo_capacity_requirement', store='True')


    @api.depends('duration_expected')
    def _wo_capacity_requirement(self):
        for workorder in self:
            workorder.wo_capacity_requirements = (workorder.duration_expected) / 60
        return True
