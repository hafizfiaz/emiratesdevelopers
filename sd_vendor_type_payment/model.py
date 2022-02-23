from odoo import models, fields, api, _


class VendorType(models.Model):
    _name = 'vendor.type'

    name = fields.Char('Name')
    vendor_active = fields.Boolean(string='Active', default=True)


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    vendor_type = fields.Many2one('vendor.type', 'Vendor Type')