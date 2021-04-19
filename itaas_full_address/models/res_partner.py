# -*- coding: utf-8 -*-
from openerp import fields, api, models, _
from bahttext import bahttext
from openerp.exceptions import UserError
from datetime import datetime, date

class res_partner(models.Model):
    _inherit ="res.partner"

    def get_partner_full_address_text(self):
        address = self.get_partner_full_address()
        address_text = ' '.join(address)
        return address_text

    def get_partner_full_address(self):
        address = []
        # use in qweb partner_address = o.partner_id.get_partner_full_address()
        # <t t-set="partner_address" t-value="o.partner_id.get_partner_full_address()"/>
        # <span t-esc="' '.join([ address for address in partner_address ])"/>
        if self.country_id.code == 'TH':
            if self.street:
                address.append(str(self.street))
            if self.street2:
                address.append(str(self.street2))

            if self.state_id and self.state_id.code == 'BKK':
                if self.sub_district_id:
                    address.append('แขวง' + str(self.sub_district_id.name))
                if self.district_id:
                    address.append('เขต' + str(self.district_id.name))
                elif self.city:
                    address.append('เขต' + str(self.city))

                address.append(str(self.state_id.name))

            elif self.state_id:
                if self.sub_district_id:
                    address.append('ตำบล' + str(self.sub_district_id.name))

                if self.district_id:
                    address.append('อำเภอ' + str(self.district_id.name))
                elif self.city:
                    address.append('อำเภอ' + str(self.city))

                address.append('จังหวัด' + str(self.state_id.name))
        else:

            if self.street:
                address.append(str(self.street))
            if self.street2:
                address.append(str(self.street2))
            if self.city:
                address.append(str(self.city))
            if self.state_id:
                address.append(str(self.state_id.name))

        if self.zip:
            address.append(str(self.zip))

        return address