# -*- coding: utf-8 -*-
# Copyright (C) 2016-2017  ITtaas.
from odoo import api, fields, models, _
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DF
from odoo.exceptions import UserError
from dateutil.relativedelta import relativedelta
from dateutil.rrule import (YEARLY,MONTHLY,WEEKLY,DAILY)
from datetime import datetime, timedelta, date
from pytz import timezone
import pytz
import calendar

import uuid

from datetime import datetime, timedelta


class categorywrite(models.Model):
    _inherit = "product.category"


    #super(models.model) to not allow system do other write in any inherit model
    def write(self, vals):
        return super(models.Model, self).write(vals)













