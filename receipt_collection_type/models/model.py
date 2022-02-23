# -*- coding: utf-8 -*-
from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError
import datetime
import time


class CollectionType(models.Model):
    _name = 'collection.type'
    _description = "Collection Type"

    name = fields.Char(string="Name")
    active = fields.Boolean(string="Active")
    auto_reconcile = fields.Boolean(string="Eligible for Auto Recon", default=False)
    project = fields.Boolean(string="Project")
    property = fields.Boolean(string="Property")
    booking = fields.Boolean(string="Booking")
    hide_booking = fields.Boolean(string="Hide Booking")
    hide_spa = fields.Boolean(string="Hide SPA")
    related_tenancy_chk = fields.Boolean(string="Related Tenancy")


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    collection_type_id = fields.Many2one('collection.type', string="Collection Type")
    officer_id = fields.Many2one('res.users', 'Collection Officer', tracking=True)
    salesperson_id = fields.Many2one('res.users', 'SalesPerson' ,store=True, tracking=True)
    owner_ids = fields.Many2many('res.users', 'payment_owner_rel', 'payment_id', 'user_id', 'Owner', compute='get_owner',store=True,)
    project = fields.Boolean(string="Project chk", related='collection_type_id.project')
    property = fields.Boolean(string="Property chk", related='collection_type_id.property')
    booking = fields.Boolean(string="Booking chk", related='collection_type_id.booking')
    hide_booking = fields.Boolean(string="Hide Booking chk", related='collection_type_id.hide_booking')
    hide_spa = fields.Boolean(string="Hide SPA chk", related='collection_type_id.hide_spa')
    related_tenancy_chk = fields.Boolean(string="Related Tenancy Chk", related='collection_type_id.related_tenancy_chk',
                                         store=True)

    # @api.depends('booking_id')
    # def get_salesperson(self):
    #     for rec in self:
    #         if rec.booking_id:
    #             rec.salesperson_id = rec.booking_id.user_id.id

    @api.depends('salesperson_id','officer_id')
    def get_owner(self):
        for rec in self:
            res = [2]
            if rec.salesperson_id:
                res.append(rec.salesperson_id.id)
            if rec.officer_id:
                res.append(rec.officer_id.id)
            rec.owner_ids = [(6,0, res)]

class AccountVoucherCollection(models.Model):
    _inherit = 'account.voucher.collection'

    collection_type_id = fields.Many2one('collection.type', string="Collection Type")
    related_tenancy_chk = fields.Boolean(string="Related Tenancy Chk", related='collection_type_id.related_tenancy_chk')
    account_holder_name = fields.Text('A/c Holder')
    bank_issued_check = fields.Many2one('res.bank', 'Bank',
                                        help='This bank indicate the name of the bank of check')
    remarks = fields.Text('Remarks')

    @api.model
    def map_spa_pdcs(self):
        colls = self.env['account.voucher.collection'].search([('sale_id','!=',False)])
        for rec in colls:
            if rec.sale_id:
                for line in rec.collection_line:
                    line.spa_id = rec.sale_id


    @api.onchange('collection_type_id')
    def _onchange_collection(self):
        if self.collection_type_id:
            for line in self.collection_line:
                line.collection_type_id = self.collection_type_id.id
                line.write({'collection_type_id':self.collection_type_id.id})

#     @api.onchange('officer_id')
#     def _onchange_officer(self):
#         if self.officer_id:
#             for line in self.collection_line:
#                 line.officer_id = self.officer_id.id
#                 line.write({'officer_id':self.officer_id.id})
#
#     @api.model
#     def cron_officer(self):
#         # pdcs = self.env['account.voucher.collection'].search([('officer_id','!=',False)])
#         # for rec in pdcs:
#         #     if rec.officer_id:
#         #         for line in rec.collection_line:
#         #             line.officer_id = rec.officer_id.id
#         #             line.write({'officer_id':rec.officer_id.id})
#         receipts = self.env['account.payment'].search([('payment_type','=','outbound')])
#         for rec in receipts:
#             if len(rec.owner_ids.ids) == 1:
#                 rec.write({'officer_id':rec.owner_ids[0].id})
#                 rec.officer_id=rec.owner_ids[0].id
#             else:
#                 if len(rec.owner_ids.ids) == 2:
#                     print('t')
#                 if rec.owner_ids.ids == [2,rec.booking_id.user_id.id]:
#                     rec.write({'officer_id': rec.booking_id.user_id.id})
#                     rec.officer_id = rec.booking_id.user_id.id
#                 else:
#                     officer = False
#                     for line in rec.owner_ids:
#                         if line.id not in  [rec.booking_id.user_id.id, 2]:
#                             officer = line.id
#                     rec.write({'officer_id':officer})
#                     rec.officer_id=officer
