# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
from datetime import datetime
from odoo.addons import decimal_precision as dp
from odoo.tools.translate import _
import time
from lxml import etree
from odoo.exceptions import UserError, ValidationError
from odoo import http


class AccountMove(models.Model):
    _inherit="account.move"

    related_installment_status = fields.Selection(
        [('draft', 'Draft'),  # ('confirm_booking', 'Confirm Booking'),
         ('confirm', 'Confirmed'),
         ('cancel', 'Cancel')],
        string='Installment Status', related="schedule_id.state", store=True)
    xx_related_spa_id = fields.Many2one('sale.order', string='Related SPA/Booking',
                                     related='schedule_id.sale_id', store=True)
    xx_related_spa_status = fields.Selection([
        ('draft', 'Draft'),
        ('under_discount_approval', 'Under Approval'),
        ('tentative_booking', 'Tentative Booking'),
        ('review', 'Under Review'),
        ('under_cancellation', 'Booking Under Cancellation'),
        ('confirm_spa', 'Confirmed for SPA'),
        # ('approved', 'Approved'),
        ('booking_rejected', 'Rejected'),
        ('booking_cancel', 'Cancel'),

        ('spa_draft', 'Unconfirmed SPA'),
        # ('under_legal_review_print', 'Under Legal Review for Print'),
        # ('under_acc_verification_print', 'Under Accounts Verification for Print'),
        # ('under_confirmation_print', 'Under Confirmation for Print'),
        # ('unconfirmed_ok_for_print', 'Unconfirmed SPA OK for Print'),
        ('under_legal_review', 'Under Legal Review'),
        ('under_accounts_verification', 'Under Accounts Verification'),
        ('under_approval', 'Under Approval'),
        # ('under_spa_termination', 'Under SPA Termination'),
        # ('under_termination', 'Under Termination'),
        ('sale', 'Approved SPA'),
        ('sent', 'Quotation Sent'),
        ('refund_cancellation', 'Refund Cancellation'),
        ('rejected', 'Rejected'),
        ('under_sd_admin_review', 'Under SD Admin Review'),
        ('paid', 'Approved SPA - Paid'),
        ('done', 'Locked'),
        ('cancel', 'Cancelled'),
    ], string='Related SPA Status', related="xx_related_spa_id.state",store=True)


class PDC(models.Model):
    _inherit="account.payment"

    state_update_date = fields.Date('Replaced/Withdrawn/Settled Date')

    def pdc_issued_stale(self):
        old_date = datetime.date.today() - datetime.timedelta(days=185)
        for rec in self.env['account.payment'].search([('maturity_date','<=',old_date),('payment_type','=','outbound'),('journal_id.type','=','pdc'),('journal_id.name','ilike','PDC Issued'),('state','=','collected')]):
            rec.state = 'stale'

    def check_outsourced(self):
        self.state_update_date = datetime.today().date()
        self.write({'state': 'replaced'})

    def check_replaced(self):
        self.state_update_date = datetime.today().date()
        self.write({'state': 'replaced'})

    def action_settle(self):
        self.state_update_date = datetime.today().date()
        self.write({'state': 'settle'})
