# -*- coding: utf-8 -*-
# Copyright (C) 2016-Today (ITAAS)

from odoo import api, fields, models, _

class ResCompany(models.Model):
    _inherit = 'res.company'
    
    branch_no = fields.Char(string='Branch',default='00000')
    eng_address = fields.Char(string='English Address')

    #only some customer for detail of address
    building = fields.Char(string='building', size=64)
    roomnumber = fields.Char(string='roomnumber', size=32)
    floornumber = fields.Char(string='floornumber', size=32)
    village = fields.Char(string='village', size=64)
    house_number = fields.Char(string='house_number', size=20)
    moo_number = fields.Char(string='moo_number', size=20)
    soi_number = fields.Char(string='soi_number', size=24)
    tumbon = fields.Char(string='tumbon', size=24)




    ####################additional field #################
    invoice_step = fields.Selection([('1step','Invoice/Tax Invoice'),('2step','Invoice--->Tax Invoice')],default='1step',help='1step is invoice and tax invoice is the same, 2 step is invoice and tax invoice is difference number')

    # disable_excel_tax_report = fields.Boolean(string="Disable Tax Report in Excel Format",default=False)
    # authorized_amount = fields.Float(string="Sale Authorize Amount",default=1000000.00)
    # readonly_date_invoice = fields.Boolean(string='Read only date invoice')
    # allow_invoice_backward = fields.Boolean(string='Allow Record Invoice Backward')
    # auto_product_code = fields.Boolean(string='Auto Generate Product Code')
    # auto_customer_code = fields.Boolean(string='Auto Generate Customer Code')
    # auto_supplier_code = fields.Boolean(string='Auto Generate Supplier Code')
    # auto_employee_code = fields.Boolean(string='Auto Generate Employee Code')
    # auto_product_barcode = fields.Boolean(string='Auto Generate Product Barcode')
    # tax_id_require = fields.Boolean(string='Require Tax ID')
    # branch_require = fields.Boolean(string='Require Branch')
    # allow_cancel = fields.Boolean(string='Allow Cancel')
    # show_head_office = fields.Boolean(string='Show Head Office')
    # show_total_tax_report = fields.Boolean(string='Show Total in Tax')
    # is_head_office = fields.Boolean(string='HO', default=True)
    # discount_amount_condition = fields.Selection([
    #     ('unit', 'Per Unit'),
    #     ('total', 'Per Total')
    # ], default='total', string="Discount Amount Condition")


    # is_sale_vat = fields.Boolean(string="เก็บภาษีขาย",default=True)
    # sale_condition = fields.Text(string="เงื่อนไขการรับประกันสินค้า", translate=True)
    # payment_info = fields.Text(string="รายละเอียดการชำระเงิน", translate=True)


    def get_company_full_address(self):
        address = ''

        if self.building:
            address = address + ' อาคาร' + str((self.building).encode('utf-8'))
        if self.roomnumber:
            address = address + ' ห้องเลขที่' + str((self.roomnumber).encode('utf-8'))
        if self.floornumber:
            address = address + ' ชั้นที่' + str((self.floornumber).encode('utf-8'))
        if self.village:
            address = address + ' หมู่บ้าน' + str((self.village).encode('utf-8'))
        if self.house_number:
            address = address + ' เลขที่' + str((self.house_number).encode('utf-8'))
        if self.moo_number:
            address = address + ' หมู่ที่' + str((self.moo_number).encode('utf-8'))
        if self.tumbon:
            address = address + ' ตำบล ' + str((self.tumbon).encode('utf-8'))
        if self.soi_number:
            address = address + ' ซอย' + str((self.soi_number).encode('utf-8'))
        if self.street:
            address = address + ' ถนน' + str((self.street).encode('utf-8'))
        if self.city and self.state_id and self.state_id.code != 'BKK':
            address = address + ' อำเภอ' + str((self.city).encode('utf-8'))
        if self.city and self.state_id and self.state_id.code == 'BKK':
            address = address + ' เขต' + str((self.city).encode('utf-8'))
        if self.state_id:
            address = address + ' จังหวัด' + str((self.state_id.name).encode('utf-8'))

        return address



