# -*- coding: utf-8 -*-


from odoo import models, fields, api, _



class MrpWorkCenterCapacity(models.Model):
    _name = "mrp.workcenter.capacity"
    _description = "Work Center Capacity"
    _order = "date_planned DESC"


    workcenter_id = fields.Many2one('mrp.workcenter', string=_('Work Center'))
    workorder_id = fields.Many2one('mrp.workorder', string=('WorkOrder'))
    product_id = fields.Many2one("product.product", string=_("Product"))
    product_qty = fields.Float(_("Required Quantity"))
    product_uom_id = fields.Many2one('uom.uom', string=_('Unit of Measure'))
    date_planned = fields.Datetime(_('Planned Date'))
    active = fields.Boolean(default=True)
    wc_available_capacity = fields.Float(_('WC Weekly Available Capacity'), group_operator="avg")
    wo_capacity_requirements = fields.Float(_('WO Capacity Requirements'))
    wc_capacity_load = fields.Float(_('WC Capacity Load %'), compute='_wc_capacity', store='True')
    wc_remaining_capacity = fields.Float(_('WC Remaining Capacity'), compute='_wc_capacity', store='True')


    @api.depends('wo_capacity_requirements','wc_available_capacity')
    def _wc_capacity(self):
        for record in self:
            if record.wc_available_capacity:
                record.wc_capacity_load = (record.wo_capacity_requirements / record.wc_available_capacity) * 100
            else:
                record.wc_capacity_load = 0.0
            record.wc_remaining_capacity = record.wc_available_capacity - record.wo_capacity_requirements
        return True


