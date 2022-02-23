# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
import time
from odoo.tools.translate import _
from lxml import etree
from odoo.exceptions import UserError, ValidationError


class MultiPdcPayment(models.Model):
    _name = 'multi.pdc.payment'
    _description = "Multi PDC Payment"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'id desc'
    _rec_name = 'name'


    def _get_jouranl_id(self):
        # for line in self.collection_line:
        journal_obj = self.env['account.journal'].search([('type', '=', 'pdc'),('subtype', '=', 'payable')])
        if journal_obj:
            return journal_obj[0].id
        else:
            journal_obj1 = self.env['account.journal'].search([('type', '=', 'pdc')])
            if journal_obj1:
                return journal_obj1[0].id
            else:
                return False

    name = fields.Char('Serial Number', readonly=True, default='/', tracking=True)
    # serial_number = fields.Char('Serial Number')
    partner_id = fields.Many2one('res.partner', 'Customer', required=True, tracking=True)
    mobile = fields.Char('Mobile', related='partner_id.mobile', readonly=True, tracking=True)
    # phone = fields.Char(related='partner_id.phone', string="Phone", readonly=True)
    # email = fields.Char(related='partner_id.email', string="Email", readonly=True)
    date = fields.Date('Date', required=True, default=time.strftime('%Y-%m-%d'), tracking=True)
    reference = fields.Char('Reference', tracking=True)
    memo = fields.Char('Memo', tracking=True)
    company_id = fields.Many2one('res.company', 'Company', required=True, default=lambda self: self.env.user.company_id, tracking=True)
    #
    collection_line = fields.One2many('account.payment', 'multi_pdc_payment_id', 'Collection Lines', tracking=True)
    journal_id = fields.Many2one('account.journal', string='Payment Journal', tracking=True)
    user_id = fields.Many2one('res.users', 'Responsible', default=lambda self: self.env.user, tracking=True)
    currency_id = fields.Many2one('res.currency', 'Currency', required=True,
                                  default=lambda self: self.env.user.company_id.currency_id.id, tracking=True)
    amount_total = fields.Float(compute='get_amount_total', string='Total', tracking=True)
    note = fields.Html('Multi PDC Payment-Terms & Conditions', default=lambda self: self.env.user.company_id.pdc_payment_terms)
    payment_term = fields.Many2one('account.payment.term', 'Payment Term', tracking=True)
    sale_id = fields.Many2one('sale.order', 'SPA', tracking=True)
    # lead_id = fields.Many2one('crm.lead', 'Booking')
    # create_uid = fields.Many2one('res.users', 'Created By')
    booking_id = fields.Many2one('sale.order', 'Booking', tracking=True)
    # shop_id = fields.Many2one('sale.shop', 'Branch', readonly=True, states={'draft': [('readonly', False)]})
    officer_id = fields.Many2one('res.users', 'Officer', readonly=True, default=lambda self: self.env.user,
                                 states={'draft': [('readonly', False)]},
                                 tracking=True)
    # collection_id = fields.Many2one('account.voucher.collection', 'Customer Payments Multi', readonly=True,
    #                                 states={'draft': [('readonly', False)]})
    property_id = fields.Many2one('account.asset.asset', string='Property', tracking=True)
    asset_project_id = fields.Many2one('account.asset.asset', 'Project', domain="[('project', '=', True)]", tracking=True)
    # agreed_term = fields.Char(string='Agreed Term')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('under_gm_review', 'Under GM Review'),
        ('gm_approved', 'GM Approved'),
        ('gm_rejected', 'GM Rejected'),
        ('pend_collection', 'Pending Collection'),
        ('collected', 'Collected'),
        ('cancelled', 'Cancelled'),
    ], 'Status', default='draft', tracking=True, readonly=True)
    # charge_amount = fields.Float('Charge', digits_compute=dp.get_precision('Account'),
    #                              states={'draft': [('readonly', False)]}, tracking=True)
    # bank_deposit = fields.Many2one('res.partner.bank', 'Bank where the check is deposit/cashed',
    #                                help='This bank indicate the name of the bank which the check is deposit and cashed')
    # move_id = fields.Many2one('account.move', 'Account Entry', copy=False)
    # move_ids = fields.One2many('account.move.line', 'collection_id', string='Journal Items', readonly=True)



    @api.onchange('asset_project_id', 'property_id')
    def onchange_asset_project_id(self):
        property_ids = self.env['account.asset.asset'].search(
            [('parent_id', '=', self.asset_project_id.id)])
        booking_ids = self.env['sale.order'].search([('property_id', '=', self.property_id.id)])
        return {'domain': {'property_id': [('id', 'in', property_ids.ids)],
                           'booking_id': [('id', 'in', booking_ids.ids)]}}

    
    def action_pending_collect(self):
        for collect in self:
            for line in collect.collection_line:
                if line.chk:
                    line.action_pending()
            if not collect.name or collect.name == '/':
                name = self.env['ir.sequence'].next_by_code('multi.pdc.payment')
                self.write({'name': name})

            collect.write({'state': 'pend_collection'})

        return True

    @api.model
    def get_old_project_properties(self):
        mpp = self.env['multi.pdc.payment'].search([])
        for rec in mpp:
            for line in rec.collection_line:
                line.asset_project_id = rec.asset_project_id.id
                line.property_id = rec.property_id.id

    
    def action_collect(self):
        for collect in self:
            for line in collect.collection_line:
                if line.chk:
                    line.button_collected()
                else:
                    line.action_post()
            if not collect.name or collect.name == '/':
                name = self.env['ir.sequence'].next_by_code('multi.pdc.payment')
                self.write({'name': name})

            collect.write({'state': 'collected'})

        return True

    @api.depends('collection_line')
    def get_amount_total(self):
        cur_obj = self.env['res.currency']
        res = {}
        for order in self:
            # res[order.id] = 0.0
            val1 = 0.0
            cur = order.currency_id
            for line in order.collection_line:
                # amount = line.amount if line.state not in ('cancel','refused') else 0.0
                amount = line.amount
                if line.currency_id != cur:
                    amount = cur_obj.compute(line.currency_id.id, cur.id, amount)
                val1 += amount
            order.amount_total = val1

    # @api.onchange('collection_line')
    # def onchange_collectionLine_id(self):
    #     print('lineeee')

    @api.onchange('partner_id')
    def onchange_partner_id(self):
        partner_obj = self.env['res.partner']
        if not self.partner_id:
            self.update({'mobile': '', 'collection_line': [(6, 0, [])]})
        else:
            partner = partner_obj.browse(self.partner_id.id)
            self.update({'mobile': partner.mobile})
            payment_term = partner.property_payment_term_id and partner.property_payment_term_id.id or False
            self.update({'payment_term': payment_term})

    
    def action_under_gm_review(self):
        self.write({'state': 'under_gm_review'})

    
    def action_gm_approved(self):
        self.write({'state': 'gm_approved'})

    
    def action_gm_rejected(self):
        self.write({'state': 'gm_rejected'})

    
    def action_rool_back(self):
        self.write({'state': 'draft'})

    
    def action_cancel_draft(self):
        for line in self.collection_line:
            if line.state == 'draft':
                line.action_draft_to_cancel()
            else:
                line.cancel()
        self.write({'state': 'cancelled'})

    
    def action_cancel(self):
        for line in self.collection_line:
            if line.state == 'draft':
                line.action_draft_to_cancel()
            else:
                line.action_cancel()
        self.write({'state': 'cancelled'})

    
    def action_draft(self):
        for line in self.collection_line:
            if line.journal_id.type == 'pdc':
                line.write({'journal_collected_entry': False,
                            'journal_pending_entry': False,
                            'journal_posted_entry': False,
                            'journal_rejected_entry': False,
                            'journal_outsourced_entry': False,
                            'journal_bank_entry': False,
                            'state': 'draft'})
            else:
                line.write({'state': 'draft'})
        self.write({'state': 'draft'})


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    multi_pdc_payment_id = fields.Many2one('multi.pdc.payment', 'Multi PDC Payment')

#
# class AccountMoveLine(models.Model):
#     _inherit = 'account.move.line'
#
#     collection_id = fields.Many2one("account.voucher.collection", 'Collection')
