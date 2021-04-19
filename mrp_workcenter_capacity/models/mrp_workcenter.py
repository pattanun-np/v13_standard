# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class MrpWorkCenter(models.Model):
    _inherit = 'mrp.workcenter'

    nr_days = fields.Float(_('working days per week'), required="True")
    nr_hours = fields.Float(_('working hours per shift'), required="True")
    nr_shift = fields.Integer(_('shifts per day'), required="True")
    wc_capacity = fields.Float(_('WC Weekly Available Capacity'), compute='_calculate_wc_capacity', store='True', group_operator='avg')
    hours_uom = fields.Many2one('uom.uom', _('Hours'), compute="_get_uom_hours")


    def _get_uom_hours(self):
        uom = self.env.ref('uom.product_uom_hour', raise_if_not_found=False)
        for record in self:
            if uom:
                record.hours_uom = uom.id
        return True


    @api.depends('nr_days','nr_hours','nr_shift','capacity','time_efficiency')
    def _calculate_wc_capacity(self):
        cap = 0.0
        for wc in self:
            cap = wc.nr_shift * wc.nr_hours * wc.nr_days * wc.capacity * wc.time_efficiency / 100
            wc.wc_capacity = cap
        return True
