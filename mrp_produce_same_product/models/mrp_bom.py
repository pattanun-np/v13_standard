# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_round, float_compare

from itertools import groupby

class MrpBom(models.Model):
    _inherit = 'mrp.bom'

    @api.constrains('product_id', 'product_tmpl_id', 'bom_line_ids')
    def _check_bom_lines(self):
        print ('--New Constrain')
        for bom in self:
            for bom_line in bom.bom_line_ids:
                # if bom.product_id:
                #     same_product = bom.product_id == bom_line.product_id
                # else:
                #     same_product = bom.product_tmpl_id == bom_line.product_id.product_tmpl_id

                # if same_product:
                #     raise ValidationError(_("BoM line product %s should not be the same as BoM product.") % bom.display_name)

                if bom.product_id and bom_line.bom_product_template_attribute_value_ids:
                    raise ValidationError(
                        _("BoM cannot concern product %s and have a line with attributes (%s) at the same time.")
                        % (bom.product_id.display_name, ", ".join(
                            [ptav.display_name for ptav in bom_line.bom_product_template_attribute_value_ids])))
                for ptav in bom_line.bom_product_template_attribute_value_ids:
                    if ptav.product_tmpl_id != bom.product_tmpl_id:
                        raise ValidationError(
                            _("The attribute value %s set on product %s does not match the BoM product %s.") %
                            (ptav.display_name, ptav.product_tmpl_id.display_name,
                             bom_line.parent_product_tmpl_id.display_name)
                        )

