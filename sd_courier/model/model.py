# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
import time
from odoo.tools.translate import _
from lxml import etree
from odoo.exceptions import UserError, ValidationError


class CourierCourier(models.Model):
    _name = 'courier.courier'
    _description = "Courier"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char('Courier Detail', tracking=True)
    partner_id = fields.Many2one('res.partner', 'Customer Name', tracking=True)
    mobile = fields.Char('Mobile', related='partner_id.mobile', readonly=True, tracking=True)
    email = fields.Char('Email', related='partner_id.email', readonly=True, tracking=True)
    spa_id = fields.Many2one('sale.order', 'SPA Number', tracking=True)
    asset_project_id = fields.Many2one('account.asset.asset', 'Project',
                                       domain="[('project', '=', True)]",
                                       tracking=True)
    property_id = fields.Many2one('account.asset.asset', string='Property',
                                  tracking=True)
    courier_company_id = fields.Many2one('res.partner', 'Courier Company Name', tracking=True)
    # courier_company_name = fields.Char('Courier Company Name', tracking=True)
    sender_name_and_address = fields.Text('Sender Name & Address', tracking=True)
    receiver_name = fields.Char('Receiver Name', tracking=True)
    receiver_contact = fields.Char('Receiver Contact', tracking=True)
    receiver_address = fields.Text('Receiver Address', tracking=True)
    country_id = fields.Many2one('res.country', 'Country', tracking=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('under_review', 'Under Review'),
        ('under_verification', 'Under Verification'),
        ('under_dispatch', 'Under Dispatch'),
        ('dispatched', 'Dispatched'),
        ('rejected', 'Rejected'),
        ('cancel', 'Canceled'),
    ], 'Status', default='draft', tracking=True, readonly=True)


    # @api.model
    # def send_courier_review_email(self):
    #     mr = self.env['mail.recipients'].search([('name','=','Courier Recipients')])
    #     for rec in mr:
    #         if rec.user_ids:
    #             email_template = rec.env.ref('sd_courier.courier_review_email')
    #             email_template.email_to = rec.get_partner_ids(rec.user_ids)
    #             email_template.send_mail(self.id, force_send=True)

    def action_submit_review(self):
        self.write({'state': 'under_review'})

    def action_review(self):
        self.write({'state': 'under_verification'})

    def action_verify(self):
        self.write({'state': 'under_dispatch'})

    def action_dispatch(self):
        self.write({'state': 'dispatched'})

    def action_reject(self):
        self.write({'state': 'rejected'})

    def action_cancel(self):
        self.write({'state': 'cancel'})

    def action_draft(self):
        self.write({'state': 'draft'})
