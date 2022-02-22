# -*- coding: utf-8 -*-
from odoo import _, api, fields, models
import time
import datetime
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from odoo.tools import float_is_zero, float_compare
from odoo.tools.safe_eval import safe_eval
from odoo import http


class AccountVoucherReplacement(models.Model):
    _name = 'account.voucher.replacement'
    _description = 'Account Voucher Replacement'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char('Name', readonly=True, default='/')
    mobile = fields.Char(related='partner_id.mobile', string="Mobile 1", store=True)
    phone = fields.Char(related='partner_id.phone', string="Phone", store=True)
    email = fields.Char(related='partner_id.email', string="Email", store=True)
    partner_id = fields.Many2one('res.partner', 'Customer ID')
    voucher_pending_ids = fields.Many2many('account.payment', 'replacement_receipts_rel', 'replacement_id', 'receipt_id', 'Pending PDCs')
    type = fields.Selection([
        ('payment','Payment'),
        ('receipt','Receipt'),
    ], 'Default Type', readonly=True, states={'draft':[('readonly',False)]})

    request_type = fields.Selection([
        ('replacement','PDC Replacement'),
        ('withdraw','PDC Withdraw'),
        ('hold','PDC Hold'),
    ], default='replacement', string='Request Type', required=True)

    submit_by = fields.Many2one('res.users', string='Submitted By')
    submit_date = fields.Date(string='Submit Date')
    approval_by = fields.Many2one('res.users', string='Approved By')
    approval_date = fields.Date(string='Approval Date')
    verified_by = fields.Many2one('res.users', string='Verified By')
    verify_date = fields.Date(string='Verify Date')

    move_ids = fields.Many2many('account.move.line', string='Journal Items')

    date = fields.Datetime('Date', default=time.strftime('%Y-%m-%d'),)
    voucher_ids = fields.Many2many('account.payment', string='Receipt &amp; Payments')
    company_id = fields.Many2one('res.company','Company', default=lambda self: self.env.user.company_id, tracking=True)

    contract_id = fields.Many2one('sale.order', 'SPA', readonly=True, states={'draft':[('readonly',False)]})
    contract_creation_date = fields.Date('Contract Creation Date', readonly=True, states={'draft':[('readonly',False)]})
    contract_signing_date = fields.Date('Contract Signing Date', readonly=True, states={'draft':[('readonly',False)]})
    contract_type = fields.Char('Contract Type', readonly=True, states={'draft':[('readonly',False)]})

    product_id = fields.Many2one('product.product', 'Product')
    total_amount_contract = fields.Float(compute='get_spa_detail', store=True, string='Total Amount of Contract')
    total_received = fields.Float(compute='get_spa_detail', store=True, string='Total Received')
    unmatured_pdc_amount = fields.Float(compute='get_spa_detail', store=True, string='Unmatured PDCs Amount')
    bounced_pdc_amount = fields.Float(compute='get_spa_detail', store=True, string='Bounced PDC Amount')
    balance_pending = fields.Float(compute='get_spa_detail', store=True, string='Balance Pending')

    account_remarks = fields.Text("Account Remarks", readonly=True)
    officer_remarks = fields.Text("Officer Remarks")
    total_charge = fields.Float(string='Total Document Charge')
    image =  fields.Binary("Image",
        help="This field holds the image used as avatar for this contact, limited to 1024x1024px")

    state = fields.Selection(
            [('draft','Draft'),
             ('under_accounts_review','Under Accounts Review'),
             ('under_verification','Under Verification'),
             ('under_approval','Under FC Approval'),
             ('under_ceo_approval','Under CEO Approval'),
             ('approved','Approved'),
             ('withdraw','Withdraw'),
             ('hold','Hold'),
             ('replaced','Replaced'),
             ('done','Done'),
             ('reject','Rejected'),
             ('cancel','Cancelled'),
            ], 'Status', readonly=True, default='draft', size=32, tracking=True)
    payment_term =  fields.Many2one('account.payment.term', 'Payment Term')
    receipt_ids = fields.Many2many('account.payment', 'replacement_all_receipts_rel', 'replacement_id', 'receipt_id', 'Pending PDCs')
    all_payments_and_receipts_ids = fields.Many2many('account.payment', 'replacement_payment_receipts_rel', 'replacement_id', 'receipt_id', 'Pending PDCs')
    # receipt_ids = fields.One2many('account.payment','replacement2_id','Receipts')
    pdc_receipt_ids = fields.Many2many('account.voucher.collection','replacement_pdcs_rel','replacement_id','pdcs_id','PDC Receipts')
    property_id = fields.Many2one('account.asset.asset', string='Property')
    asset_project_id = fields.Many2one('account.asset.asset', 'Project', domain="[('project', '=', True)]")
    # booking_id = fields.Many2one('crm.booking', 'Booking')
    sale_id = fields.Many2one('sale.order', 'SPA')
    rollback_state = fields.Char('Roll Back State')
    hold_date = fields.Date('Hold')
    pending_total = fields.Float('Pending Total')

    # @api.depends('booking_id')
    # def get_spa(self):
    #     for rec in self:
    #         if rec.booking_id:
    #             spa_ids = rec.env['sale.order'].search([('booking_id','=', rec.booking_id.id)])
    #             if spa_ids:
    #                 rec.sale_id = spa_ids[0].id

       
    def get_partner_ids(self, user_ids):
        if user_ids:
            anb =  str([user.partner_id.email for user in user_ids]).replace('[', '').replace(']', '')
            return anb.replace("'", '')

       
    def get_req_type(self, status):
        state = False
        if status:
            if status == 'replacement':
                state = 'PDC Replacement'
            elif status == 'withdraw':
                state = 'PDC Withdraw'
            elif status == 'hold':
                state = 'PDC Hold'
        return state

    @api.model
    def send_hold_withdraw_email(self,state):
        group = False
        if state == 'under_approval':
            group = self.env['res.groups'].search([('name','=','General Financial Manager')])
        if state == 'under_ceo_approval':
            group = self.env['res.groups'].search([('name','=','Chief Executive Officer')])
        for rec in group:
            if rec.users:
                email_template = rec.env.ref('account_voucher_replace.email_pdc_hold_withdraw')
                email_template.email_from = email_template.mail_server_id.name
                email_template.email_to = self.get_partner_ids(rec.users)
                email_template.send_mail(self.id, force_send=True)


       
    def get_url(self,record):
        action_id = record.env.ref('account_voucher_replace.action_account_voucher_replacement')
        # base_url = record.env['ir.config_parameter'].sudo().get_param('web.base.url') + '/schedule/?id=' + str(
        #     record.id)
        base_url = http.request.env['ir.config_parameter'].get_param('web.base.url') + '/web?id=' + str(
            record.id) + '&action=' + str(action_id.id) + '&' + 'model=' + record._name + '&' + 'view_type=form'\
        + '#'+ 'id=' + str(record.id) + '&action=' + str(action_id.id) + '&' + 'model=' + record._name + '&' +\
        'view_type=form'

        return base_url

    @api.depends('sale_id')
    def get_spa_detail(self):
        for rec in self:
            if rec.sale_id:
                rec.total_amount_contract  = rec.sale_id.amount_total
                rec.total_received  = rec.sale_id.total_receipts
                rec.unmatured_pdc_amount  = rec.sale_id.un_matured_pdcs
                rec.bounced_pdc_amount  = rec.sale_id.bounced_pdcs
                rec.balance_pending  = rec.sale_id.pending_balance

    @api.onchange('asset_project_id')
    def onchange_asset_project_id(self):
        property_ids = self.env['account.asset.asset'].search(
            [('parent_id', '=', self.asset_project_id.id)])
        return {'domain': {'property_id': [('id', 'in', property_ids.ids)]}}

    @api.onchange('partner_id')
    def onchange_partner_id(self):
        if self.partner_id:
            booking_ids = self.env['sale.order'].search(
                [('partner_id', '=', self.partner_id.id)])
            if booking_ids:
                property_ids = self.env['account.asset.asset'].search(
                    [('id', '=', booking_ids[0].property_id.id)])
                if property_ids:
                    self.property_id = property_ids[0].id
                    self.asset_project_id = property_ids[0].parent_id.id
                return {'domain': {'property_id': [('id', 'in', property_ids.ids)],
                                   'sale_id': [('id', 'in', booking_ids.ids)]}}
        else:
            self.sale_id = False
            self.property_id = False

    #    
    # def action_withdraw(self):
    #     for collect in self:
    #         for line in collect.collection_line:
    #             if line.chk:
    #                 line.check_outsourced()
    #             else:
    #                 line.post()
    #         if not collect.number or collect.number == '/':
    #             number = self.env['ir.sequence'].next_by_code('account.voucher.replacement')
    #             self.write({'number': number})
    #         collect.write({'state': 'collected'})
    #     return True

       
    def submit_to_accounts(self):
        self.write({'state': 'under_accounts_review',
                    'submit_by': self.env.user.id,
                    'submit_date': datetime.now().strftime('%Y-%m-%d')})

       
    def action_reject(self):
        self.write({'rollback_state': self.state})
        self.write({'state': 'reject'})

       
    def action_approve(self):
        self.write({'state': 'approved',
                    'approval_by': self.env.user.id,
                    'approval_date': datetime.now().strftime('%Y-%m-%d')})

       
    def action_review(self):
        self.write({'state': 'under_verification'})

       
    def action_verify(self):
        if self.request_type == 'hold':
            self.write({'state': 'under_ceo_approval',
                    'verified_by': self.env.user.id,
                    'verify_date': datetime.now().strftime('%Y-%m-%d')})
            self.send_hold_withdraw_email(self.state)
        else:
            self.write({'state': 'under_approval',
                    'verified_by': self.env.user.id,
                    'verify_date': datetime.now().strftime('%Y-%m-%d')})
            self.send_hold_withdraw_email(self.state)

       
    def action_ceo_approved(self):
        self.write({'state': 'approved'})

       
    def action_ceo_rejected(self):
        self.write({'rollback_state': self.state})
        self.write({'state': 'reject'})

       
    def action_pdc_withdraw(self):
        for rec in self:
            for line in rec.voucher_pending_ids:
                if line.chk:
                    line.check_outsourced()
            if not rec.name or rec.name == '/':
                number = self.env['ir.sequence'].next_by_code('account.voucher.replacement')
                self.write({'name': number})
            rec.write({'state': 'done'})
        return True


       
    def action_pdc_hold(self):
        for rec in self:
            if not rec.hold_date:
                rec.write({'hold_date': datetime.now().date()})
            for line in rec.voucher_pending_ids:
                if line.chk:
                    line.button_hold()
                    line.write({'hold_date': rec.hold_date})
            if not rec.name or rec.name == '/':
                number = self.env['ir.sequence'].next_by_code('account.voucher.replacement')
                self.write({'name': number})
            rec.write({'state': 'done'})
        return True

       
    def action_pdc_replaced(self):
        for rec in self:
            for line in rec.voucher_pending_ids:
                if line.chk:
                    line.check_replaced()
            if not rec.name or rec.name == '/':
                number = self.env['ir.sequence'].next_by_code('account.voucher.replacement')
                self.write({'name': number})
            rec.write({'state': 'done'})
        return True

    @api.model
    def create(self, vals):
        if vals.get('name', _('/')) == _('/'):
            vals['name'] = self.env['ir.sequence'].next_by_code('account.voucher.replacement')
        return super(AccountVoucherReplacement, self).create(vals)

       
    def action_set_to_draft(self):
        self.write({'state': 'draft'})

       
    def action_rool_back(self):
        if self.rollback_state:
            self.write({'state': self.rollback_state})
        else:
            raise ValidationError("No roll back state stored")


       
    def action_cancel(self):
        # for line in self.collection_line:
        #     if line.state == 'draft' or line.state == 'draft':
        #         line.action_draft_to_cancel()
        #     else:
        #         line.cancel()
        self.write({'state': 'cancel'})

       
    def action_refresh(self):
        pending_domain =[]
        pending_total = 0.0
        if self.partner_id:
            pending_domain.append(('chk','=',True))
            pending_domain.append(('payment_type','=','inbound'))
            pending_domain.append(('state','=','collected'))
            pending_domain.append(('partner_id', '=', self.partner_id.id))
        if self.spa_id:
            pending_domain.append(('spa_id', '=', self.spa_id.id))
        if self.property_id:
            pending_domain.append(('property_id', '=', self.property_id.id))
        if self.sale_id:
            pending_domain.append(('spa_id', '=', self.sale_id.id))
        collected_receipt_ids = self.env['account.payment'].search(pending_domain)
        all_receipt_and_payments_ids = self.env['account.payment'].search([('chk','=',True),('partner_id', '=', self.partner_id.id)])
        all_receipt_ids = self.env['account.payment'].search([('chk','=',True),('partner_id', '=', self.partner_id.id),('payment_type','=','inbound')])
        pdc_receipt_ids = self.env['account.voucher.collection'].search([('partner_id', '=', self.partner_id.id)])
        for line in collected_receipt_ids:
            pending_total += line.amount
        self.pending_total = pending_total
        self.voucher_pending_ids = [[6, 0, collected_receipt_ids.ids]]
        self.pdc_receipt_ids = [[6, 0, pdc_receipt_ids.ids]]
        self.receipt_ids = [[6, 0, all_receipt_ids.ids]]
        self.all_payments_and_receipts_ids = [[6, 0, all_receipt_and_payments_ids.ids]]

