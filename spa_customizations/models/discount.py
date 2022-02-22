# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from datetime import datetime


class BookingDiscount(models.Model):
    _name = "booking.discount"
    _description = 'Booking Discount'

    name = fields.Char(string='Name')
    property_id = fields.Many2one('account.asset.asset', string='Property')
    asset_project_id = fields.Many2one('account.asset.asset', 'Project', domain="[('project', '=', True)]")
    disc_type = fields.Selection([
        ('percent', 'Percentage'),
        ('fixed', 'Fixed Discount')], string='Type')
    value = fields.Float(string='Value')

    active = fields.Boolean('Active',default=True)
    start_date = fields.Datetime('Start Date')
    end_date = fields.Datetime('End Date')
    user_ids = fields.Many2many('res.users',
        relation='rel_user_booking_disc',
        column1='booking_discount_id',
        column2='user_id',
        string='Visible to Users')
    approval_require = fields.Boolean('Approval Require')
    unit_type_ids = fields.Many2many('unit.type', string="Unit Types")
    manual = fields.Boolean('Manual')
    min_down_payment_perc = fields.Float('Minimum Down Payment %')
    related_payment_ids = fields.Many2many('payment.schedule', 'schedule_discount_rel', 'schedule_id', 'discount_id',
                                           'Related Payment Options')

    @api.onchange('asset_project_id')
    def onchange_asset_project_id(self):
        property_ids = self.env['account.asset.asset'].search(
            [('state', '=', 'draft'), ('parent_id', '=', self.asset_project_id.id)])
        return {'domain': {'property_id': [('id', 'in', property_ids.ids)]}}

