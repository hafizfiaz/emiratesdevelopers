# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
# from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError, ValidationError
import datetime
import time

#
# class AccountPayment(models.Model):
#     _inherit = 'crm.booking'
#
#     payment_id = fields.Many2one('account.payment')
#     payment_ids = fields.One2many('account.payment','booking_id','Receipts')
#
#
# class SaleOrder(models.Model):
#     _inherit = 'sale.order'
#
#     payment_id = fields.Many2one('account.payment')


