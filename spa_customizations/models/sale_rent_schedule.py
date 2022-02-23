# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from datetime import datetime, timedelta, date

import logging
_logger = logging.getLogger(__name__)


class SaleRentSchedule(models.Model):
    _name = "sale.rent.schedule"
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin', 'sequence.mixin']
    _description = 'Sale Rent Schedule'

    # @api.depends('partner_id','partner_id.nationality_id')
    # def _compute_nationality(self):
    #     for rec in self:
    #         rec.nationality_id = rec.partner_id.nationality_id.id

    # @api.depends('sale_id','sale_id.tag_ids')
    # def _compute_tags(self):
    #     for rec in self:
    #         rec.tag_ids = [(6, 0, rec.sale_id.tag_ids.ids)]

    @api.depends('sale_id','sale_id.receivable_status_id')
    def _compute_status(self):
        for rec in self:
            rec.receivable_status_id = rec.sale_id.receivable_status_id.id

    # tag_ids = fields.Many2many('crm.lead.tag', 'sale_rent_tag_rel', 'rent_id', 'tag_id', string='Tags', help="Classify and analyze your lead/opportunity categories like: Training, Service", compute='_compute_tags', store=True)
    # nationality_id = fields.Many2one('res.country', readonly=True, compute='_compute_nationality', store=True)
    receivable_status_id = fields.Many2one('receivable.status', 'Receivable Status', compute='_compute_status', store=True)
    note = fields.Text(
        string='Notes',
        help='Notes.', tracking=True)
    company_id = fields.Many2one('res.company',
        string='Company',
        default=lambda self: self.env['res.company']._company_default_get(
            'sale.rent.schedule'))
    currency_id = fields.Many2one('res.currency',
        related='company_id.currency_id',
        string='Currency',
        required=True)
    start_date = fields.Date(
        string='Due Date',
        required=True,
        help='Start Date.', tracking=True)

    property_id = fields.Many2one('account.asset.asset',
        string='Property',
        help='Property Name.', tracking=True)
    asset_property_id = fields.Many2one('account.asset.asset',
        string='Project',
        help='Property Name.', tracking=True)

    booking_id = fields.Many2one('sale.order',
        string='Booking',
        help='Booking Name.', tracking=True)
    sale_id = fields.Many2one('sale.order', string='Sale', help='Sale Order Name.', tracking=True)
    move_check = fields.Boolean(
        string='Posted', store=True, compute='calculate_paid_posted', tracking=True)
    paid = fields.Boolean(
        string='Paid', store=True, compute='calculate_paid_posted',
        help="True if this rent is paid by tenant", tracking=True)
    invc_id = fields.Many2one('account.move',
        string='Invoice', tracking=True)
    inv = fields.Boolean(
        string='Invoiced?', tracking=True)
    pen_amt = fields.Float(
        string='Pending Amount',
        help='Pending Ammount.', tracking=True
        )
    is_readonly = fields.Boolean(
        string='Readonly')
    sequence = fields.Integer('Serial No.', compute='_get_line_numbers', tracking=True)
    # sequence = fields.Integer('Serial No.',  tracking=True)
    calculation = fields.Selection([('balance', 'Balance'),('percent', 'Percentage'),('fixed', 'Fixed Amount')]
                                   ,string='Calculation', tracking=True)
    value = fields.Float(string='Value/Percent(%)', tracking=True)
    post = fields.Float(string='Post', tracking=True)
    sale_type = fields.Selection([
        ('samana_sale', 'Samana Sale'),
        ('investor_sale', 'Investor Sale'),
    ], string='Sale Type', required=True, default='samana_sale', tracking=True)

    name = fields.Char(related='partner_id.name', string='Name', tracking=True)
    partner_id = fields.Many2one('res.partner', string='Customer', compute='get_partner_info', store=True, tracking=True)
    mobile = fields.Char(string='Mobile', compute='get_partner_info')
    receipt_date = fields.Date(compute='compute_pending_balance', store=True, string='Receipt Date', tracking=True)
    delay_days = fields.Integer(compute='get_delay_days', store=True, string='Delay Days', tracking=True)
    surcharge = fields.Float(string='Surcharge', tracking=True)
    receipt_total = fields.Float(compute='compute_pending_balance', store=True, string='Received Amount', tracking=True)
    related_receipts_ids = fields.Many2many('account.payment', 'related_receipts_pdc_rel','installment_id','pdc_id', string='Related PDCs')
    installment_status = fields.Selection([('paid', 'Paid'),('unpaid', 'Unpaid'),
                                           ('partially_paid', 'Partially Paid'),
                                           ('pdc_secured', 'PDC Secured'),
                                           ('default', 'Default'),('cancel', 'Cancel')],
                                            string='Installment Status', default="unpaid",
                                            compute='calculate_pen_amt', store=True, tracking=True)
    receipts_ids = fields.One2many(
        'account.payment','schedule_id',
        string='Receipts', tracking=True)
    invoice_ids = fields.One2many('account.move', 'schedule_id', string='Invoices')
    state = fields.Selection(
        [('draft', 'Draft'),  # ('confirm_booking', 'Confirm Booking'),
         ('confirm', 'Confirmed'),
         ('cancel', 'Cancel')],
        string='Status', default='draft', tracking=True)
    amount_without_vat = fields.Float('Amount without VAT')
    vat_id = fields.Many2one('account.tax','VAT(%)')
    vat_amount = fields.Float(compute='get_vat_amount', store=True, string='VAT Amount')
    installment_inc_vat_amount = fields.Float(compute='get_installment_vat_amount', store=True
                                              , string='Installment Amount Including VAT')
    amount = fields.Monetary(
        string='Installment Amount Including Vat',
        default=0.0,
        compute='get_installment_vat_amount',store=True,
        currency_field='currency_id')

    state_spa = fields.Selection([
        ('draft', 'Draft'),
        ('under_discount_approval', 'Under Approval'),
        ('tentative_booking', 'Tentative Booking'),
        ('review', 'Under Review'),
        ('under_cancellation', 'Booking Under Cancellation'),
        ('confirm_spa', 'Confirmed for SPA'),
        # ('approved', 'Approved'),
        ('booking_rejected', 'Rejected'),
        ('booking_cancel', 'Cancel'),

        ('spa_draft', 'Unconfirmed SPA'),
        # ('under_legal_review_print', 'Under Legal Review for Print'),
        # ('under_acc_verification_print', 'Under Accounts Verification for Print'),
        # ('under_confirmation_print', 'Under Confirmation for Print'),
        # ('unconfirmed_ok_for_print', 'Unconfirmed SPA OK for Print'),
        ('under_legal_review', 'Under Legal Review'),
        ('under_accounts_verification', 'Under Accounts Verification'),
        ('under_approval', 'Under Approval'),
        # ('under_spa_termination', 'Under SPA Termination'),
        # ('under_termination', 'Under Termination'),
        ('sale', 'Approved SPA'),
        ('sent', 'Quotation Sent'),
        ('refund_cancellation', 'Refund Cancellation'),
        ('rejected', 'Rejected'),
        ('under_sd_admin_review', 'Under SD Admin Review'),
        ('paid', 'Approved SPA - Paid'),
        ('done', 'Locked'),
        ('cancel', 'Cancelled'),
    ], string='Status', readonly=True,related='sale_id.state')


    @api.depends('installment_status')
    def calculate_paid_posted(self):
        for rec in self:
            if rec.installment_status == 'paid':
                rec.move_check = True
                rec.paid = True
            else:
                rec.move_check = False
                rec.paid = False

    @api.depends('vat_id','amount_without_vat')
    def get_vat_amount(self):
        for rec in self:
            rec.vat_amount = rec.amount_without_vat * (rec.vat_id.amount / 100)

    @api.model
    def map_amount_to_copy(self):
        srs = self.env['sale.rent.schedule'].search([])
        for rec in srs:
            rec.amount_without_vat = rec.amount

    @api.model
    def map_invc_invoice_ids(self):
        srs = self.env['sale.rent.schedule'].search([('state','=','confirm')])
        count=0
        print(len(srs))
        for rec in srs:
            if not rec.invoice_ids and rec.invc_id:
                rec.invoice_ids = [(6, 0, rec.invc_id.ids)]
                count+=1
                print(count)

    @api.model
    def old_installment_vat_amount(self):
        srs = self.env['sale.rent.schedule'].search([])
        for rec in srs:
            rec.installment_inc_vat_amount = rec.amount_without_vat + rec.vat_amount
            rec.amount = rec.amount_without_vat + rec.vat_amount

    @api.depends('vat_amount','amount_without_vat')
    def get_installment_vat_amount(self):
        for rec in self:
            rec.installment_inc_vat_amount = rec.amount_without_vat + rec.vat_amount
            rec.amount = rec.amount_without_vat + rec.vat_amount

    @api.depends('start_date','receipt_date','receipt_total','amount')
    def get_delay_days(self):
        # srs = self.env['sale.rent.schedule'].search([])
        for rec in self:
            due_date = False
            receipt_date = False
            current_date = fields.Date.today()
            if rec.start_date:
                # due_date = datetime.strptime(rec.start_date, "%Y-%m-%d").date()
                due_date = rec.start_date
            if rec.receipt_date:
                receipt_date = rec.receipt_date
                # receipt_date = datetime.strptime(rec.receipt_date, "%Y-%m-%d").date()
            if rec.start_date and rec.start_date <= current_date:
                pen_amt = round(rec.amount, 2) - rec.receipt_total
                rec.update({'pen_amt': pen_amt})
            else:
                rec.update({'pen_amt': 0.0})
            if rec.start_date and current_date and rec.start_date <= current_date and rec.receipt_total < rec.amount:
                delay = due_date -current_date
                rec.update({'delay_days': delay.days})
                # rec.delay_days = delay.days
            elif rec.start_date and current_date and receipt_date  and rec.receipt_total >= rec.amount and rec.paid == True:
                delay = receipt_date - due_date
                rec.update({'delay_days': delay.days})
                # rec.delay_days = delay.days
            else:
                rec.update({'delay_days': 0})

    @api.model
    def get_overdue_amount(self):
        srs = self.env['sale.rent.schedule'].search([])
        for rec in srs:
            due_date = False
            receipt_date = False
            current_date = fields.Date.today()
            if rec.start_date:
                due_date = rec.start_date
            if rec.receipt_date:
                receipt_date = rec.receipt_date
            if rec.start_date <= current_date:
                pen_amt = round(rec.amount, 2) - rec.receipt_total
                rec.update({'pen_amt': pen_amt})
            else:
                rec.update({'pen_amt': 0.0})
            if rec.start_date and current_date and rec.start_date <= current_date and rec.receipt_total < rec.amount:
                delay = due_date - current_date
                rec.update({'delay_days': delay.days})
            elif rec.start_date and current_date and receipt_date  and rec.receipt_total >= rec.amount and rec.paid == True:
                delay = receipt_date - due_date
                rec.update({'delay_days': delay.days})
            else:
                rec.update({'delay_days': 0})

    def calculate_payments(self):
        for rec in self:
            pen_amt = 0.0
            inv_list = []
            if rec.invoice_ids:
                for inv in rec.invoice_ids:
                    if inv.state in ['posted','paid']:
                        inv_list.append(inv.id)
            elif not rec.invoice_ids and rec.invc_id:
                if rec.invc_id.state in ['posted','paid']:
                    inv_list.append(rec.invc_id.id)
            else:
                rec.update({'receipts_ids':[(6, 0, [])]})

            payment_ids = rec.env['account.payment'].search([('reconciled_invoice_ids', 'in', inv_list)], order='date desc')
            rec.update({'receipts_ids':[(6, 0, payment_ids.ids)]})


    def action_cancel(self):
        self.state = 'cancel'
        self.installment_status = 'cancel'

    def action_default(self):
        print('test')
        # self.installment_status = 'default'

    @api.depends('sale_id')
    def get_partner_info(self):
        for rec in self:
            if rec.sale_id:
                rec.partner_id = rec.sale_id.partner_id.id
                rec.mobile = rec.sale_id.partner_id.mobile
                rec.update({
                    'partner_id': rec.sale_id.partner_id.id,
                    'mobile': rec.sale_id.partner_id.mobile,
                })
            else:
                rec.partner_id = False
                rec.mobile = False

    @api.model
    def get_info_from_spa(self):
        lines = self.env['sale.rent.schedule'].search([('state','in',['confirm','draft'])])
        for rec in lines:
            if rec.sale_id:
                rec.partner_id = rec.sale_id.partner_id.id
                rec.mobile = rec.sale_id.partner_id.mobile
                rec.update({
                    'property_id': rec.sale_id.property_id.id,
                    'partner_id': rec.sale_id.partner_id.id,
                    'mobile': rec.sale_id.partner_id.mobile,
                    'asset_property_id': rec.sale_id.asset_project_id.id
                })

    def get_sale_type(self):
        lines = self.env['sale.rent.schedule'].search([('state','=','confirm')])
        for rec in lines:
            rec.sale_type = 'samana_sale'
            print(rec.id)

    @api.depends('receipt_total', 'amount', 'state','related_receipts_ids')
    def calculate_pen_amt(self):
        for rec in self:
            # rec.pen_amt = round(rec.amount, 2) - rec.receipt_total
            print("computethis")
            if not rec.receipt_total:
                rec.installment_status = 'unpaid'
            if rec.receipt_total >= rec.amount:
                rec.installment_status = 'paid'
            if rec.receipt_total and rec.receipt_total < rec.amount:
                rec.installment_status = 'partially_paid'
            if rec.state == 'cancel':
                rec.installment_status = 'cancel'
            if rec.related_receipts_ids:
                rec.installment_status = 'pdc_secured'

    def _get_line_numbers(self):
        for rec in self:
            if rec.sale_id:
                line_num = 0
                for line in rec.env['sale.rent.schedule'].search([('sale_id', '=', rec.sale_id.id)], order='start_date asc'):
                    line_num += 1
                    if line.id == rec.id:
                        break
                rec.sequence = line_num
            else:
                rec.sequence = 0


    def get_invloice_lines(self):
        """TO GET THE INVOICE LINES"""
        for rec in self:
            inv_line = {
                'name': _('Installment Date '+ str(rec.start_date)),
                'price_unit': rec.amount_without_vat or 0.00,
                'quantity': 1,
                'property_id': rec.property_id.id,
                'asset_project_id': rec.asset_property_id.id,
                'tax_ids': [(6, 0, rec.vat_id.ids)],
                'account_id': rec.sale_id.asset_project_id.income_acc_id.id or False,
            }
            return [(0, 0, inv_line)]

    def create_invoice_auto(self):
        inv_obj = self.env['account.move']
        sale_rent = self.env['sale.rent.schedule'].search([('start_date','<=',datetime.now().date()),('inv','!=',True),('state','in',['confirm'])])
        print(len(sale_rent))
        for rec in sale_rent:
            if rec.sale_id:
                inv_line_values = rec.get_invloice_lines()
                inv_values = {
                    'schedule_id':rec.id,
                    'partner_id': rec.sale_id.partner_id.id or False,
                    'move_type': 'out_invoice',
                    'asset_project_id': rec.asset_property_id.id if rec.asset_property_id else rec.sale_id.asset_project_id.id or False,
                    'property_id': rec.sale_id.property_id.id or False,
                    'invoice_date': rec.start_date or False,
                    'invoice_line_ids': inv_line_values,
                }
                print(rec.id)
                invoice_id = inv_obj.create(inv_values)
                invoice_id.action_post()
                rec.write({'invc_id': invoice_id.id, 'inv': True})
                rec.update({'invoice_ids': [(6, 0, invoice_id.ids)]})

    def create_invoice(self):
        for rec in self:
            inv_obj = rec.env['account.move']
            inv_line_values = rec.get_invloice_lines()
            inv_values = {
                'schedule_id':rec.id,
                'partner_id': rec.sale_id.partner_id.id or False,
                'move_type': 'out_invoice',
                'property_id': rec.property_id.id if rec.property_id else rec.sale_id.property_id.id or False,
                'asset_project_id': rec.asset_property_id.id if rec.asset_property_id else rec.sale_id.asset_project_id.id or False,
                'invoice_date': rec.start_date or False,
                'invoice_line_ids': inv_line_values,
            }
            invoice_id = inv_obj.create(inv_values)
            # invoice_id.action_invoice_open()
            rec.write({'invc_id': invoice_id.id, 'inv': True})
            rec.update({'invoice_ids': [(6, 0, invoice_id.ids)]})
            # inv_form_id = rec.env.ref('account.invoice_form').id

            return {
                # 'view_type': 'form',
                # 'view_id': inv_form_id,
                'view_mode': 'form',
                'res_model': 'account.move',
                'res_id': rec.invc_id.id,
                'type': 'ir.actions.act_window',
                'target': 'current',
            }

    def open_invoice(self):
        return {
            'view_id': self.env.ref('account.view_move_form').id,
            'view_mode': 'form',
            'res_model': 'account.move',
            'res_id': self.invc_id.id,
            'type': 'ir.actions.act_window',
            'target': 'current',
        }

    @api.depends('invoice_ids', 'invoice_ids.amount_total', 'invoice_ids.amount_residual')
    def compute_pending_balance(self):
        for rec in self:
            invoice_residual = 0
            invoice_total = 0
            for invoice in rec.invoice_ids:
                if invoice.state in ['posted','paid']:
                    invoice_total += invoice.amount_total
                    invoice_residual += invoice.amount_residual
                if invoice.state in ['draft']:
                    invoice_total += invoice.amount_total
                    invoice_residual += invoice.amount_total
            invoice_paid = invoice_total - invoice_residual
            if invoice_paid > -1 and invoice_paid < 0:
                invoice_paid = 0
            rec.receipt_total = invoice_paid
            inv_list = []
            for inv in rec.invoice_ids:
                if inv.state in ['posted', 'paid']:
                    inv_list.append(inv.id)

            payment_ids = rec.env['account.payment'].search([('reconciled_invoice_ids', 'in', inv_list)],
                                                            order='date desc')
            if payment_ids:
                rec.update({'receipt_date': payment_ids[0].date})
            else:
                rec.update({'receipt_date': False})


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    schedule_id = fields.Many2one('sale.rent.schedule', 'Schedule')