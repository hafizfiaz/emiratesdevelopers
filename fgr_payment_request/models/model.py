# -*- coding: utf-8 -*-
from odoo import fields, models, api, _

import time
from datetime import datetime
from datetime import date
from datetime import timedelta
from odoo.exceptions import UserError
from odoo.addons.mail.models import mail_template
from odoo.addons.mail.models.mail_render_mixin import jinja_template_env, jinja_safe_template_env
from dateutil.relativedelta import relativedelta
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    project_id = fields.Many2one(
        'project.project', 'Task Project', readonly=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]},
        help='Select a non billable project on which tasks can be created.')
    project_ids = fields.Many2many('project.project', compute="_compute_project_ids", string='Task Projects', copy=False, groups="project.group_project_user", help="Projects used in this sales order.")
    partner_invoice_id = fields.Many2one(
        'res.partner', string='Invoice Address',
        readonly=True, required=False,
        states={'draft': [('readonly', False)], 'sent': [('readonly', False)], 'sale': [('readonly', False)]},
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]",)
    partner_shipping_id = fields.Many2one(
        'res.partner', string='Delivery Address', readonly=True, required=False,
        states={'draft': [('readonly', False)], 'sent': [('readonly', False)], 'sale': [('readonly', False)]},
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]",)

class AccountAssetAsset(models.Model):
    _inherit = "account.asset.asset"

    fgr_agreement = fields.Text('FGR Agreement')


