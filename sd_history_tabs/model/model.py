# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
from odoo.tools.translate import _
from odoo.exceptions import UserError
import base64
import os
# import urllib2


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    @api.depends('journal_id','journal_id.name')
    def compute_naqoodi(self):
        for rec in self:
            if rec.journal_id.name == "Naqoodi Payment":
                rec.naqoodi_check = True
            else:
                rec.naqoodi_check = False

    receipts_ids = fields.Many2many('account.payment', 'account_receipt_history_rel','receipt_id','history_id', string='Receipt History')
    payments_ids = fields.Many2many('account.payment', 'account_payment_history_rel','payment_id','history_id', string='Payment History')
    bills_ids = fields.Many2many('account.move', 'account_bill_history_rel','bill_id','history_id', string='Bills History')
    naqoodi_payments_ids = fields.Many2many('account.payment', 'account_payment_naqoodi_rel','payment_id','naqoodi_id', string='Naqoodi Payment for this Unit')
    naqoodi_check = fields.Boolean('Naqoodi', compute='compute_naqoodi', store=True)

    def compute_tabs(self):
        receipts = self.env['account.payment'].search(
            [('partner_id', '=', self.partner_id.id), ('payment_type','=','inbound'),('state', 'in', ['posted','approved'])])
        self.receipts_ids = [(6, 0, receipts.ids)]
        payments = self.env['account.payment'].search(
            [('partner_id', '=', self.partner_id.id), ('payment_type','=','outbound'),('state', 'in', ['posted','approved'])])
        self.payments_ids = [(6, 0, payments.ids)]
        bills = self.env['account.move'].search(
            [('partner_id', '=', self.partner_id.id), ('state', '=', 'posted'), ('move_type','=','in_invoice')])
        self.bills_ids = [(6, 0, bills.ids)]
        naqoodi_payments = self.env['account.payment'].search(
            [('property_id', '=', self.property_id.id), ('journal_id.name','=','Naqoodi Payment'), ('payment_type','=','outbound'),('state', 'in', ['posted','approved'])])
        self.naqoodi_payments_ids = [(6, 0, naqoodi_payments.ids)]


class AccountMove(models.Model):
    _inherit = 'account.move'

    @api.depends('journal_id','journal_id.name')
    def compute_naqoodi(self):
        for rec in self:
            if rec.journal_id.name == "Naqoodi Payment":
                rec.naqoodi_check = True
            else:
                rec.naqoodi_check = False

    receipts_ids = fields.Many2many('account.payment', 'account_invoice_receipt_history_rel', 'receipt_id', 'history_id',
                                    string='Receipt History', order='payment_date desc')
    payments_ids = fields.Many2many('account.payment', 'account_invoice_payment_history_rel', 'payment_id', 'history_id',
                                    string='Payment History', order='payment_date desc')
    naqoodi_payments_ids = fields.Many2many('account.payment', 'account_invoice_naqoodi_rel', 'bill_id',
                                            'naqoodi_id', string='Naqoodi Payment for this Unit')
    naqoodi_check = fields.Boolean('Naqoodi', compute='compute_naqoodi', store=True)

    def compute_tabs(self):
        receipts = self.env['account.payment'].search(
            [('partner_id', '=', self.partner_id.id), ('payment_type', '=', 'inbound'), ('state', 'in', ['posted','approved'])])
        self.receipts_ids = [(6, 0, receipts.ids)]
        payments = self.env['account.payment'].search(
            [('partner_id', '=', self.partner_id.id), ('payment_type', '=', 'outbound'), ('state', 'in', ['posted','approved'])])
        self.payments_ids = [(6, 0, payments.ids)]
        naqoodi_payments = self.env['account.payment'].search(
            [('partner_id', '=', self.partner_id.id), ('journal_id.name','=','Naqoodi Payment'),('state', 'in', ['posted','approved'])])
        print(naqoodi_payments)
        self.naqoodi_payments_ids = [(6, 0, naqoodi_payments.ids)]


# class ApprovalApproval(models.Model):
#     _inherit = 'approval.approval'
#
#     receipts_ids = fields.Many2many('account.payment', 'approval_receipt_history_rel','receipt_id','history_id', string='Receipt History', order='payment_date desc')
#     payments_ids = fields.Many2many('account.payment', 'approval_payment_history_rel','payment_id','history_id', string='Payment History', order='payment_date desc')
#     bills_ids = fields.Many2many('account.invoice', 'approval_bill_history_rel','bill_id','history_id', string='Bills History', order='create_date desc')
#
#     # bill_request_ids = fields.Many2many('approval.approval', 'account_bill_request_history_rel','bill_request_id','history_id', string='Bill Approval History', order='create_uid desc')
#
#     @api.multi
#     def compute_tabs(self):
#         receipts = self.env['account.payment'].search(
#             [('partner_id', '=', self.partner_id.id), ('payment_type','=','inbound'), '|',('state', '=', 'posted'),('state_pdc', '=', 'approved')])
#         self.receipts_ids = [(6, 0, receipts.ids)]
#         payments = self.env['account.payment'].search(
#             [('partner_id', '=', self.partner_id.id), ('payment_type','=','outbound'), '|',('state', '=', 'posted'),('state_pdc', '=', 'approved')])
#         self.payments_ids = [(6, 0, payments.ids)]
#         bills = self.env['account.invoice'].search(
#             [('partner_id', '=', self.partner_id.id), ('state', '=', 'paid'), ('type','=','in_invoice')])
#         self.bills_ids = [(6, 0, bills.ids)]

