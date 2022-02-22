# -*- coding: utf-8 -*-
import base64
import os
from odoo import models, fields, api, _
from odoo.exceptions import UserError
root_path = os.path.dirname(os.path.abspath(__file__))


class RemoveScheduleWiz(models.Model):
    _name = "wiz.remove.schedule"
    _description = "Remove Schedule"

    name = fields.Char('Name', readonly=True)
    booking_id = fields.Many2one('sale.order', 'Booking')

    def action_remove_schedule_lines(self):
        for line in self.booking_id.sale_payment_schedule_ids:
            if line.inv:
                raise UserError(_(
                    "Some installment lines has invoices so you can not remove schedule this way"))
        for line1 in self.booking_id.sale_payment_schedule_ids:
            line1.unlink()