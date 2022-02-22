# -*- coding: utf-8 -*-
from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta


class ChangeWebStatus(models.TransientModel):
    _name = "change.web.status"
    _description = 'Change Web Status'

    asset_project_id = fields.Many2one('account.asset.asset', 'Project', domain="[('project', '=', True)]")
    property_id = fields.Many2one('account.asset.asset', string='Property')
    web_state = fields.Selection(([('draft', 'Available'), ('sold', 'Sold')]), string='Web Status')

    @api.onchange('asset_project_id')
    def onchange_asset_project_id(self):
        property_ids = self.env['account.asset.asset'].search(
            [('parent_id', '=', self.asset_project_id.id)])
        return {'domain': {'property_id': [('id', 'in', property_ids.ids)]}}

    def action_apply(self):
        if self.property_id:
            self.property_id.web_state = self.web_state


class AccountAsset(models.Model):
    _inherit = "account.asset.asset"

    web_state = fields.Selection(([('draft', 'Available'), ('sold', 'Sold')]), string='Web Status',
                                 tracking=True)

    @api.depends('property_id')
    def _get_4_percent_of_property(self):
        for rec in self:
            rec.property_four_percent = rec.price * 0.04

    @api.onchange('price')
    def _get_oqood(self):
        for rec in self:
            rec.oqood_fee = rec.price * 0.04

