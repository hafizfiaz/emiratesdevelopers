# -*- coding: utf-8 -*-
from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from googletrans import Translator

import logging
_logger = logging.getLogger(__name__)


class DLDPaymentPlan(models.Model):
    _name = "dld.payment.plan"
    _description = "DLD Schedule"

    name = fields.Char('Description')
    percentage = fields.Float('Percentage')
    payment_date_disc = fields.Char('Payment Date')
    amount = fields.Float(compute='compute_amount', string='Amount')
    asset_project_id = fields.Many2one('account.asset.asset', 'Project', domain="[('project', '=', True)]")
    booking_id = fields.Many2one('sale.order', 'Booking')
    sale_id = fields.Many2one('sale.order', 'SPA')

    @api.depends('percentage','sale_id','sale_id.amount_total')
    def compute_amount(self):
        for rec in self:
            amount = 0
            if rec.sale_id and rec.percentage:
                amount = (rec.percentage/100) * rec.sale_id.amount_total
            rec.amount = amount


class AccountAssetAsset(models.Model):
    _inherit = "account.asset.asset"

    payment_plan_ids = fields.One2many('dld.payment.plan', 'asset_project_id', 'Payment Plan')




