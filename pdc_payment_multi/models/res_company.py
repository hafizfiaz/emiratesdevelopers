# -*- coding: utf-8 -*-
from odoo import fields, models, api, _

class res_company(models.Model):
    _inherit = 'res.company'

    pdc_payment_terms = fields.Html('Multi PDC Payment-Terms & Conditions', translate=True, help="Default terms and conditions for Payments.")

