# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.osv import expression
from odoo.tools import float_is_zero
from odoo.tools import float_compare, float_round
from odoo.tools.misc import formatLang
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, date


import time
import math

# class account_account(models.Model):
#     _inherit = "account.account"
#
#     is_cheque = fields.Boolean(string='Account for Cheque',default=False)



class AccountChequeStatement(models.Model):
    _name = 'account.cheque.statement'
    _order = "name desc, id desc"
    _inherit = ['mail.thread']
    _description = "Account Cheque Statement"


    name = fields.Char(string='Number', states={'open': [('readonly', False)]}, copy=False, readonly=True)
    issue_date = fields.Date(required=True, states={'confirm': [('readonly', True)]}, index=True, copy=False, string='Issue Date')
    ref = fields.Char(string='Reference')
    partner_id = fields.Many2one('res.partner',string='Partner')
    cheque_bank = fields.Many2one('res.bank', string="Cheque Bank")
    cheque_branch = fields.Char(string="Branch")
    cheque_number = fields.Char(string="Cheque Number")
    allow_dup_cheque_no = fields.Boolean(string='Allow Duplicate Cheque')
    cheque_date = fields.Date(string="Effective Date")
    amount = fields.Float(string="Amount")
    state = fields.Selection([('open', 'New'), ('post', 'Post'),('confirm', 'Validated'),('cancel', 'Cancel'),('reject', 'Reject')], string='Status', required=True, readonly=True,copy=False, default='open')
    type = fields.Selection([('rec','Receive'),('pay','Payment')])
    communication = fields.Char(string='Remark')
    validate_date = fields.Date(string='Check Date')
    over_due = fields.Boolean(string='Over Due',default=False)
    name_for_cheque = fields.Char(string='Name for Cheque')

    #for technical
    journal_id = fields.Many2one('account.journal',string='Journal')
    move_id = fields.Many2one('account.move',compute="get_move_id",string='Original Transaction')
    move_new_id = fields.Many2one('account.move', string='New Transaction')
    payment_id = fields.Many2one('account.payment',string='Payment')
    company_id = fields.Many2one('res.company', related='journal_id.company_id', string='Company',readonly=True)
    user_id = fields.Many2one('res.users', string='Responsible Person', required=False, default=lambda self: self.env.user)
    account_id = fields.Many2one('account.account',string='Destination Account',readonly=True,states={'open': [('readonly', False)]})

    # @api.multi
    def unlink(self):
        ################## Remove this condition temporary - JA 08/10/2020 due to missing move_id in check from cancel payment but does not cancel cheque#############
        if any(rec.state == 'confirm' for rec in self):
            raise UserError(_("You can not delete a validated cheque"))
        ################## Remove this condition temporary#############
        return super(AccountChequeStatement, self).unlink()

    @api.model
    def check_over_due(self):
        cheque_ids = self.env['account.cheque.statement'].search([('cheque_date', '<', datetime.now().strftime('%m/%d/%Y 00:00:00')),('state','=','open')])
        for cheque in cheque_ids:
            cheque.over_due = True

    # @api.multi
    def action_reject(self):
        #print "action_reject"
        view = self.env['ir.model.data'].xmlid_to_res_id('thai_accounting.cheque_reject_form')
        ctx = self.env.context.copy()
        # ctx.update({'order_id': self.id})
        return {
            'name': _(u'Warning: Reject the cheque can not redo'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'account.cheque.statement',
            'views': [(view, 'form')],
            'view_id': view,
            'target': 'new',
            'res_id': self.id,
            'context': ctx,
        }

    # @api.multi
    def reject_cheque(self):
        # print "reject_cheque"
        self.payment_id.cancel()
        self.write({'state': 'reject'})
        self.validate_date = date.today()



    # @api.one
    @api.onchange('payment_id.move_line_ids')
    def get_move_id(self):
        if self.payment_id.move_line_ids:
            self.move_id = self.payment_id.move_line_ids[0].move_id.id


    @api.model
    def create(self, vals):
        if vals.get('type') == 'rec':
            vals['name'] = self.env['ir.sequence'].next_by_code('cheque.rec.no')
        else:
            vals['name'] = self.env['ir.sequence'].next_by_code('cheque.pay.no')

        vals['account_id'] = self.env['account.journal'].browse(vals['journal_id']).bank_for_cheque_account_id.id
        return super(AccountChequeStatement,self).create(vals)

    # @api.multi
    def action_validate(self):
        # print "action_validate"
        if not self.validate_date:
            self.validate_date = date.today()

        move_line_vals = self.cheque_move_line_reverse_get()

        line = [(0, 0, l) for l in move_line_vals]

        new_name = ""

        # journal_id = self.env['account.journal'].search([('code','=','MISC')],limit=1)
        journal_id = self.journal_id.adj_journal

        if journal_id.sequence_id:
            # If invoice is actually refund and journal has a refund_sequence then use that one or use the regular one
            sequence_id = journal_id.sequence_id
            new_name = sequence_id.with_context(ir_sequence_date=self.validate_date).next_by_id()
            # print "new_new"
            # print new_name
        else:
            raise UserError(_('Please check sequence of your journal'))

        if move_line_vals:
            move_vals = {
                'ref': self.ref,
                'line_ids': line,
                'journal_id': self.journal_id.id,
                'date': self.validate_date,
                'name': new_name,
                'partner_id' : self.partner_id.id,
                # 'invoice_date': tax_invoice_date,
                'narration': self.communication,
            }
            account_move = self.env['account.move']
            # print "move vals"
            # print move_vals
            move_id = account_move.create(move_vals)
            move_id.post()
            self.write({'move_new_id': move_id.id})
            self.write({'state': 'confirm'})
            self.write({'over_due': False})

    def cheque_move_line_reverse_get(self):
        # print "cheque_move_line_reverse_get"
        res = []
        line_id = self.env['account.move.line'].search([('move_id','=',self.move_id.id),('account_id.is_cheque','=',True)],limit=1)

        if line_id:
            original_account_id = line_id.account_id
            if line_id.debit:
                debit = 0.00
                credit = line_id.debit
            else:
                debit = line_id.credit
                credit = 0.00
        else:
            print ('----New')

            if self.type == 'rec':
                credit = self.amount
                debit = 0.00
            else:
                credit =  0.00
                debit = self.amount
            original_account_id = self.journal_id.default_credit_account_id

        new_account_id = self.account_id


        #convert for first statement
        print ('---aCC')
        print (original_account_id.name)
        print(new_account_id.name)
        print (debit)
        print (credit)
        # print original_account_id.name
        # print new_account_id.name
        if original_account_id and new_account_id:
            #convert exsting line to remove the exist value
            res.append({
                'date_maturity': self.validate_date,
                'partner_id': self.partner_id.id,
                'ref': self.ref,
                'name': self.name,
                'debit': debit,
                'credit': credit,
                'account_id': original_account_id.id,
                'amount_currency': False,
                'currency_id': False,
                'quantity': 1.00,
                'product_id': False,
                'product_uom_id': False,
                'analytic_account_id': False,
                'tax_ids': False,
                'tax_line_id': False,
            })

            #new line for new record
            res.append({
                'date_maturity': self.validate_date,
                'partner_id': self.partner_id.id,
                'ref': self.ref,
                'name': self.name,
                'debit': credit,
                'credit': debit,
                'account_id': new_account_id.id,
                'amount_currency': False,
                'currency_id': False,
                'quantity': 1.00,
                'product_id': False,
                'product_uom_id': False,
                'analytic_account_id': False,
                'tax_ids': False,
                'tax_line_id': False,
            })

        else:
            raise UserError(_(
                'Please check your journal and ensure that default "Debit" and "Credit" Account is marked as "Accoun for Cheque"'))
        print ('move-res')
        print (res)
        # print (x)
        return res

    def action_post(self):
        return self.write({'state': 'post'})

    def action_set_draft(self):
        return self.write({'state': 'open'})


    def action_cancel(self):
        if self.move_new_id:
            self.move_new_id.button_draft()
            self.move_new_id.button_cancel()
            self.move_new_id.with_context(force_delete=True).unlink()
        return self.write({'state': 'cancel'})



class account_payment(models.Model):
    _inherit = "account.payment"

    def post(self):
        res = super(account_payment,self).post()
        for payment in self:
            if payment.bank_cheque and not payment.cheque_reg_id:
                if payment.partner_type == 'customer':
                    type = 'rec'
                else:
                    type = 'pay'
                vals_cheque_rec = {
                    'issue_date': payment.payment_date,
                    'ref': payment.communication,
                    'cheque_bank': payment.cheque_bank.id,
                    'partner_id': payment.partner_id.id,
                    'cheque_branch': payment.cheque_branch,
                    'cheque_number': payment.cheque_number,
                    'cheque_date': payment.cheque_date,
                    'amount': payment.amount,
                    'journal_id': payment.journal_id.id,
                    'user_id': self.env.user.id,
                    'communication': payment.remark,
                    'company_id': payment.env.user.company_id.id,
                    'type': type,
                    'payment_id': payment.id,
                }
                self.cheque_reg_id = self.env['account.cheque.statement'].create(vals_cheque_rec).id
                self.cheque_reg_id.get_move_id()
        return res