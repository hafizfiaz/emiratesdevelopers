# -*- coding: utf-8 -*-
from odoo import fields, models, api, _


# class CrmBooking(models.Model):
#     _inherit = 'crm.booking'
#
#     pdc_receipt_ids = fields.One2many('account.voucher.collection', 'booking_id', string='PDC Receipts')


# class SaleOrder(models.Model):
#     _inherit = 'sale.order'
#
#     pdc_receipt_ids = fields.One2many('account.voucher.collection', 'sale_id', related='booking_id.pdc_receipt_ids', store=True, string='PDC Receipts')