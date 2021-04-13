# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import time

from odoo import api, fields, models, _
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError
from datetime import datetime, date


class ChequeAdvanceConfirmOrder(models.TransientModel):
    _name = "cheque.advance.confirm.order"
    _description = "Cheque Advance Confirm Order"

    is_single_validate = fields.Boolean(string='Single Validate')
    validate_date = fields.Date(string='Validate Date')
    destination_account_id = fields.Many2one('account.account', string='Destination Account')


    # order_date = fields.Date(string='Order Date')
    def post_cheque_to_bank(self):
        cheque_ids = self.env['account.cheque.statement'].browse(self._context.get('active_ids', []))

        for order in cheque_ids.filtered(lambda x: x.state == 'open'):
            order.action_post
        return {'type': 'ir.actions.act_window_close'}


    def confirm_order(self):
        cheque_ids = self.env['account.cheque.statement'].browse(self._context.get('active_ids', []))

        if self.is_single_validate:
            cheque_ids.action_single_validate(self.validate_date,self.destination_account_id)
        else:
            for order in cheque_ids.filtered(lambda x: x.state in ('open','post')):
                order.action_validate()
        return {'type': 'ir.actions.act_window_close'}



class account_cheque_statement(models.Model):
    _inherit = 'account.cheque.statement'

    def action_single_validate(self,validate_date,destination_account_id):
        # print ("action_validate")
        total_debit = 0
        all_label = ""
        all_ref = ""
        if not validate_date:
            validate_date = date.today()


        all_move_line_vals = []
        for cheque in self:
            if cheque.journal_id:
                journal_id = cheque.journal_id

            move_line_vals = cheque.cheque_move_line_reverse_get()
            for move_line in move_line_vals:
                if not total_debit and move_line['debit']:
                    all_label += move_line['name'] + ','
                    all_ref += move_line['ref'] + ','
                    total_debit += move_line['debit']
                    move_line['account_id'] = destination_account_id.id
                elif total_debit and move_line['debit']:
                    all_label += move_line['name'] + ','
                    all_ref += move_line['ref'] + ','
                    total_debit += move_line['debit']
                    move_line_vals.remove(move_line)

            all_move_line_vals += move_line_vals

        ##########new update####
        # print ('--ALL MOVE')
        # print (all_move_line_vals)
        #####update debit value####
        for move_line in all_move_line_vals:
            if move_line['debit']:
                move_line['debit'] = total_debit
                move_line['name'] = all_label
                move_line['ref'] = all_ref

        move_line_vals = all_move_line_vals

        line = [(0, 0, l) for l in move_line_vals]

        new_name = ""

        # journal_id = self.env['account.journal'].search([('code','=','MISC')],limit=1)
        if journal_id:
            journal_id = journal_id.adj_journal
        else:
            raise UserError(_("Please check journal to record reverse check transaction"))


        if journal_id.sequence_id:
            # If invoice is actually refund and journal has a refund_sequence then use that one or use the regular one
            sequence_id = journal_id.sequence_id
            new_name = sequence_id.with_context(ir_sequence_date=validate_date).next_by_id()
            # print "new_new"
            # print new_name
        else:
            raise UserError(_('Please check sequence of your journal'))

        if move_line_vals:
            move_vals = {
                'line_ids': line,
                'journal_id': journal_id.id,
                'date': validate_date,
                'name': new_name,
                'ref': all_ref,
            }
            account_move = self.env['account.move']
            # print "move vals"
            # print move_vals
            move_id = account_move.create(move_vals)
            move_id.post()
            self.write({'move_new_id': move_id.id})
            self.write({'state': 'confirm'})
            self.write({'validate_date': validate_date})
            self.write({'over_due': False})