# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
from odoo.exceptions import UserError, ValidationError
import datetime
import time


class JournalSubType(models.Model):
    _name = 'account.journal.type'
    _description = 'Account Journal Type'

    name = fields.Char('Name')
    active = fields.Boolean('Active', default=True)


class AccountReceipt(models.Model):
    _inherit = 'account.journal'

    payment_type = fields.Selection([('receipt', 'Receipt'), ('payment', 'Payment')], 'Payment Type')
    sub_type = fields.Many2one('account.journal.type', 'Bank Sub Type')
    # type = fields.Selection(selection_add=[('pdc', 'Check')])
    type = fields.Selection([
            ('sale', 'Sales'),
            ('purchase', 'Purchase'),
            ('cash', 'Cash'),
            ('bank', 'Bank'),
            ('general', 'Miscellaneous'),('pdc', 'Check')
        ], required=True,
        help="Select 'Sale' for customer invoices journals.\n"\
        "Select 'Purchase' for vendor bills journals.\n"\
        "Select 'Cash' or 'Bank' for journals that are used in customer or vendor payments.\n"\
        "Select 'General' for miscellaneous operations journals.")

    @api.depends('type')
    def _compute_inbound_payment_method_ids(self):
        for journal in self:
            if journal.type in ('bank', 'cash', 'pdc'):
                journal.inbound_payment_method_ids = self._default_inbound_payment_methods()
            else:
                journal.inbound_payment_method_ids = False

    @api.depends('type')
    def _compute_outbound_payment_method_ids(self):
        for journal in self:
            if journal.type in ('bank', 'cash', 'pdc'):
                journal.outbound_payment_method_ids = self._default_outbound_payment_methods()
            else:
                journal.outbound_payment_method_ids = False



class AccountPayment(models.Model):
    _inherit = 'account.payment'

    sub_type = fields.Many2one('account.journal.type', 'Bank Sub Type',related='journal_id.sub_type', store=True)

