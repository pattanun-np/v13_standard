# -*- coding: utf-8 -*-
from odoo import fields, api, models, _

class res_company(models.Model):
    _inherit ="res.company"

    street = fields.Char(compute=False, inverse=False)
    street2 = fields.Char(compute=False, inverse=False)
    zip = fields.Char(compute=False, inverse=False)
    city = fields.Char(compute=False, inverse=False)
    state_id = fields.Many2one('res.country.state', string="Fed. State",compute=False, inverse=False)
    country_id = fields.Many2one('res.country', string="Country",compute=False, inverse=False)

    def get_company_full_address_text(self):
        address = self.get_company_full_address()
        address_text = ' '.join(address)
        return address_text

    def get_company_full_address(self):
        address = []
        # use in qweb company_address = o.company_id.get_company_full_address()
        # <t t-set="company_address" t-value="o.company_id.get_company_full_address()"/>
        # <span t-esc="' '.join([ address for address in company_address ])"/>
        if self.country_id.code == 'TH':
            if self.house_number:
                address.append('เลขที่' + str(self.house_number))
            if self.building:
                address.append('อาคาร' + str(self.building))
            if self.roomnumber:
                address.append('ห้องเลขที่' + str(self.roomnumber))
            if self.floornumber:
                address.append('ชั้นที่' + str(self.floornumber))
            if self.village:
                address.append('หมู่บ้าน' + str(self.village))
            if self.moo_number:
                address.append('หมู่ที่'  + str(self.moo_number))
            if self.soi_number:
                address.append('ซอย' + str(self.soi_number))
            if self.street:
                address.append('ถนน' + str(self.street))
            if self.street2:
                address.append(str(self.street2))

            if self.state_id and self.state_id.code == 'BKK':
                if self.tumbon:
                    address.append('แขวง' + str(self.tumbon))
                if self.city:
                    address.append('เขต' + str(self.city))

                address.append(str(self.state_id.name))
            else:
                if self.tumbon:
                    address.append('ตำบล' + str(self.tumbon))
                if self.city:
                    address.append('อำเภอ' + str(self.city))
                address.append('จังหวัด' + str(self.state_id.name))
        else:
            if self.building:
                address.append(str(self.building))
            if self.roomnumber:
                address.append(str(self.roomnumber))
            if self.floornumber:
                address.append(str(self.floornumber))
            if self.village:
                address.append(str(self.village))
            if self.house_number:
                address.append(str(self.house_number))
            if self.moo_number:
                address.append(str(self.moo_number))
            if self.soi_number:
                address.append(str(self.soi_number))
            if self.street:
                address.append(str(self.street))
            if self.street2:
                address.append(str(self.street2))
            if self.tumbon:
                address.append(str(self.tumbon))
            if self.city:
                address.append(str(self.city))
            if self.state_id:
                address.append(str(self.state_id.name))

        if self.zip:
            address.append(str(self.zip))

        return address


