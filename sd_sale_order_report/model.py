# -*- coding: utf-8 -*-
from odoo import api, exceptions, fields, models, _
import time


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    all_payment_bank_id = fields.Many2one('account.journal', 'All Payment Bank', domain="[('type', '=', 'bank')]",
                                          tracking=True)

    @api.onchange('asset_project_id', 'property_id')
    def onchange_all_bank_ids(self):
        if self.asset_project_id:
            self.all_payment_bank_id = self.asset_project_id.all_payment_bank_id.id

    @api.model
    def old_payment_bank(self):
        sos = self.env['sale.order'].search([])
        for rec in sos:
            if rec.asset_project_id:
                rec.all_payment_bank_id = rec.asset_project_id.all_payment_bank_id