class FGRPaymentRequest(models.Model):
    _name = 'fgr.payment.request'
    _description = 'FGR Payment Request'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Subject', tracking=True)
    spa_id = fields.Many2one('sale.order', string='SPA/Booking', required=True, tracking=True)
    related_booking_id = fields.Many2one('sale.order', compute='get_spa_details', store=True, string='Related Booking',
                                         tracking=True)
    partner_id = fields.Many2one('res.partner', compute='get_spa_details', store=True, string='Customer Name',
                                 tracking=True)
    mobile = fields.Char(string='Mobile', compute='get_spa_details', store=True, tracking=True)
    email = fields.Char(string='Email', compute='get_spa_details', store=True, tracking=True)
    joined_partner_id = fields.Many2many('res.partner', 'joined_partner_fgr_rel', 'fgr_id', 'join_id',
                                         string="Joined Partner's", compute='get_spa_details', store=True,
                                         tracking=True)
    asset_project_id = fields.Many2one('account.asset.asset', 'Project', domain="[('project', '=', True)]",
                                       compute='get_spa_details', store=True, tracking=True)
    property_id = fields.Many2one('account.asset.asset', string='Property', compute='get_spa_details', store=True,
                                  tracking=True)
    sale_date = fields.Datetime('Sale Date', compute='get_spa_details', store=True, tracking=True)
    agent_ref = fields.Boolean(string='Agent Ref.', compute='get_spa_details', store=True, tracking=True)
    agent_id = fields.Many2one('res.partner', string='Agent Name', compute='get_spa_details', store=True,
                               tracking=True)
    booking_date = fields.Datetime('Booking Date', compute='get_spa_details', store=True, tracking=True)
    property_price = fields.Float('Property Price', compute='get_spa_details', store=True, tracking=True)
    agent_discount = fields.Float(string='Agent Discount', compute='get_spa_details', store=True,
                                  tracking=True)
    booking_discount = fields.Float(string='Booking Discount', compute='get_spa_details', store=True,
                                    tracking=True)
    discount_value = fields.Float(string='Total Discount Amount', compute='get_spa_details', store=True,
                                  tracking=True)
    discount_value_perc = fields.Float(string='Total Discount (%)', compute='get_spa_details', store=True,
                                       tracking=True)
    price = fields.Float(string='Property Sale Price', compute='get_spa_details', store=True,
                         tracking=True)
    oqood_fee = fields.Float(string='Oqood Fee charge', compute='get_spa_details', store=True,
                             tracking=True)
    admin_fee = fields.Float(string='Admin Fee charge', compute='get_spa_details', store=True,
                             tracking=True)
    total_spa_value = fields.Float('Total SPA Value', compute='get_spa_details', store=True,
                                   tracking=True)
    total_due = fields.Float('Total Due Amount', compute='get_spa_details', store=True, tracking=True)
    matured_pdcs = fields.Float(string='Amount Received (Realized Collections)', compute='get_spa_details', store=True,
                                tracking=True)
    balance_due_collection = fields.Float('Balance Due Collection', compute='get_spa_details', store=True,
                                          tracking=True)
    fgr_detail_ids = fields.One2many('fgr.details', 'fgr_payment_request_id', 'FGR Details')
    invoice_ids = fields.Many2many('account.move', 'fgr_invoice_rel', 'sale_id', 'invoice_id',
                                   string='FGR Invoices', tracking=True, compute='compute_invoices')
    fgr_total_payment = fields.Float('Total Rent', compute="totalfgramnt")
    fgr_total_payment_perc = fields.Float('Total Rent Percentage', compute="totalfgramntperc")
    agreement_start_date = fields.Date('Agreement Start Date')
    agreement_end_date = fields.Date('Agreement End Date')
    no_of_installment = fields.Integer('No of Installments')
    difference = fields.Char(compute='get_dates_difference', string='Duration')
    interval = fields.Selection(
        [('monthly', 'Monthly'), ('quarterly', 'Quarterly'), ('biannually', 'Biannually'), ('yearly', 'Yearly')],
        string="Interval")
    fgr_agreement = fields.Text('FGR Agreement')
    custom_plan = fields.Boolean('Custom FGR Payment Plan')
    installment_amount = fields.Float('Installment Amount', compute='get_installment_amount', store=True)
    remarks = fields.Text('Remarks')
    annual_rent = fields.Float('Annual Rent', compute="annaualrentamnt")
    annual_rent_perc = fields.Float('Annual Rent Percentage')
    total_years = fields.Integer('No. of Years')
    installment_date = fields.Date('Installment Start Date')

    # inv_total = fields.Float(string='Invoice Total', compute='compute_invoices')
    # total_received = fields.Float(string='Total Received', compute='compute_invoices')

    total_fgr_requested = fields.Float('Total FGR payment Requested', compute='compute_invoices', store=True,
                                       tracking=True)
    total_fgr_invoiced = fields.Float('Total FGR Invoiced', compute='compute_invoices', store=True,
                                      tracking=True)
    total_fgr_paid = fields.Float('Total FGR Paid', compute='compute_invoices', store=True, tracking=True)
    total_fgr_pending = fields.Float('Total FGR Payment Pending', compute='compute_fgr_pending', store=True,
                                     tracking=True)
    payment_ids = fields.Many2many('account.payment', 'fgr_payment_rel', 'sale_id', 'payment_id',
                                   domain=[('payment_type', '=', 'outbound'), ('state', 'not in',
                                                                               ['draft', 'under_approval',
                                                                                'under_review', 'cancelled',
                                                                                'rejected'])],
                                   string='Payments', tracking=True, compute='compute_invoices',
                                   store=False)
    receipt_ids = fields.Many2many('account.payment', 'fgr_receipt_rel', 'sale_id', 'receipt_id',
                                   string='Receipts', tracking=True,
                                   domain=[('payment_type', '=', 'inbound'), (
                                       'state', 'not in', ['draft', 'refused', 'outsourced', 'cancelled', 'rejected'])],
                                   compute='compute_receipts', store=False)
    # @api.multi
    def name_get(self):
        return [(rpb.id, "%s %s %s" % (rpb.partner_id.name, rpb.asset_project_id.name, rpb.property_id.name)) for rpb in self]

    @api.depends('receipt_ids', 'receipt_ids.amount', 'receipt_ids.state')
    def _compute_receipts_total(self):
        for rec in self:
            total = 0
            for line in rec.receipt_ids:
                if line.state not in ['draft,refused,outsourced,cancelled,rejected']:
                    total += line.amount
            rec.receipt_total = total

    receipt_total = fields.Float('Receipt Total', compute='_compute_receipts_total', store=True)

    def compute_receipts(self):
        for rec in self:
            receipt_ids = rec.env['account.payment'].search([('partner_id', '=', rec.partner_id.id),
                                                             ('property_id', '=', rec.property_id.id),
                                                             ('payment_type', '=', 'inbound'),
                                                             ('state', 'not in',
                                                              ['draft', 'refused', 'outsourced', 'cancelled',
                                                               'rejected'])])
            rec.receipt_ids = [(6, 0, receipt_ids.ids)]

    @api.model
    def compute_old_payments(self):
        payment_ids = self.env['fgr.payment.request'].search([])
        for rec in payment_ids:
            if rec.fgr_detail_ids:
                inv_list = []
                for line in rec.fgr_detail_ids:
                    if line.inv:
                        inv_list.append(line.invc_id.id)
                        for inv in line.invc_ids:
                            inv_list.append(inv.id)
                payment_ids = rec.env['account.payment'].search([('reconciled_invoice_ids', 'in', inv_list),('state', 'not in', ['cancelled','rejected'])])
                rec.payment_ids = [(6, 0, payment_ids.ids)]

    # 
    # def compute_payments(self):
    #     for rec in self:
    #         payment_ids = rec.env['account.payment'].search([('partner_id', '=', rec.partner_id.id),
    #                                                          ('property_id', '=', rec.property_id.id),
    #                                                          ('payment_type', '=', 'outbound'),
    #                                                          ('state', 'not in',
    #                                                           ['draft', 'under_approval', 'under_review', 'cancelled',
    #                                                            'rejected'])])
    #         rec.payment_ids = [(6, 0, payment_ids.ids)]

    @api.depends('fgr_detail_ids', 'fgr_detail_ids.invc_id', 'fgr_detail_ids.invc_id.amount_residual', 'fgr_detail_ids.invc_ids', 'fgr_detail_ids.invc_ids.amount_residual')
    def compute_invoices(self):
        for rec in self:
            if rec.fgr_detail_ids:
                inv_list = []
                inv_total = 0
                total = 0
                requested = 0
                for line in rec.fgr_detail_ids:
                    requested += line.amount
                    if line.inv:
                        if not line.invc_ids:
                            inv_total += line.invc_id.amount_total
                            total += line.invc_id.amount_total - line.invc_id.amount_residual
                            inv_list.append(line.invc_id.id)
                        else:
                            for r in line.invc_ids:
                                inv_total += r.amount_total
                                total += r.amount_total - r.amount_residual
                                inv_list.append(r.id)
                payment_ids = rec.env['account.payment'].search([('reconciled_invoice_ids', 'in', inv_list),('state', 'not in', ['cancelled','rejected'])])
                rec.payment_ids = [(6, 0, payment_ids.ids)]
                rec.invoice_ids = [(6, 0, inv_list)]
                rec.total_fgr_paid = total
                # rec.inv_total = inv_total
                rec.total_fgr_invoiced = inv_total
                rec.total_fgr_requested = requested
            else:
                rec.payment_ids = []
                rec.invoice_ids = []
                rec.total_fgr_paid = 0
                # rec.inv_total = inv_total
                rec.total_fgr_invoiced = 0
                rec.total_fgr_requested = 0

    @api.depends('total_fgr_requested', 'total_fgr_paid')
    def compute_fgr_pending(self):
        for rec in self:
            rec.total_fgr_pending = rec.total_fgr_requested - rec.total_fgr_paid

    @api.depends('annual_rent_perc', 'price')
    def annaualrentamnt(self):
        for rec in self:
            annual_rent = 0
            if rec.annual_rent_perc:
                annual_rent = rec.annual_rent_perc * rec.price / 100
            rec.annual_rent = annual_rent

    @api.model
    def cron_annual_rent(self):
        fgrr = self.env['fgr.payment.request'].search([])
        for rec in fgrr:
            annual_rent = 0
            if rec.annual_rent_perc:
                rec.annual_rent = rec.annual_rent_perc * rec.price / 100
            rec.annual_rent = annual_rent

    @api.depends('total_years', 'annual_rent')
    def totalfgramnt(self):
        for rec in self:
            fgr_total_payment = 0
            if rec.total_years and rec.annual_rent:
                fgr_total_payment = rec.total_years * rec.annual_rent
            rec.fgr_total_payment = fgr_total_payment

    @api.depends('total_years', 'annual_rent_perc')
    def totalfgramntperc(self):
        for rec in self:
            fgr_total_payment_perc = 0
            if rec.total_years and rec.annual_rent_perc:
                fgr_total_payment_perc = rec.total_years * rec.annual_rent_perc
            rec.fgr_total_payment_perc = fgr_total_payment_perc

    @api.depends('fgr_total_payment', 'no_of_installment')
    def get_installment_amount(self):
        for rec in self:
            installment_amount = 0
            if rec.no_of_installment:
                installment_amount = rec.fgr_total_payment / rec.no_of_installment
            rec.installment_amount = installment_amount

    #
    # def write(self, vals):
    #     res = super(FGRPaymentRequest, self).write(vals)
    #     total_pp = 0.0
    #     if self.fgr_detail_ids:
    #         for line in self.fgr_detail_ids:
    #             total_pp += line.amount
    #         if round(total_pp) >= round(self.fgr_total_payment) and round(total_pp) <= round(self.fgr_total_payment + 1):
    #             pass
    #         else:
    #             raise UserError(_("FGR Schedule total is not equal to the FGR Total payment"))
    #     return res

    def get_related_attachments(self):
        for rec in self:
            attachments = rec.env['ir.attachment'].search(
                [('res_model', '=', 'fgr.payment.request'), ('res_id', '=', rec.id)])
            booking_att = rec.env['ir.attachment'].search(
                [('res_model', '=', 'sale.order'), ('res_id', '=', rec.related_booking_id.id)])
            so_att = rec.env['ir.attachment'].search([('res_model', '=', 'sale.order'), ('res_id', '=', rec.spa_id.id)])
            tree_id = self.env.ref('sd_settle_and_attachment_req.view_attachment_tree_on_model').id
            # print(attachments.ids)
            all_attach = booking_att.ids + so_att.ids + attachments.ids

            return {
                'name': _('Attachments'),
                'view_mode': 'tree',
                'view_id': tree_id,
                'res_model': 'ir.attachment',
                'type': 'ir.actions.act_window',
                'domain': [('id', 'in', all_attach)],
                'context': {
                    'create': False,
                    'edit': False
                },
            }

    def create_agreement_schedule(self):
        if not self.installment_date or not self.agreement_end_date:
            raise UserError(_("Please define duration first."))
        if self.fgr_detail_ids:
            raise UserError('Schedule already there please delete or unlink it first')
        if not self.fgr_total_payment:
            raise UserError('Please set FGR Total Payment')
        new_date = self.installment_date
        end_date = self.agreement_end_date
        difference = relativedelta(self.agreement_end_date + relativedelta(days=1), self.installment_date)
        months = difference.months
        years = difference.years
        if years:
            months = months + (years * 12)

        iteration = 1
        if self.interval == 'monthly':
            iteration = months
        elif self.interval == 'quarterly':
            if months > 4:
                iteration = months / 3
            else:
                iteration = 1
        elif self.interval == 'yearly':
            if months > 12:
                iteration = months / 12
            else:
                iteration = 1
        elif self.interval == 'biannually':
            if months > 24:
                iteration = months / 24
            else:
                iteration = 1

        i = 0
        total = 0
        fgr_lines = self.fgr_detail_ids
        each_amount = self.fgr_total_payment / self.no_of_installment
        while i < self.no_of_installment:
            total += each_amount
            fgr_lines += fgr_lines.new({
                'Due_date': str(new_date),
                'fgr_details': 'FGR Details',
                'asset_project_id': self.asset_project_id.id,
                'property_id': self.property_id.id,
                'amount': each_amount,
                'fgr_payment_request_id': self.id,
            })
            if self.interval == 'monthly':
                new_date = new_date + relativedelta(months=1)
            elif self.interval == 'quarterly':
                new_date = new_date + relativedelta(months=3)
            elif self.interval == 'biannually':
                new_date = new_date + relativedelta(months=24)
            elif self.interval == 'yearly':
                new_date = new_date + relativedelta(months=12)
            else:
                raise UserError('Please select Interval')
            if new_date > end_date:
                new_date = end_date
            i += 1

        if fgr_lines:
            self.fgr_detail_ids = fgr_lines

    def gethtmlval(self, val):
        if val:
            converted_content = jinja_template_env.from_string(val).render(
                {'object': self})
            return converted_content
        else:
            return

    @api.onchange('asset_project_id')
    def onchange_proejct(self):
        if self.asset_project_id:
            self.fgr_agreement = self.asset_project_id.fgr_agreement

    @api.depends('agreement_start_date', 'agreement_end_date')
    def get_dates_difference(self):
        for rec in self:
            difference2 = 0
            if rec.agreement_start_date and rec.agreement_end_date:
                if rec.agreement_end_date < rec.agreement_start_date:
                    raise UserError('End date is greater then start date')
                difference = relativedelta(rec.agreement_end_date + relativedelta(days=1), rec.agreement_start_date)
                difference2 = str(difference.years) + ' Years ' + str(difference.months) + ' Months ' \
                              + str(difference.days) + ' Days '
            rec.difference = difference2

    @api.depends('spa_id')
    def get_spa_details(self):
        for rec in self:
            rec.related_booking_id = rec.spa_id.id
            rec.partner_id = rec.spa_id.partner_id.id
            rec.mobile = rec.spa_id.partner_id.mobile
            rec.email = rec.spa_id.partner_id.email
            rec.joined_partner_id = [(6, 0, rec.spa_id.joint_partner_id.ids)]
            rec.asset_project_id = rec.spa_id.asset_project_id.id
            rec.property_id = rec.spa_id.property_id.id
            rec.sale_date = rec.spa_id.date_order
            # rec.agent_ref = rec.spa_id.agent_ref
            # rec.agent_id = rec.spa_id.agent_id.id
            rec.property_price = rec.spa_id.property_price
            rec.booking_discount = rec.spa_id.discount_value
            rec.booking_date = rec.spa_id.booking_date
            agent_discount = (rec.spa_id.agent_discount_perc / 100) * rec.spa_id.property_price
            rec.agent_discount = agent_discount
            discount_value = agent_discount + rec.spa_id.discount_value
            rec.discount_value = discount_value
            discount_value_perc = 0
            if rec.spa_id.property_price:
                total_discount_perc = (discount_value / rec.spa_id.property_price) * 100
                rec.discount_value_perc = total_discount_perc
            rec.discount_value_perc = discount_value_perc
            rec.price = rec.spa_id.price
            rec.oqood_fee = rec.spa_id.oqood_fee
            rec.admin_fee = rec.spa_id.admin_fee
            rec.total_spa_value = rec.spa_id.total_spa_value
            rec.total_due = rec.spa_id.instalmnt_bls_pend_plus_admin_oqood
            rec.matured_pdcs = rec.spa_id.matured_pdcs
            rec.balance_due_collection = rec.spa_id.balance_due_collection

    # instalmnt_bls_pend_plus_admin_oqood

    state = fields.Selection(
        [('draft', 'Draft'),
         ('under_review', 'Under Review'),
         ('under_accounts_verification', 'Under Accounts Verification'),
         ('under_approval', 'Under Approval'),
         ('approved', 'Approved'),
         ('in_process', 'In Process'),
         ('done', 'Done'),
         ('rejected', 'Rejected'),
         ('cancel', 'Cancelled')], default='draft', string='Status',
        tracking=True)

    company_id = fields.Many2one(
        'res.company',
        'Company',
        help="Company name which involve",
        default=lambda self: self.env.user.company_id)

    @api.depends('fgr_detail_ids', 'fgr_detail_ids.inv')
    def action_status(self):
        for rec in self:
            state = rec.state
            if rec.fgr_detail_ids:
                done = True
                for line in rec.fgr_detail_ids:
                    if line.inv:
                        rec.write({'state': 'in_process'})
                    else:
                        done = False
                if done:
                    rec.write({'state': 'done'})
            else:
                rec.state = state

    def action_submit_review(self):
        if not self.fgr_detail_ids:
            raise UserError('Please define schedule first')
        self.write({'state': 'under_review'})

    def action_under_accounts(self):
        self.write({'state': 'under_accounts_verification'})

    def action_review(self):
        self.write({'state': 'under_approval'})

    def action_approved(self):
        self.write({'state': 'approved'})

    def action_rollback(self):
        if self.state == 'under_approval':
            self.write({'state': 'under_review'})

    def action_reject(self):
        self.write({'state': 'rejected'})

    def action_draft(self):
        self.write({'state': 'draft'})

    # 
    # def action_done(self):
    #     self.write({'state':'done'})

    def action_cancel(self):
        self.write({'state': 'cancel'})


