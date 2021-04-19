#-*- coding: utf-8 -*-


from odoo import api, fields, models, _
from datetime import datetime, date
import dateutil.parser
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT,DEFAULT_SERVER_DATETIME_FORMAT
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_is_zero, float_compare
from datetime import datetime, timedelta


class account_journal(models.Model):
    _inherit = "account.journal"
    _order = 'sequence asc'

    #will use in the future
    adj_journal = fields.Many2one('account.journal', string="Adjust Journal", copy=False)
    bank_cheque = fields.Boolean(string='Cheque', default=False)
    bank_for_cheque_account_id = fields.Many2one('account.account',string='Default Bank Account for Cheque')
    debit_sequence_id = fields.Many2one('ir.sequence',string='Debit Note Sequence')

    #########more sequence for tax_invoice and payment ###########
    tax_invoice_sequence_id = fields.Many2one('ir.sequence', string='Tax Invoice Sequence')
    payment_sequence_id = fields.Many2one('ir.sequence', string='Payment Sequence')



