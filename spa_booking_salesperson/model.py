# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.tools import safe_eval
from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from odoo.exceptions import UserError, ValidationError


class SaleOrder(models.Model):
    _inherit = "sale.order"

    @api.model
    def get_default_users(self):
        return self.env['res.users'].search([('id', '=', self.env.user.id)]).ids

    salesperson_ids = fields.Many2many('res.users', 'so_salesperson', 'cid', 'user_id', default=get_default_users,
                                       string='Salesperson')

    @api.model
    def get_old_salespersons_so(self):
        for rec in self.env['sale.order'].search([]):
            if rec.user_id and not rec.salesperson_ids:
                rec.salesperson_ids = [(6, 0, rec.user_id.ids)]