class AccountInvoice(models.Model):
    _inherit = "account.move"

    fgr_payment_req_id = fields.Many2one('fgr.payment.request', 'FGR Payment')
    fgr_payment_req_detail_id = fields.Many2one('fgr.details', 'FGR Payment Line')


class FGRDetails(models.Model):
    _name = 'fgr.details'
    _description = 'FGR Details'

    name = fields.Char("Name")
    sr_no = fields.Integer('Sr#', compute='_get_line_numbers')
    fgr_details = fields.Text('FGR Details')
    amount = fields.Float('FGR Amount')
    Due_date = fields.Date('Due Date')
    inv = fields.Boolean('Invoiced')
    paid_check = fields.Boolean('Paid', compute='get_paid_check', store=True)
    invc_id = fields.Many2one('account.move', 'Invoice')
    invc_ids = fields.One2many('account.move', 'fgr_payment_req_detail_id', 'Invoices')
    fgr_payment_request_id = fields.Many2one('fgr.payment.request', 'FGR Payment', ondelete='cascade')
    state = fields.Selection(
        [('draft', 'Draft'),
         ('confirm', 'Confirmed'),
         ('cancel', 'Cancelled')], compute='get_state', store=True, default='draft', string='Status')
    asset_project_id = fields.Many2one('account.asset.asset', 'Project', domain="[('project', '=', True)]")
    property_id = fields.Many2one('account.asset.asset', string='Property')

    @api.model
    def old_fgr_line_project_property(self):
        fgr_lines = self.env['fgr.details'].search([])
        for rec in fgr_lines:
            if not rec.property_id or rec.asset_project_id:
                rec.property_id = rec.fgr_payment_request_id.property_id.id
                rec.asset_project_id = rec.fgr_payment_request_id.asset_project_id.id

    @api.depends('invc_id', 'invc_id.state', 'invc_id.payment_state','invc_ids', 'invc_ids.state', 'invc_ids.payment_state')
    def get_paid_check(self):
        for rec in self:
            if rec.invc_ids:
                paid = True
                for inv in rec.invc_ids:
                    if inv.state not in ['rejected', 'cancel'] and inv.payment_state not in ['in_payment', 'paid']:
                        paid = False
                rec.paid_check = paid
            else:
                paid = False
                if rec.invc_id and rec.invc_id.state == 'posted' and rec.invc_id.payment_state in ['in_payment','paid']:
                    paid = True
                rec.paid_check = paid

    # def _get_line_numbers(self):
    #     # line_num = 1
    #     fgr_ids_list = []
    #     fgr_ids = self.env['fgr.details'].search([('fgr_payment_request_id', '!=', False)])
    #     for ln in fgr_ids:
    #         fgr_ids_list.append(ln.fgr_payment_request_id.id)
    #     for val in set(fgr_ids_list):
    #         line_num = 1
    #         for line in self.env['fgr.details'].search([('fgr_payment_request_id', '=', val)], order='Due_date asc'):
    #             line.sr_no = line_num
    #             line_num += 1
    #
    def _get_line_numbers(self):
        for rec in self:
            if rec.fgr_payment_request_id:
                line_num = 0
                for line in rec.env['fgr.details'].search([('fgr_payment_request_id', '=', rec.fgr_payment_request_id.id)], order='Due_date asc'):
                    line_num += 1
                    if line.id == rec.id:
                        break
                rec.sr_no = line_num
            else:
                rec.sr_no = 0


    @api.depends('fgr_payment_request_id', 'fgr_payment_request_id.state')
    def get_state(self):
        for rec in self:
            if rec.fgr_payment_request_id.state in ['approved', 'done', 'in_process']:
                rec.state = 'confirm'
            elif rec.fgr_payment_request_id.state in ['cancel', 'rejected']:
                rec.state = 'cancel'
            else:
                rec.state = 'draft'

    def get_partner_ids(self, user_ids):
        if user_ids:
            anb = str([user.partner_id.email for user in user_ids]).replace('[', '').replace(']', '')
            return anb.replace("'", '')

    @api.model
    def send_fgr_due_email(self):
        srs = self.env['fgr.details'].search([('state', '=', 'confirm'),('inv', '=', True),('paid_check', '=', False)])
        for rec in srs:
            if rec.Due_date:
                current_date = datetime.now().date()
                dates_diff = rec.Due_date - current_date
                days = dates_diff.days
                if days in [0, 5]:
                    mr = rec.env['mail.recipients'].search([('name','=','FGR Due Alert')])
                    for reci in mr:
                        if reci.user_ids:
                            email_template = rec.env.ref(
                                'fgr_payment_request.fgr_payment_due_template')
                            if email_template.mail_server_id:
                                email_template.email_from = email_template.mail_server_id.name
                            email_template.email_to = rec.get_partner_ids(reci.user_ids)
                            email_template.send_mail(rec.id, force_send=True)

    def get_invloice_lines(self):
        for rec in self:
            inv_line = {
                # 'origin': 'fgr.details',
                'name': _('FGR Details'),
                'price_unit': rec.amount or 0.00,
                'quantity': 1,
                'property_id': rec.fgr_payment_request_id.property_id.id,
                'asset_project_id': rec.fgr_payment_request_id.asset_project_id.id,
                'account_id': self.env['account.account'].search([('id', '=', 1041)]).id or False,
            }
            return [(0, 0, inv_line)]

    def unlink_fgr_cancel_inv(self):
        fgr_sche = self.env['fgr.details'].search([('inv', '=', True)])
        for rec in fgr_sche:
            if rec.invc_id and rec.invc_id.state == 'cancel':
                rec.invc_id = False
                rec.inv = False

    def create_fgr_invoice_auto(self):
        inv_obj = self.env['account.move']
        jan_1st = date(2022, 1, 1)
        fgr_sche = self.env['fgr.details'].search(
            [('Due_date', '>=', jan_1st),('Due_date', '<=', datetime.now().date()), ('inv', '!=', True), ('state', '=', 'confirm')])
        for rec in fgr_sche:
            inv_line_values = rec.get_invloice_lines()
            inv_values = {
                'fgr_payment_req_id': rec.fgr_payment_request_id.id,
                'partner_id': rec.fgr_payment_request_id.partner_id.id or False,
                'move_type': 'in_invoice',
                # 'date_due': rec.Due_date,
                'journal_id': 17,
                'property_id': rec.fgr_payment_request_id.property_id.id or False,
                'asset_project_id': rec.fgr_payment_request_id.asset_project_id.id or False,
                'invoice_date': datetime.now().strftime(
                    DEFAULT_SERVER_DATE_FORMAT) or False,
                'invoice_date_due': rec.Due_date or False,
                'invoice_line_ids': inv_line_values,
            }
            invoice_id = inv_obj.create(inv_values)
            invoice_id.action_post()
            rec.write({'invc_id': invoice_id.id, 'inv': True})
            rec.update({'invc_ids': [(6, 0, invoice_id.ids)]})
            if invoice_id:
                rec.fgr_payment_request_id.state = 'in_process'

    def create_invoice(self):
        inv_obj = self.env['account.move']
        for rec in self:
            inv_line_values = rec.get_invloice_lines()
            inv_values = {
                'fgr_payment_req_id': rec.fgr_payment_request_id.id,
                'partner_id': rec.fgr_payment_request_id.partner_id.id or False,
                'move_type': 'in_invoice',
                # 'date_due': rec.Due_date,
                # 'date_due': rec.invoice_date,
                'journal_id': 17,
                'property_id': rec.fgr_payment_request_id.property_id.id or False,
                'asset_project_id': rec.fgr_payment_request_id.asset_project_id.id or False,
                'invoice_date': datetime.now().strftime(
                    DEFAULT_SERVER_DATE_FORMAT) or False,
                'invoice_date_due': rec.Due_date or False,
                'invoice_line_ids': inv_line_values,
            }
            invoice_id = inv_obj.create(inv_values)
            invoice_id.action_post()
            rec.write({'invc_id': invoice_id.id, 'inv': True})
            rec.update({'invc_ids': [(6, 0, invoice_id.ids)]})
            if invoice_id:
                rec.fgr_payment_request_id.state = 'in_process'
            inv_form_id = self.env.ref('account.view_move_form').id

            return {
                'view_id': inv_form_id,
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


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    fgr_details_ids = fields.Many2many('fgr.details', 'fgr_payment_rel', 'fgr_id', 'payment_id', 'FGR Installments',
                                       domain=[('state', '=', 'confirm')])


class BookingDiscount(models.Model):
    _inherit = 'booking.discount'

    related_payment_ids = fields.Many2many('payment.schedule', 'schedule_discount_rel', 'schedule_id', 'discount_id',
                                           'Related Payment Options')


# class SaleOrder(models.Model):
#     _inherit = 'sale.order'

    # @api.onchange('booking_discount_id')
    # def onchange_booking_discount_id(self):
    #     dom = [('id', '=', -1)]
    #     if self.booking_discount_id and self.booking_discount_id.related_payment_ids:
    #         dom = [('id', 'in', self.booking_discount_id.related_payment_ids.ids)]
    #
    #     return {'domain': {'payment_schedule_id': dom}}
