# -*- coding: utf-8 -*-
# Copyright (C) 2020-today ITAAS (Dev K.Book)

from odoo import fields, api, models, _
from bahttext import bahttext
from odoo.exceptions import UserError
from datetime import datetime, date

class AccountActivityType(models.Model):
    _name = 'account.activity.type'
    _rec_name = 'name'

    name = fields.Char('Name', required=True)