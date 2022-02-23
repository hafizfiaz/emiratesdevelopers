# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import AccessError, UserError
from odoo.tools import float_compare
import time
from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT


class CommissionType(models.Model):
    _name = "commission.type"
    _description = "Commission Type"

    name = fields.Char(string='Name', required=True)
    percentage = fields.Boolean(string='Percentage')
    fixed = fields.Boolean(string='Fixed')
    percentage_value = fields.Float(string='Percentage Value')
    amount_value = fields.Float(string='Amount Value')
    asset_project_id = fields.Many2one('account.asset.asset', 'Project', domain="[('project', '=', True)]")
    property_id = fields.Many2one('account.asset.asset',string='Property')
    payment_schedule_id = fields.Many2one('payment.schedule',string='Payment Schedule')
    active = fields.Boolean(string='Active', default=True)
    unit_type_ids = fields.Many2many('unit.type', string="Unit Types")
    is_agent = fields.Boolean(string="Agent")
    is_internal_user = fields.Boolean(string="Internal User")

    @api.onchange('asset_project_id')
    def onchange_asset_project_id(self):
        property_ids = self.env['account.asset.asset'].search(
            [('state', '=', 'draft'), ('parent_id', '=', self.asset_project_id.id)])
        payment_schedule_ids = self.env['payment.schedule'].search([('asset_project_id', '=', self.asset_project_id.id)])
        return {'domain': {'property_id': [('id', 'in', property_ids.ids)],
                           'payment_schedule_id': [('id', 'in', payment_schedule_ids.ids)]}}

    @api.onchange('percentage','fixed')
    def onchange_type(self):
        if self.percentage:
            self.fixed = False
            self.amount_value = False
        if self.fixed:
            self.percentage = False
            self.percentage_value = False
