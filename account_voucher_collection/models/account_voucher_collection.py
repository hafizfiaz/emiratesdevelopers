# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
import time
from odoo.tools.translate import _
from lxml import etree
from odoo.exceptions import UserError, ValidationError


class account_voucher_collection(models.Model):
    _name = 'account.voucher.collection'
    _description = 'Account Voucher Collection'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'id desc'
    _rec_name = 'number'


    def _get_jouranl_id(self):
        return True
        # for line in self.collection_line:
        # journal_obj = self.env['account.journal'].search([('type', '=', 'pdc'),('subtype', '=', 'receivable')])
        # if journal_obj:
        #     return journal_obj[0].id
        # else:
        #     journal_obj1 = self.env['account.journal'].search([('type', '=', 'pdc')])
        #     if journal_obj1:
        #         return journal_obj1[0].id
        #     else:
        #         return False

    number = fields.Char('Serial Number', readonly=True, default='/')
    serial_number = fields.Char('Serial Number')
    partner_id = fields.Many2one('res.partner', 'Customer', required=True)
    mobile = fields.Char('Mobile', related='partner_id.mobile', readonly=True)
    phone = fields.Char(related='partner_id.phone', string="Phone", readonly=True)
    email = fields.Char(related='partner_id.email', string="Email", readonly=True)
    date = fields.Date('Date', required=True, default=time.strftime('%Y-%m-%d'))
    # mobile_2 = fields.Char(related='partner_id.mobile2', string="Mobile 2", readonly=True, store=True)
    reference = fields.Char('Reference')
    name = fields.Char('Memo')
    company_id = fields.Many2one('res.company', 'Company', required=True, default=lambda self: self.env.user.company_id)
    # 'shop_id':fields.many2one('sale.shop', 'Branch'),
    collection_line = fields.One2many('account.payment', 'collection_id', 'Collection Lines')
    journal_id = fields.Many2one('account.journal', string='Payment Journal', default=_get_jouranl_id)
    user_id = fields.Many2one('res.users', 'Responsible', default=lambda self: self.env.user)
    currency_id = fields.Many2one('res.currency', 'Currency', required=True,
                                  default=lambda self: self.env.user.company_id.currency_id.id)
    amount_total = fields.Float(compute='get_amount_total', string='Total')
    note = fields.Html('Terms and conditions', default=lambda self: self.env.user.company_id.payment_note)
    payment_term = fields.Many2one('account.payment.term', 'Payment Term')
    sale_id = fields.Many2one('sale.order', 'SPA/Booking')
    lead_id = fields.Many2one('crm.lead', 'Booking')
    create_uid = fields.Many2one('res.users', 'Created By')
    # booking_id = fields.Many2one('crm.booking', 'Booking')
    shop_id = fields.Many2one('sale.shop', 'Branch', readonly=True, states={'draft': [('readonly', False)]})
    officer_id = fields.Many2one('res.users', 'Officer', readonly=True, default=lambda self: self.env.user,
                                 states={'draft': [('readonly', False)]},
                                 tracking=True)
    collection_id = fields.Many2one('account.voucher.collection', 'Customer Payments Multi', readonly=True,
                                    states={'draft': [('readonly', False)]})
    property_id = fields.Many2one('account.asset.asset', string='Property')
    asset_project_id = fields.Many2one('account.asset.asset', 'Project', domain="[('project', '=', True)]")
    agreed_term = fields.Char(string='Agreed Term')
    state = fields.Selection([
        ('draft', 'Draft'),
        # HRN 2018-05-10
        ('under_gm_review', 'Under GM Review'),
        ('under_accounts_verification', 'Under Accounts Verification'),
        ('gm_approved', 'GM Approved'),
        ('gm_rejected', 'GM Rejected'),
        # HRN
        ('collected', 'Collected'),
        ('cancelled', 'Cancelled'),
    ], 'Status', default='draft', tracking=True, readonly=True)
    charge_amount = fields.Float('Charge',
                                 states={'draft': [('readonly', False)]}, tracking=True)
    bank_deposit = fields.Many2one('res.partner.bank', 'Bank where the check is deposit/cashed',
                                   help='This bank indicate the name of the bank which the check is deposit and cashed')
    move_id = fields.Many2one('account.move', 'Account Entry', copy=False)
    move_ids = fields.One2many('account.move.line', 'collection_id', string='Journal Items', readonly=True)

    @api.onchange('property_id')
    def get_spa(self):
        if self.property_id:
            sale_orders = self.env['sale.order'].search(
                [('property_id', '=', self.property_id.id), ('asset_project_id', '=', self.asset_project_id.id),
                 ('state', 'not in', ['draft', 'cancel', 'rejected'])])
            if sale_orders:
                self.sale_id = sale_orders[0].id
            else:
                self.sale_id = False
        else:
            self.sale_id = False

    def submit_accounts_verification(self):
        for rec in self:
            user = self.env.user
            if user.receipt_confirmation_limit:
                total = 0
                total2 = 0
                for line in user.receipts_confirmed_ids:
                    total+= line.amount
                for line1 in rec.collection_line:
                    total2+= line1.amount
                total_to_confirm = total + total2
                if total_to_confirm > user.receipt_confirmation_limit:
                    raise ValidationError('Your amount limit exceed from validation limit, please contact administrator')
            for line in rec.collection_line:
                line.submit_accounts_verification()
            if not rec.number or rec.number == '/':
                number = self.env['ir.sequence'].next_by_code('account.voucher.collection')
                self.write({'number': number})

            rec.write({'state': 'under_accounts_verification'})
        return True

    # @api.depends('booking_id')
    # def get_spa(self):
    #     for rec in self:
    #         if rec.booking_id:
    #             spa_ids = rec.env['sale.order'].search([('booking_id','=', rec.booking_id.id)])
    #             if spa_ids:
    #                 rec.sale_id = spa_ids[0].id

    @api.onchange('asset_project_id')
    def onchange_asset_project_id(self):
        property_ids = self.env['account.asset.asset'].search(
            [('parent_id', '=', self.asset_project_id.id)])
        return {'domain': {'property_id': [('id', 'in', property_ids.ids)]}}

    @api.model
    def get_old_project_properties(self):
        mpp = self.env['account.voucher.collection'].search([])
        for rec in mpp:
            if rec.property_id or rec.asset_project_id:
                for line in rec.collection_line:
                    line.asset_project_id = rec.asset_project_id.id
                    line.property_id = rec.property_id.id

    def action_collect(self):
        for collect in self:
            if not collect.number or collect.number == '/':
                number = self.env['ir.sequence'].next_by_code('account.voucher.collection')
                self.write({'number': number})
            for line in collect.collection_line:
                if line.chk:
                    line.action_create_sequence()
                    line.button_collected()
                else:
                    # amount = line.amount * (line.payment_type in ('outbound', 'transfer') and 1 or -1)
                    # line._create_payment_entry(amount)
                    line.button_collected()
            # if not collect.number or collect.number == '/':
            #     number = self.env['ir.sequence'].next_by_code('account.voucher.collection')
            #     self.write({'number': number})

            collect.write({'state': 'collected'})
            # END TRA

        # self.action_move_line_create()

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

    collection_id = fields.Many2one('account.voucher.collection', 'Customer Payments Multi')


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    collection_id = fields.Many2one("account.voucher.collection", 'Collection')
