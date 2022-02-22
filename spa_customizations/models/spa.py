# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from datetime import datetime
from odoo.exceptions import AccessError, UserError, ValidationError
from dateutil.relativedelta import relativedelta
from odoo.addons.mail.models import mail_template
from odoo.addons.mail.models.mail_render_mixin import jinja_template_env, jinja_safe_template_env
import base64
import os

root_path = os.path.dirname(os.path.abspath(__file__))
from xlrd import open_workbook


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    asset_project_id = fields.Many2one('account.asset.asset', 'Project', domain="[('project', '=', True)]")
    rental_id = fields.Many2one('account.analytic.account', string='Rental Tenancy')

    @api.onchange('asset_project_id')
    def onchange_asset_project_id(self):
        property_ids = self.env['account.asset.asset'].search(
            [('state', '=', 'draft'),('parent_id', '=', self.asset_project_id.id)])
        return {'domain': {'property_id': [('id', 'in', property_ids.ids)]}}

    def action_new_quotation(self):
        action = super().action_new_quotation()
        # Make the lead's Assigned Partner the quotation's Referrer.
        action['context']['default_asset_project_id'] = self.asset_project_id.id
        action['context']['default_property_id'] = self.property_id.id
        action['context']['from_method'] = True
        return action

class AccountPayment(models.Model):
    _inherit = 'account.payment'

    spa_id = fields.Many2one('sale.order', 'SPA/Booking')


class OqoodStatus(models.Model):
    _name = 'oqood.status'
    _description = 'Oqood Status'

    name = fields.Char('Name')
    active = fields.Boolean('Active', default=True)


class AdminFeeStatus(models.Model):
    _name = 'admin.status'
    _description = 'Admin Status'

    name = fields.Char('Name')
    active = fields.Boolean('Active', default=True)


class ReceivableStatus(models.Model):
    _name = 'receivable.status'
    _description = 'SPA Receivable Status'

    name = fields.Char('Name')
    active = fields.Boolean('Active', default=True)


class InventoryStatus(models.Model):
    _name = 'inventory.status'
    _description = 'SPA Inventory Status'

    name = fields.Char('Name')
    active = fields.Boolean(string='Active', default=True)


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _default_receivable_status(self):
        return self.env['receivable.status'].search([('name', '=', 'Under Normal Collections')], limit=1).id or False

    booking_number = fields.Integer('Booking Number', readonly=True, tracking=True)
    pricelist_id = fields.Many2one(
        'product.pricelist', string='Pricelist', check_company=True,  # Unrequired company
        readonly=False,
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]", tracking=1,
        help="If you change the pricelist, only newly added lines will be affected.")
    booking_date = fields.Datetime('Booking Date', tracking=True)
    finish_type = fields.Selection([('standard_finish', 'Standard Finish'), ('premium_finish', 'Premium Finish')],
                                   default="standard_finish", string="Finish Type", tracking=True)
    premium_finish_cost = fields.Float('Premium Finish Cost', tracking=True)
    premium_schedule_ids = fields.One2many('premium.finish.ps', 'sale_id',
                                        'Premium Finish Payment Schedule', tracking=True)
    booking_days = fields.Integer('Booking Days', compute='compute_booking_days', store=True)
    sale_type = fields.Selection([
        ('samana_sale', 'Samana Sale'),
        ('investor_sale', 'Investor Sale'),
    ], string='Sale Type', required=True, default='samana_sale', tracking=True)
    property_id = fields.Many2one('account.asset.asset', string='Property', tracking=True)
    asset_project_id = fields.Many2one('account.asset.asset', 'Project', domain="[('project', '=', True)]")
    rental_returns = fields.Selection([('yes', 'Yes'), ('no', 'No')], string='Rental Returns', tracking=True)
    joint_active = fields.Boolean(string="Joint Purchase", tracking=True)
    # joint_partner_id = fields.Many2one('res.partner',
    #                                    string="Joint Partner", tracking=True)
    joint_partner_id = fields.Many2many('res.partner', 'joined_partner_rel', 'spa_id', 'join_id',
                                         string="Joint Partner's", tracking=True)
    joint_partner_dump = fields.Many2one('res.partner', string="Dump Joint Partner", tracking=True)
    property_four_percent = fields.Float('Oqood Reg Fee 4%', compute='_get_4_percent_of_property', store=True,
                                         tracking=True)

    booking_remarks = fields.Text("Booking Remarks")
    property_price = fields.Float('Price', related='property_id.value', store=True, readonly=True, tracking=True)
    receivable_status_id = fields.Many2one(
        'receivable.status', 'Receivable Status', default=_default_receivable_status)
    property_price_per_sqf = fields.Float(compute='_compute_property_price_per_sqf', store=True,
                                          string='Property Price Per SQF')
    oqood_status = fields.Many2one('oqood.status', 'Oqood Status')
    admin_status = fields.Many2one('admin.status', 'Admin Fee Status')
    tas_inflows = fields.Char('TAS Inflows')
    spa_dld_amendment = fields.Boolean('dle', default=False)
    inventory_status = fields.Many2one('inventory.status', 'SPA Inventory Status')
    spa_wo_amendment = fields.Boolean('SPA Without DLD Schedule', default=False)

    # bottom fields
    amount_till_date = fields.Float('Total Installments Payable Till Date', tracking=True)
    paid_installments = fields.Float(string="Paid Installments", store=True, tracking=True,
                                     compute='get_paid_installments', help="sum of received amount from installments")
    paid_installments_perc = fields.Float(string="Paid Installments %", store=True, tracking=True,
                                          compute='get_paid_perc',
                                          help="(Paid Installments / Total Property Sale Value) *100")
    matured_pdcs_perc = fields.Float(string="Total Realized Collection %", store=True, tracking=True,
                                     compute='get_realized_perc',
                                     help="(Amount Received (Realized Collections)/ Total SPA Value) *100")
    unsecured_collections_perc = fields.Float(string="Total Unsecured Collections %", store=True, tracking=True,
                                              compute='get_unsecured_perc',
                                              help="Total Unsecured Collections / Total SPA Value) *100")
    pending_balance = fields.Float('Pending Collections', compute='compute_pending_balance', tracking=True,
                                   help='Total SPA Value - Total Collections')

    balance_due_collection = fields.Float('Balance Due Collection', store=True, compute='compute_balance_due',
                                          tracking=True,
                                          help='Total Due Amount - Amount Received (Realized Collections)')
    total_unsecured_collections = fields.Float('Total Unsecured Collections', store=True,
                                               compute='compute_unsecured_collections', tracking=True,
                                               help='Sum of Non-matured + Uncleared + Held + Bounced Cheques')
    installment_balance_pending = fields.Float('Balance Due Installment',
                                               compute='compute_installment_balance_pending', store=True,
                                               tracking=True,
                                               help='Installments Due - Paid Installments')
    instalmnt_bls_pend_plus_admin_oqood = fields.Float('Total Due Amount',
                                                       compute='compute_installment_balance_pending', store=True,
                                                       tracking=True,
                                                       help='Installment Payable till Date + Oqood charged + Admin Charged + Other Charges')
    pending_balance_perc = fields.Float('Pending Collections (%)', compute='compute_pending_balance_perc',
                                        tracking=True, help='Pending Collections /Total SPA Value*100')
    receipts_perc = fields.Float('Total Collections % ', compute='compute_receipts_perc', tracking=True
                                 , store=True, help='Total Collections/Total SPA Value*100')
    matured_pdcs = fields.Float('Amount Received (Realized Collections)', store=True, compute='compute_receipt_total',
                                tracking=True, help='All Posted Receipts')
    hold_pdcs = fields.Float('Cheques Held', store=True, compute='compute_receipt_total', tracking=True)
    deposited_pdcs = fields.Float('Uncleared Cheques', store=True, compute='compute_receipt_total',
                                  tracking=True, help="PDCs in Deposited Status")
    withdraw_pdcs = fields.Float('Cheques Withdrawn', store=True, compute='compute_receipt_total',
                                 tracking=True, help="PDCs in Withdraw Status")
    un_matured_pdcs = fields.Float('Non-Matured Collections', store=True, compute='compute_receipt_total',
                                   tracking=True, help="PDCs in Pending for Collection and Collected Status")
    bounced_pdcs = fields.Float('Bounced Cheque', store=True, compute='compute_receipt_total',
                                tracking=True, help="PDCs in Bounced Status")
    total_receipts = fields.Float('Total Collections', store=True, compute='compute_receipt_total',
                                  tracking=True, help="Total Receipts where state not in 'draft','proforma',"
                                                      "'cancelled','refused','rejected','replaced','outsourced'")
    total_spa_value = fields.Float('Total SPA Value', store=True, compute='compute_total_spa_value',
                                   tracking=True, help='Property Price + Oqood charged + Admin Charged + Other Charges')
    #
    oqood_fee = fields.Float(string='Oqood Fee Charged', compute='_get_4_percent_of_property', store=True,
                             tracking=True)
    admin_fee = fields.Float(string='Admin Fee Charged', tracking=True)
    net_receipts = fields.Float('Total Booking Value', compute='compute_net_receipts', store=True, tracking=True)

    oqood_received = fields.Float('Oqood Received')
    admin_received = fields.Float('Admin Fee Received')
    balance_due_oqood = fields.Float(string="Balance Due Oqood", store=True, tracking=True,
                                     compute='due_oqood', help="Oqood fee charged - Oqood fee received")
    balance_due_admin = fields.Float(string="Balance Due Admin Charges", store=True, tracking=True,
                                     compute='due_admin', help="Admin fee charged - Admin fee received")
    other_received = fields.Float(string="Other Charges Received", tracking=True,
                                  help="Total Reconciled amount against Add Jvs")
    balance_due_other = fields.Float(string="Balance Due Other Charges", tracking=True,
                                     compute='due_other', store=True,
                                     help="Other Charges - Other Charges Received",)
    escrow = fields.Float(string="Escrow Receipts", compute='_escrow')
    escrow_perc = fields.Float(string="Escrow Receipt Percentage(%)", compute='escrow_perct')
    non_escrow = fields.Float(string="Non Escrow Receipts", compute='_escrow')
    non_escrow_perc = fields.Float(string="Non Escrow Receipt Percentage(%)", compute="non_escrow_perct")
    total_escrow = fields.Float("Total", compute="escrow_tot")
    total_escrow_perc = fields.Float("Total Percentage(%)", compute="tot_escrow_perct")

    price = fields.Float(string='Property Sale Price', compute='compute_price', store=True, tracking=True)
    agreed_payment_plan = fields.Char('Agreed Payment Plan', tracking=True)
    installment_start_date = fields.Date('Installment Start Date', tracking=True)
    payment_plan_creation = fields.Selection(
        [('later', 'Later'), ('standard', 'Standard Selection'), ('excel', 'Excel Upload'),
         ('custom', 'Custom Payment Plan')], string='Payment Plan Creation')
    payment_schedule_id = fields.Many2one('payment.schedule', 'Payment Schedule', required=False, tracking=True)

    booking_discount_id = fields.Many2one('booking.discount', string='Booking Discount', tracking=True)
    manual_discount = fields.Boolean('Manual', tracking=True)
    manual_discount_perc = fields.Float(compute='compute_discount_perc', store=True, string='Discount(%)',
                                        tracking=True)
    discount_value = fields.Float(string='Discount Amount', compute='compute_discount_value')
    manual_discount_amount = fields.Float(string='Manual Discount Amount', tracking=True)
    agent_commission_type_id = fields.Many2one('commission.type', string='Agent Commission')

    agent_discount_perc = fields.Float('Agent Discount(%)', tracking=True)
    net_commission_perc = fields.Float(compute='compute_net_comm', store=True, string='Net Commission(%)',
                                       tracking=True)
    net_commission_sp = fields.Float(compute='compute_net_commission_sp', store=True, string='Net Commission on SP',
                                     tracking=True)
    file = fields.Binary(string='Select Xls file')
    file2 = fields.Binary(string='file to download')
    import_done = fields.Boolean(string='import done')
    invoiced_schedule_check = fields.Boolean(compute='compute_is_invoiced', string='Invoiced Schedule Check')
    schedule_total = fields.Float(compute="compute_schedule_total", string='Installment Total')
    down_payment_perc = fields.Float('Down Payment(%)', tracking=True)
    down_payment = fields.Float(compute='get_down_payment', store=True, string='Down Payment', tracking=True)
    each_installment_perc = fields.Float('Each Installment(%)', tracking=True)
    each_installment_amount = fields.Float(compute='get_each_installment', store=True, string='Each Instalment Amount')
    no_of_installment_amount = fields.Float(compute='get_no_of_installment_amount', store=True,
                                            string='No of Installment Amount')
    no_of_installment = fields.Integer(string='No of Instalment')
    installment_interval = fields.Selection(
        [('monthly', 'Monthly'), ('quarterly', 'Quarterly'),
         ('semi_annually', 'Semi-annually'),
         ('yearly', 'Yearly'),
         ('custom_days', 'Custom Days Interval')], 'Instalment Interval')
    installment_days_interval = fields.Integer(string='Instalment Days Interval')
    property_price_after_dp = fields.Float(compute="get_amount_after_dp", store=True, string='Property Price After DP')
    handover_perc = fields.Float('Handover(%)', tracking=True)
    handover_amount = fields.Float(compute='get_handover', store=True, string='Handover Amount')
    remaining_perc = fields.Float(compute='get_remaining', store=True, string='Remaining(%)', tracking=True)
    remaining_amount = fields.Float(compute='get_remaining_amount', store=True, string='Remaining Amount')
    remaining_no_of_installment = fields.Integer(string='Remaining No of Instalment')
    remaining_installments_amount = fields.Float(compute='get_remaining_installments_amount',
                                                 string='Remaining No of Instalment Amount', store=True)
    sale_payment_schedule_ids = fields.One2many('sale.rent.schedule', 'sale_id', 'Sale Payment Schedule', tracking=True)
    is_payment_schedule = fields.Boolean(string="Payment Schedule Created", default=False, tracking=True)
    vat_id = fields.Many2one('account.tax', 'VAT(%)')
    vat_amount = fields.Float(compute='get_vat_amount', store=True, string='VAT Amount')
    property_inc_vat_amount = fields.Float(compute='get_property_vat_amount', store=True,
                                           string='Property Amount Including VAT')
    other_charges = fields.Float(string='Other Charges', compute='compute_other_charges', store=True, tracking=True)
    receipt_ids = fields.One2many('account.payment', 'spa_id', string='Receipts', tracking=True)
    payments_ids = fields.One2many('account.payment', 'spa_payment_id', string='Payments', tracking=True)

    other_charges_ids = fields.Many2many('account.move', 'spa_other_charges_rel', 'sale_id', 'charge_id',
                                         string='other Charges')
    other_charges_inv_ids = fields.Many2many('account.move', 'spa_other_charges_inv_rel', 'sale_id', 'charge_inv_id',
                                             string='other Charges')
    add_charges_ids = fields.Many2many('account.move', 'spa_add_charge_rel', 'sale_id', 'charge_id',
                                       string='Add JVs')
    less_charges_ids = fields.Many2many('account.move', 'spa_less_charge_rel', 'sale_id', 'charge_id',
                                        string='Less JVs')
    # waive_off_oqood = fields.Boolean('Waive Off Oqood', default=False, tracking=True)
    # oqood_waived = fields.Float('Oqood Waived', tracking=True)
    state = fields.Selection([
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
    ], string='Status', readonly=True, copy=False, index=True, tracking=3, default='draft')

    demand = fields.Boolean(string='Is Demand')
    # action_buy_create_spa
    tentative_booking_date = fields.Date('Tentative Booking Date')
    rejected_from = fields.Char(string='Rejected From')
    approval_require = fields.Boolean(string='Approval Require')
    later_check = fields.Boolean(string='Later Check')
    min_down_payment_perc = fields.Float('Minimum Down Payment %')
    spa_barcode = fields.Char('Barcode', compute='compute_spa_barcode', tracking=True)
    sale_term_id = fields.Many2one('sale.payment.term', string="Terms and Condition", tracking=True)
    internal_type = fields.Selection([('booking', 'Booking'), ('spa', 'SPA')], string='Internal Type',
                                     compute='compute_internal_type', store=True)
    payment_plan_ids = fields.One2many('dld.payment.plan', 'sale_id', 'Payment Plan')
    project_name = fields.Char(compute="get_project_name", store=True, string='PRj Name')
    schedule_a = fields.Text('Schedule A')
    schedule_b = fields.Text('Schedule B')
    schedule_c = fields.Text('Schedule C')
    schedule_d = fields.Text('Schedule D')
    schedule_e = fields.Text('Schedule E')
    schedule_f = fields.Text('Schedule F')
    schedule_g = fields.Text('Schedule G')
    schedule_h = fields.Text('Schedule H')
    schedule_i = fields.Text('Schedule I')
    schedule_a_eng = fields.Text('Schedule A Eng')
    schedule_b_eng = fields.Text('Schedule B Eng')
    schedule_c_eng = fields.Text('Schedule C Eng')
    schedule_d_eng = fields.Text('Schedule D Eng')
    schedule_e_eng = fields.Text('Schedule E Eng')
    schedule_f_eng = fields.Text('Schedule F Eng')
    schedule_g_eng = fields.Text('Schedule G Eng')
    schedule_h_eng = fields.Text('Schedule H Eng')
    schedule_i_eng = fields.Text('Schedule I Eng')

    all_invoice_ids = fields.Many2many('account.move', 'spa_invoice_rell', 'sale_id', 'invoice_id',
                                        string='Invoices', compute='compute_all_invoices', store=True)
    pdc_receipts = fields.One2many('account.voucher.collection', 'sale_id', string='PDC Receipts', tracking=True)

    @api.depends('sale_payment_schedule_ids','sale_payment_schedule_ids.invc_id',
                 'sale_payment_schedule_ids.invc_id.state',
                 'sale_payment_schedule_ids.invc_id.payment_state',
                 'other_charges_inv_ids','other_charges_inv_ids.state',
                 'other_charges_inv_ids.payment_state',
                 'partner_id','property_id')
    def compute_all_invoices(self):
        for rec in self:
            invoices = rec.env['account.move'].search([('payment_state', '!=', 'reversed'),('partner_id','=',rec.partner_id.id),('property_id','=',rec.property_id.id),('state','in',['posted','paid']),('move_type','=','out_invoice')])
            if invoices:
                rec.all_invoice_ids = [(6, 0, invoices.ids)]
            else:
                rec.all_invoice_ids = [(6, 0, [])]



    @api.model
    def cron_compute_invoices(self):
        sos = self.env['sale.order'].search([])
        for rec in sos:
            invoices = rec.env['account.move'].search([('payment_state', '!=', 'reversed'),('partner_id','=',rec.partner_id.id),('property_id','=',rec.property_id.id),('state','in',['posted','paid']),('move_type','=','out_invoice')])
            if invoices:
                rec.all_invoice_ids = [(6, 0, invoices.ids)]
            else:
                rec.all_invoice_ids  = [(6, 0, [])]

    @api.model
    def cron_joint_partner(self):
        sos = self.env['sale.order'].search([('joint_partner_dump','!=',False)])
        for rec in sos:
            if rec.joint_partner_dump:
                rec.joint_partner_id = [(6, 0, rec.joint_partner_dump.ids)]


    @api.model
    def get_empty_terms(self):
        so = self.env['sale.order'].search([])
        for rec in so:
            if not rec.sale_term_id:
                rec.sale_term_id = rec.asset_project_id.sale_term_id.id

    @api.model
    def get_amount_till_now(self):
        sos = self.env['sale.order'].search([])
        for rec in sos:
            if rec.sale_payment_schedule_ids:
                total = 0.00
                for line in rec.sale_payment_schedule_ids:
                    if line.start_date <= datetime.now().date():
                        total += line.amount
                rec.amount_till_date = total


    @api.onchange('sale_payment_schedule_ids','sale_payment_schedule_ids.start_date','sale_payment_schedule_ids.amount')
    def onchange_payment_schedule(self):
        for rec in self:
            if rec.sale_payment_schedule_ids:
                total = 0.00
                for line in rec.sale_payment_schedule_ids:
                    if line.start_date <= datetime.now().date():
                        total += line.amount
                rec.amount_till_date = total

    def gethtmlval(self, val):
        if val:
            converted_content = jinja_template_env.from_string(val).render({'object': self})
            return converted_content
        else:
            return

    @api.depends('asset_project_id')
    def get_project_name(self):
        for rec in self:
            if rec.asset_project_id:
                rec.project_name = rec.asset_project_id.name
            else:
                rec.project_name = False

    @api.model
    def old_get_project_name(self):
        sos = self.env['sale.order'].search([])
        for rec in sos:
            if rec.asset_project_id:
                rec.project_name = rec.asset_project_id.name
            else:
                rec.project_name = False

    @api.model
    def old_schedules(self):
        sos = self.env['sale.order'].search([])
        for rec in sos:
            if rec.asset_project_id:
                rec.schedule_a_eng = rec.asset_project_id.schedule_a_eng
                rec.schedule_b_eng = rec.asset_project_id.schedule_b_eng
                rec.schedule_c_eng = rec.asset_project_id.schedule_c_eng
                rec.schedule_d_eng = rec.asset_project_id.schedule_d_eng
                rec.schedule_e_eng = rec.asset_project_id.schedule_e_eng
                rec.schedule_f_eng = rec.asset_project_id.schedule_f_eng
                rec.schedule_g_eng = rec.asset_project_id.schedule_g_eng
                rec.schedule_h_eng = rec.asset_project_id.schedule_h_eng
                rec.schedule_i_eng = rec.asset_project_id.schedule_i_eng
                rec.sale_term_id = rec.asset_project_id.sale_term_id.id

    def name_get(self):
        return [(bd.id, "%s %s %s" % (
            bd.name if bd.name else bd.name, bd.property_id.name, bd.asset_project_id.name)) for bd in self]

    def action_spa_view_summary(self):
        for rec in self:
            ctx = dict(
                default_sale_id=rec.id,
                default_amount_untaxed=rec.amount_untaxed,
                default_amount_tax=rec.amount_tax,
                default_amount_total=rec.amount_total,
                default_amount_till_date=rec.amount_till_date,
                default_paid_installments=rec.paid_installments,
                default_paid_installments_perc=rec.paid_installments_perc,
                default_matured_pdcs_perc=rec.matured_pdcs_perc,
                default_unsecured_collections_perc=rec.unsecured_collections_perc,
                default_pending_balance=rec.pending_balance,
                default_balance_due_collection=rec.balance_due_collection,
                default_total_unsecured_collections=rec.total_unsecured_collections,
                default_installment_balance_pending=rec.installment_balance_pending,
                default_instalmnt_bls_pend_plus_admin_oqood=rec.instalmnt_bls_pend_plus_admin_oqood,
                default_pending_balance_perc=rec.pending_balance_perc,
                default_receipts_perc=rec.receipts_perc,
                default_matured_pdcs=rec.matured_pdcs,
                default_hold_pdcs=rec.hold_pdcs,
                default_deposited_pdcs=rec.deposited_pdcs,
                default_un_matured_pdcs=rec.un_matured_pdcs,
                default_bounced_pdcs=rec.bounced_pdcs,
                default_total_receipts=rec.total_receipts,
                default_total_spa_value=rec.total_spa_value,
                default_oqood_fee=rec.oqood_fee,
                default_admin_fee=rec.admin_fee,
                default_oqood_received=rec.oqood_received,
                default_admin_received=rec.admin_received,
                default_balance_due_oqood=rec.balance_due_oqood,
                default_balance_due_admin=rec.balance_due_admin,
                default_other_received=rec.other_received,
                default_balance_due_other=rec.balance_due_other,
                default_escrow=rec.escrow,
                default_escrow_perc=rec.escrow_perc,
                default_non_escrow=rec.non_escrow,
                default_non_escrow_perc=rec.non_escrow_perc,
                default_total_escrow=rec.total_escrow,
                default_total_escrow_perc=rec.total_escrow_perc,
                default_other_charges=rec.other_charges,

            )
            return {
                'name': _('SPA Summary View'),
                # 'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'spa.summary.view',
                'view_id': rec.env.ref('spa_customizations.view_spa_summary_view').id,
                'type': 'ir.actions.act_window',
                'context': ctx,
                'target': 'new'
            }

    def action_schedule_view_summary(self):
        for rec in self:
            ctx = dict(
                default_schedule_a_eng = rec.schedule_a_eng,
                default_schedule_b_eng = rec.schedule_b_eng,
                default_schedule_c_eng = rec.schedule_c_eng,
                default_schedule_d_eng = rec.schedule_d_eng,
                default_schedule_e_eng = rec.schedule_e_eng,
                default_schedule_f_eng = rec.schedule_f_eng,
                default_schedule_g_eng = rec.schedule_g_eng,
                default_schedule_h_eng = rec.schedule_h_eng,
                default_schedule_i_eng = rec.schedule_i_eng,

            )
            return {
                'name': _('SPA Schedule View'),
                'view_mode': 'form',
                'res_model': 'spa.schedule.view',
                'view_id': rec.env.ref('spa_customizations.view_spa_schedule_view').id,
                'type': 'ir.actions.act_window',
                'context': ctx,
                'target': 'new'
            }


    @api.model
    def get_dld_schedule_from_project(self, st):
        cb = self.env['sale.order'].search([('asset_project_id', '=', st)])
        for rec in cb:
            if not rec.payment_plan_ids:
                rec.payment_plan_ids = False
                pp_lines = rec.payment_plan_ids
                for l in rec.asset_project_id.payment_plan_ids:
                    pp_lines += pp_lines.new({
                        'name': l.name,
                        'percentage': l.percentage,
                        'payment_date_disc': l.payment_date_disc,
                        'sale_id': rec.id,
                    })
                if pp_lines:
                    rec.payment_plan_ids = pp_lines

    @api.onchange('payment_plan_creation')
    def onchange_payment_plan_creation(self):
        self.down_payment_perc = 0
        self.each_installment_perc = 0
        self.no_of_installment = 0
        self.handover_perc = 0
        self.remaining_perc = 0
        self.remaining_no_of_installment = 0
        self.installment_interval = False
        self.sale_payment_schedule_ids = False

    @api.depends('state')
    def compute_internal_type(self):
        for rec in self:
            if rec.state in ['draft', 'under_discount_approval', 'tentative_booking', 'review',
                             'under_cancellation', 'confirm_spa', 'booking_rejected', 'booking_cancel']:
                rec.internal_type = 'booking'
            else:
                rec.internal_type = 'spa'

    @api.model
    def old_internal_type(self):
        sos = self.env['sale.order'].search([])
        for rec in sos:
            if rec.state in ['draft', 'under_discount_approval', 'tentative_booking', 'review',
                             'under_cancellation', 'confirm_spa', 'booking_rejected', 'booking_cancel']:
                rec.internal_type = 'booking'
            else:
                rec.internal_type = 'spa'

    @api.depends('name', 'property_id')
    def compute_spa_barcode(self):
        for rec in self:
            rec.spa_barcode = str(rec.name) + "-" + str(rec.property_id.name)

    # def print_report_sale_form(self):
    #     data = {}
    #     return self.env.ref('spa_customizations.report_sale_form').report_action(self, data=data)

    def print_report_golf(self):
        data = {}
        return self.env.ref('spa_customizations.report_golf_form').report_action(self, data=data)

    def print_report_saleorder_english(self):
        data = {}
        data['english'] = True
        return self.env.ref('spa_customizations.report_sale_form').report_action(self, data=data)

    def get_joint_partner_address(self, jp):
        st = ''
        if jp:
            for line in jp:
                if st:
                    st = st + ', '
                if line.street:
                    st = st + line.street
                if line.street2:
                    if st:
                        st = st + ', '
                    st = st + line.street2
                if line.city:
                    if st:
                        st = st + ', '
                    st = st + line.city
                if line.state_id:
                    if st:
                        st = st + ', '
                    st = st + line.state_id.name
                if line.country_id:
                    if st:
                        st = st + ', '
                    st = st + line.country_id.name
        return st

    def get_jp_nationality(self, jp):
        st = ''
        if jp:
            for line in jp:
                if st:
                    st = st + ' / '
                if line.nationality_id:
                    st = st + line.nationality_id.name
        return st

    def get_jp_country(self, jp):
        st = ''
        if jp:
            for line in jp:
                if st:
                    st = st + ' / '
                if line.country_id:
                    st = st + line.country_id.name
        return st

    def get_jp_ppno(self, jp):
        st = ''
        if jp:
            for line in jp:
                if st:
                    st = st + ' / '
                if line.passport_no:
                    st = st + line.passport_no
        return st

    def get_jp_eid_no(self, jp):
        st = ''
        if jp:
            for line in jp:
                if st:
                    st = st + ' / '
                if line.eid_no:
                    st = st + line.eid_no
        return st

    def get_jp_email(self, jp):
        st = ''
        if jp:
            for line in jp:
                if st:
                    st = st + ' / '
                if line.email:
                    st = st + line.email
        return st

    def get_jp_city(self, jp):
        st = ''
        if jp:
            for line in jp:
                if st:
                    st = st + ' / '
                if line.street:
                    st = st + line.street
                if line.street2:
                    if st:
                        st = st + ', '
                    st = st + line.street2
                if line.city:
                    if st:
                        st = st + ', '
                    st = st + line.city
        return st

    def get_jp_len(self, jp):
        return len(jp)

    def get_jp_mobile(self, jp):
        st = ''
        if jp:
            for line in jp:
                if st:
                    st = st + ' / '
                if line.mobile:
                    st = st + line.mobile
                if line.phone:
                    if st:
                        st = st + ', '
                    st = st + line.phone
        return st

    def get_joined_partner_name(self, jp):
        st = ''
        if jp:
            for line in jp:
                if st:
                    st = st + ', '
                st = st + line.name
        return st

    @api.onchange('booking_discount_id')
    def onchange_discount_require(self):
        if self.booking_discount_id:
            self.approval_require = self.booking_discount_id.approval_require
            self.min_down_payment_perc = self.booking_discount_id.min_down_payment_perc
        else:
            self.min_down_payment_perc = False
            self.approval_require = False

    def action_is_buy_reject(self):
        self.write({'state': 'booking_rejected'})

    def action_is_buy_canceled(self):
        self.write({'state': 'booking_cancel'})
        self.property_id.write({'state': 'draft'})

    def action_is_buy_draft(self):
        self.write({'state': 'draft'})

    def submit_for_legal_review_print(self):
        ctx = dict(
            default_name="Please review the details properly as all payment schedule lines will be active for auto invoicing and installment notices once you submit the SPA under legal review. Do you still want to proceed?",
            default_sale_id=self.id
        )
        return {
            'name': _('Legal Review'),
            # 'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'submit.legal.review',
            'view_id': self.env.ref('spa_customizations.submit_legal_review_wizard').id,
            'type': 'ir.actions.act_window',
            'context': ctx,
            'target': 'new'
        }

    def action_legal_verify(self):
        for rec in self:
            rec.state = 'under_acc_verification_print'

    def action_account_verify(self):
        for rec in self:
            rec.state = 'under_confirmation_print'

    def action_refund_cancellation(self):
        for line in self.sale_payment_schedule_ids:
            if not line.inv:
                line.state = 'cancel'
                line.installment_status = 'cancel'
        self.property_id.write({'state': 'draft'})
        self.write({'state': 'refund_cancellation'})

    def action_rollback(self):
        for rec in self:
            if rec.state == 'under_legal_review_print':
                rec.state = 'draft'
            if rec.state == 'under_acc_verification_print':
                rec.state = 'under_legal_review_print'
            if rec.state == 'under_confirmation_print':
                rec.state = 'under_acc_verification_print'
            if rec.state == 'unconfirmed_ok_for_print':
                rec.state = 'under_confirmation_print'
            if rec.state == 'under_legal_review':
                rec.state = 'unconfirmed_ok_for_print'
            if rec.state == 'under_accounts_verification':
                rec.state = 'under_legal_review'
            if rec.state == 'under_approval':
                rec.state = 'under_accounts_verification'
            if rec.state == 'sale':
                rec.state = 'under_approval'
            if rec.rejected_from:
                if rec.state == 'rejected':
                    rec.state = rec.rejected_from

    def action_reject(self):
        for rec in self:
            rec.state = 'rejected'
            rec.rejected_from = rec.state

    def action_draft_spa(self):
        for rec in self:
            rec.state = 'spa_draft'

    def action_view_premium(self):
        ctx = {'default_sale_id': self.id}

        return {
            'name': _("Premium Finsh Schedule"),
            'view_id': self.env.ref('spa_customizations.premium_finish_field_tree').id,
            'view_mode': 'tree',
            'context': ctx,
            'domain': [('id', 'in', self.premium_schedule_ids.ids)],
            'res_model': 'premium.finish.ps',
            'type': 'ir.actions.act_window'
        }

    def action_view_pdc_receipts(self):
        ctx = {'default_partner_id': self.partner_id.id, 'default_sale_id': self.id,
               'default_asset_project_id': self.asset_project_id.id,
               'default_property_id': self.property_id.id}

        return {
            'name': _("PDC Receipts"),
            'view_id': False,
            'view_mode': 'tree,form',
            'context': ctx,
            'domain': [('id', 'in', self.pdc_receipts.ids)],
            'res_model': 'account.voucher.collection',
            'type': 'ir.actions.act_window'
        }

    def submit_for_legal_review(self):
        for rec in self:
            ctx = dict(
                default_name='Please review the details properly as all payment schedule lines will be active for auto invoicing and installment notices once you submit the SPA under legal review. Do you still want to proceed?',
                default_sale_id=rec.id
            )
            return {
                'name': _('Submit for Legal Review'),
                # 'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'submit.legal.review',
                'view_id': rec.env.ref('spa_customizations.submit_legal_review_wizard').id,
                'type': 'ir.actions.act_window',
                'context': ctx,
                'target': 'new'
            }
            # rec.state = 'under_legal_review'

    # def submit_for_final_legal_review(self):
    #     for rec in self:
    #         ctx = dict(
    #             default_sale_id=rec.id
    #         )
    #         return {
    #             'name': _('Submit for Final Legal Review'),
    #             'view_type': 'form',
    #             'view_mode': 'form',
    #             'res_model': 'spa.legal.review',
    #             'view_id': rec.env.ref('spa_customizations.view_legal_review_wizard').id,
    #             'type': 'ir.actions.act_window',
    #             'context': ctx,
    #             'target': 'new'
    #         }
    #         # rec.state = 'under_legal_review'

    def action_legal_final_verify(self):
        for rec in self:
            ctx = dict(
                default_sale_id=rec.id
            )
            return {
                'name': _('Legal Final Verification'),
                # 'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'spa.account.review',
                'view_id': rec.env.ref('spa_customizations.view_account_review_wizard').id,
                'type': 'ir.actions.act_window',
                'context': ctx,
                'target': 'new'
            }

    def action_account_final_verify(self):
        for rec in self:
            ctx = dict(
                default_sale_id=rec.id
            )
            return {
                'name': _('Accounts Final Verification,'),
                # 'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'spa.gm.review',
                'view_id': rec.env.ref('spa_customizations.view_gm_review_wizard').id,
                'type': 'ir.actions.act_window',
                'context': ctx,
                'target': 'new'
            }

    def action_unconfirmed_ok_for_print(self):
        for rec in self:
            rec.state = 'unconfirmed_ok_for_print'

    def action_is_buy_spa(self):
        self.write({'state': 'spa_draft'})
        for line in self.sale_payment_schedule_ids:
            line.state = 'confirm'
        # self.property_id.write({'state': 'book'})
        self.action_buy_create_spa()
        self.property_id.write({'state': 'sold'})

    def action_buy_create_spa(self):
        for data in self:
            if data.property_id:
                oqood_fee_rec = False
                admin_fee_rec = False
                if not data.asset_project_id.admin_fee_ledger_id:
                    raise UserError(_("Please select Admin Fee Ledger in selected Project."))
                if not data.asset_project_id.oqood_fee_ledger_id:
                    raise UserError(_("Please select Oqood Fee Ledger in selected Project."))
                if data.oqood_fee:
                    if not data.asset_project_id.oqood_fee_ledger_id:
                        raise UserError(_("Please select Oqood Fee Ledger in selected Project."))
                    oqood_invoice_line = []
                    oqood_invoice_line.append ((0, 0, {'name': "Oqood fee of" + str(data.name),
                                                     'asset_project_id': data.asset_project_id.id,
                                                     'property_id': data.property_id.id,
                                                     'account_id': data.asset_project_id.oqood_fee_ledger_id.id,
                                                     'quantity': 1,
                                                     # 'product_uom': 1,
                                                     'price_unit': data.oqood_fee}))
                    oqood_fee_rec = self.env['account.move'].create({
                        'partner_id': data.partner_id.id,
                        'asset_project_id': data.asset_project_id.id,
                        'property_id': data.property_id.id,
                        'invoice_user_id': data.user_id.id,
                        'team_id': data.team_id.id,
                        'company_id': self.env.user.company_id.id,
                        'move_type': 'out_invoice',
                        # 'account_id': data.partner_id.property_account_receivable_id.id,
                        'invoice_date': datetime.now().strftime('%Y-%m-%d'),
                        'state': 'draft',
                        # 'invoice_line_ids': admin_fee_lines
                        'invoice_line_ids': oqood_invoice_line
                    })
                admin_fee_lines = []
                if data.asset_project_id.admin_fee_ledger_id and data.asset_project_id.admin_fee:
                    admin_fee_lines.append ((0, 0, {'name': "admin fee of" + str(data.name),
                                                     'asset_project_id': data.asset_project_id.id,
                                                     'property_id': data.property_id.id,
                                                     'account_id': data.asset_project_id.admin_fee_ledger_id.id,
                                                     'quantity': 1,
                                                     # 'product_uom': 1,
                                                     'price_unit': data.asset_project_id.admin_fee}))
                if data.asset_project_id.vat_input_ledger_id and data.asset_project_id.vat_input_amount:
                    admin_fee_lines.append ((0, 0, {'name': "admin fee of" + str(data.name),
                                                     'asset_project_id': data.asset_project_id.id,
                                                     'property_id': data.property_id.id,
                                                     'account_id': data.asset_project_id.vat_input_ledger_id.id,
                                                     'quantity': 1,
                                                     # 'product_uom': 1,
                                                     'price_unit': data.asset_project_id.vat_input_amount}))
                if data.asset_project_id.other_income_ledger_id and data.asset_project_id.other_income_amount:
                    admin_fee_lines.append ((0, 0, {'name': "admin fee of" + str(data.name),
                                                     'asset_project_id': data.asset_project_id.id,
                                                     'property_id': data.property_id.id,
                                                     'account_id': data.asset_project_id.other_income_ledger_id.id,
                                                     'quantity': 1,
                                                     # 'product_uom': 1,
                                                     'price_unit': data.asset_project_id.other_income_amount}))
                if data.asset_project_id.admin_fee_ledger_id:
                    admin_fee_rec = self.env['account.move'].create({
                        'partner_id': data.partner_id.id,
                        'asset_project_id': data.asset_project_id.id,
                        'property_id': data.property_id.id,
                        'invoice_user_id': data.user_id.id,
                        'team_id': data.team_id.id,
                        'company_id': self.env.user.company_id.id,
                        'move_type': 'out_invoice',
                        # 'account_id': data.partner_id.property_account_receivable_id.id,
                        'invoice_date': datetime.now().strftime('%Y-%m-%d'),
                        'state': 'draft',
                        'invoice_line_ids': admin_fee_lines
                    })
                inv_ids = []
                if oqood_fee_rec:
                    oqood_fee_rec.action_post()
                    inv_ids.append(oqood_fee_rec.id)
                if admin_fee_rec:
                    admin_fee_rec.action_post()
                    inv_ids.append(admin_fee_rec.id)
                if inv_ids:
                    data.write({'other_charges_inv_ids': [(6, 0, inv_ids)]})
                self.env.context = dict(self.env.context)
                self.env.context.update({'from_method': True})
                data.onchange_asset_project_id()
                data.property_id.write({'state': 'sold'})
                # if oqood_fee_rec:
                #     oqood_fee_rec.write({'related_spa_id': rec.id})
                # if admin_fee_rec:
                #     admin_fee_rec.write({'related_spa_id': rec.id})
            else:
                raise UserError('Please Select property')



    # def action_buy_create_spa(self):
    #     for data in self:
    #         if data.property_id:
    #             data.property_id.write({'state': 'sold'})
    #         else:
    #             raise UserError('Please Select property')

    def action_is_buy_confirm_booking(self):
        self.write({'state': 'confirm_spa'})
        # self.send_booking_update_email()

    def action_discount_approval(self):
        for rec in self:
            if rec.booking_discount_id:
                if rec.booking_discount_id.min_down_payment_perc or rec.booking_discount_id.approval_require:
                    if not rec.sale_payment_schedule_ids:
                        raise UserError(
                            _("You cannot proceed for booking discount approval without creating payment schedule. Please create the payment schedule first."))
            rec.state = 'under_discount_approval'
            rec.send_booking_discount_approval_email()
            message = self.env['mail.message'].search([], order="id desc", limit=1)
            if message:
                if message.res_id == self.id and message.model == self._name and message.message_type == 'email':
                    message.res_id = False
                    # message.model = False

    def get_years(self, booking):
        year_list = []
        for data in booking.sale_payment_schedule_ids:
            if data.start_date.year not in year_list:
                year_list.append(data.start_date.year)
        return year_list

    def get_yearly_pp_vals(self, booking):
        year_dict={}
        if booking.asset_project_id.handover_date:
            if booking.sale_payment_schedule_ids:
                year_list = self.get_years(booking)
                for year in year_list:
                    year_total = 0
                    for line in booking.sale_payment_schedule_ids:
                        if line.start_date.year == year:
                            year_total += line.amount
                    year_dict[year] = year_total
                    year_dict[str(year)+'perc'] = (year_total / booking.property_inc_vat_amount) * 100
            else:
                raise UserError(_("Please define payment schedule first"))
        else:
            raise UserError(_("Please set handover date in selected project"))
        return year_dict


    def get_pp_vals(self, booking):
        total_pre_handover = 0.0
        total_post_handover = 0.0
        total_handover = 0.0
        pre_perc = 0.0
        handover_perc = 0.0
        post_perc = 0.0
        if booking.asset_project_id.handover_date:
            if booking.sale_payment_schedule_ids:
                for line in booking.sale_payment_schedule_ids:
                    if line.start_date < booking.asset_project_id.handover_date:
                        total_pre_handover += line.amount_without_vat
                    if line.start_date == booking.asset_project_id.handover_date:
                        total_handover += line.amount_without_vat
                    if line.start_date > booking.asset_project_id.handover_date:
                        total_post_handover += line.amount_without_vat
                pre_perc = (total_pre_handover / booking.price) * 100
                handover_perc = (total_handover / booking.price) * 100
                post_perc = (total_post_handover / booking.price) * 100
            else:
                raise UserError(_("Please define payment schedule first"))
        else:
            raise UserError(_("Please set handover date in selected project"))
        return {
            'pre_handover': total_pre_handover,
            'handover': total_handover,
            'post_handover': total_post_handover,
            'pre_perc': pre_perc,
            'handover_perc': handover_perc,
            'post_perc': post_perc
            }

    def get_payment_plan_creation(self, status):
        state = ''
        if status:
            if status == 'excel':
                state = 'Excel Upload'
            if status == 'custom':
                state = 'Custom Payment Plan'
            if status == 'standard':
                state = 'Standard Selection'
            if status == 'later':
                state = 'Later'
        return state

    def action_discount_approved(self):
        for rec in self:
            rec.tentative_booking_date = datetime.now().date()
            rec.state = 'tentative_booking'

    def action_tentative_booking(self):
        for rec in self:
            rec.state = 'tentative_booking'
            rec.tentative_booking_date = datetime.now().date()
            # rec.send_tentative_booking_email()

    def action_is_buy_review(self):
        print_string = ''
        check = False
        if self.partner_id:
            if not self.partner_id.mobile:
                print_string = print_string + ' Mobile'
                check = True
            if not self.partner_id.email:
                if print_string:
                    print_string = print_string + ' and'
                print_string = print_string + ' Email'
                check = True
            if not self.partner_id.street:
                if print_string:
                    print_string = print_string + ' and'
                print_string = print_string + ' Address'
                check = True
            # if not self.partner_id.passport_no:
            #     if print_string:
            #         print_string = print_string + ' and'
            #     print_string = print_string + ' Passport No'
            #     check = True
            # if not self.partner_id.passport_expiry_date:
            #     if print_string:
            #         print_string = print_string + ' and'
            #     print_string = print_string + ' Passport Expiry Date'
            #     check = True
            # if not self.partner_id.nationality:
            #     if print_string:
            #         print_string = print_string + ' and'
            #     print_string = print_string + ' Nationality'
            #     check = True
        if check:
            raise UserError(_("Please Set %s in partner profile") % (print_string,))
        if not self.sale_payment_schedule_ids:
            raise UserError(_("Please define payment schedule first"))

        if self.asset_project_id.handover_date:
            total_pre_handover = 0.0
            total_post_handover = 0.0
            pre_perc = 0.0
            post_perc = 0.0
            for line in self.sale_payment_schedule_ids:
                if line.start_date <= self.asset_project_id.handover_date:
                    total_pre_handover += line.amount_without_vat
                if line.start_date > self.asset_project_id.handover_date:
                    total_post_handover += line.amount_without_vat
                if self.asset_project_id.installment_date_max:
                    if line.start_date > self.asset_project_id.installment_date_max:
                        raise UserError(_("Installment date is greater then Instalment Date Maximum"))
                pre_perc = (total_pre_handover / self.price) * 100
                post_perc = (total_post_handover / self.price) * 100
            if self.asset_project_id.payment_plan_pre_handover_prec:
                if pre_perc != self.asset_project_id.payment_plan_pre_handover_prec:
                    raise UserError(_("Payment Plan Pre Handover % is not equal to Calculated %"))
                if pre_perc != self.asset_project_id.payment_plan_pre_handover_prec:
                    raise UserError(_("Hanover Date % is not equal to Calculated %"))

            if self.asset_project_id.payment_plan_post_handover_prec:
                if post_perc != self.asset_project_id.payment_plan_post_handover_prec:
                    raise UserError(_("Payment Plan Post Handover % is not equal to Calculated %"))
        ctx = dict(
            default_name="Are You Sure, You Have Reviewed All The Data , Payment Schedule, Price and other things",
            default_booking_id=self.id
        )
        return {
            'name': _('Review'),
            # 'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'is.buy.review',
            'view_id': self.env.ref('spa_customizations.is_buy_review_wizard').id,
            'type': 'ir.actions.act_window',
            'context': ctx,
            'target': 'new'
        }

    def open_action_cancel(self):
        # active_ids = self.env.context.get('active_ids', [])
        ctx = dict(
            default_sale_order_id=self.id,
        )
        return {
            'name': _('Cancel SPA'),
            'view_mode': 'form',
            'res_model': 'cancel.spa.wiz',
            'view_id': self.env.ref('spa_customizations.cancel_spa_wizard_view').id,
            'type': 'ir.actions.act_window',
            'context': ctx,
            'target': 'new'
        }
    # @api.depends('add_charges_ids','add_charges_ids.state','add_charges_ids.line_ids','add_charges_ids.line_ids.reconciled_amount')
    # def get_other_received(self):
    #     for rec in self:
    #         total_chrges_received = 0
    #         if rec.add_charges_ids:
    #             for fline in rec.add_charges_ids:
    #                 if fline.state == 'posted':
    #                     for sline in fline.line_ids:
    #                         total_chrges_received += sline.reconciled_amount
    #         rec.other_received = total_chrges_received

    @api.depends('total_receipts', 'total_spa_value')
    def compute_receipts_perc(self):
        for rec in self:
            total = 1
            if rec.total_spa_value:
                total = rec.total_spa_value
            rec.receipts_perc = (rec.total_receipts / total) * 100

    @api.depends('pending_balance', 'total_spa_value')
    def compute_pending_balance_perc(self):
        for rec in self:
            total = 1
            if rec.total_spa_value:
                total = rec.total_spa_value
            rec.pending_balance_perc = (rec.pending_balance / total) * 100

    @api.depends('total_spa_value', 'total_receipts')
    def compute_pending_balance(self):
        for rec in self:
            pb = rec.total_spa_value - rec.total_receipts
            if pb > 0:
                rec.pending_balance = pb
            else:
                rec.pending_balance = 0

    @api.depends('add_charges_ids', 'add_charges_ids.state', 'less_charges_ids', 'less_charges_ids.state')
    def compute_other_charges(self):
        for rec in self:
            total_adds = 0
            total_less = 0
            for adds in rec.add_charges_ids:
                if adds.state == 'posted':
                    total_adds += adds.amount_total
            for less in rec.less_charges_ids:
                if less.state == 'posted':
                    total_less += less.amount_total
            total = total_adds - total_less
            rec.other_charges = total

    @api.model
    def old_other_charges(self):
        for rec in self.search([]):
            total_adds = 0
            total_less = 0
            for adds in rec.add_charges_ids:
                if adds.state == 'posted':
                    total_adds += adds.amount_total
            for less in rec.less_charges_ids:
                if less.state == 'posted':
                    total_less += less.amount_total
            total = total_adds - total_less
            rec.other_charges = total

    @api.model
    def change_currency(self):
        query = "UPDATE sale_order SET currency_id = 130 WHERE currency_id != 130;"
        self._cr.execute(query)
        self._cr.commit()

    @api.model
    def change_currency_partner(self):
        query = "Update product_pricelist set currency_id=130;"
        self._cr.execute(query)
        self._cr.commit()

    @api.model
    def map_old_booking_number(self):
        query = "UPDATE sale_order SET booking_number = old_booking_number WHERE booking_number is null"
        self._cr.execute(query)
        self._cr.commit()

    @api.depends('un_matured_pdcs', 'hold_pdcs', 'deposited_pdcs', 'bounced_pdcs')
    def compute_unsecured_collections(self):
        for o in self:
            o.total_unsecured_collections = o.un_matured_pdcs + o.hold_pdcs + o.deposited_pdcs + o.bounced_pdcs

    @api.depends('oqood_received', 'oqood_fee')
    def due_oqood(self):
        for rec in self:
            if rec.oqood_fee - rec.oqood_received > 0:
                rec.balance_due_oqood = rec.oqood_fee - rec.oqood_received
            else:
                rec.balance_due_oqood = 0

    @api.depends('admin_received', 'admin_fee')
    def due_admin(self):
        for rec in self:
            if rec.admin_fee - rec.admin_received > 0:
                rec.balance_due_admin = rec.admin_fee - rec.admin_received
            else:
                rec.balance_due_admin = 0

    @api.depends('other_charges','other_received')
    def due_other(self):
        for rec in self:
            rec.balance_due_other = rec.other_charges - rec.other_received

    # @api.depends('total_receipts', 'amount_till_date','oqood_fee','admin_fee','other_charges','paid_installments')
    @api.depends('total_receipts', 'amount_till_date', 'oqood_fee', 'admin_fee', 'paid_installments')
    def compute_installment_balance_pending(self):
        for rec in self:
            # temp = rec.amount_till_date + rec.admin_fee + rec.oqood_fee + rec.other_charges
            temp = rec.amount_till_date + rec.admin_fee + rec.oqood_fee
            rec.instalmnt_bls_pend_plus_admin_oqood = temp
            ibp = rec.amount_till_date - rec.paid_installments
            if ibp < 0:
                rec.installment_balance_pending = 0
            else:
                rec.installment_balance_pending = ibp

    @api.depends('matured_pdcs', 'instalmnt_bls_pend_plus_admin_oqood')
    def compute_balance_due(self):
        for rec in self:
            result = rec.instalmnt_bls_pend_plus_admin_oqood - rec.matured_pdcs
            if result > 0:
                rec.balance_due_collection = result
            else:
                rec.balance_due_collection = 0

    @api.depends('receipt_ids', 'receipt_ids.amount', 'receipt_ids.state')
    def compute_receipt_total(self):
        for rec in self:
            if rec.receipt_ids:
                total = 0.00
                matured = 0.00
                unmatured = 0.00
                hold = 0.00
                deposited = 0.00
                bounced = 0.00
                withdraw = 0.00
                for receipt in rec.receipt_ids:
                    if receipt.state not in ['draft', 'proforma', 'cancelled', 'refused', 'rejected', 'replaced',
                                             'outsourced'] and receipt.payment_type == 'inbound':
                        total += receipt.amount
                    if receipt.state in ['paid_unposted', 'posted'] and receipt.payment_type == 'inbound':
                        matured += receipt.amount
                    if receipt.state in ['pending', 'collected'] and receipt.payment_type == 'inbound':
                        unmatured += receipt.amount
                    if receipt.state == 'hold' and receipt.payment_type == 'inbound':
                        hold += receipt.amount
                    if receipt.state == 'deposited' and receipt.payment_type == 'inbound':
                        deposited += receipt.amount
                    if receipt.state == 'outsourced' and receipt.payment_type == 'inbound':
                        withdraw += receipt.amount
                    if receipt.state == 'refused' and receipt.payment_type == 'inbound':
                        bounced += receipt.amount
                rec.total_receipts = total
                rec.matured_pdcs = matured
                rec.un_matured_pdcs = unmatured
                rec.hold_pdcs = hold
                rec.deposited_pdcs = deposited
                rec.withdraw_pdcs = withdraw
                rec.bounced_pdcs = bounced

    # @api.depends('oqood_fee', 'amount_total', 'admin_fee', 'other_charges')
    @api.depends('oqood_fee', 'amount_total', 'admin_fee')
    def compute_total_spa_value(self):
        for rec in self:
            rec.total_spa_value = rec.amount_total + rec.oqood_fee + rec.admin_fee

    @api.depends('total_unsecured_collections', 'total_spa_value')
    def get_unsecured_perc(self):
        for rec in self:
            if rec.total_spa_value:
                rec.unsecured_collections_perc = (rec.total_unsecured_collections / rec.total_spa_value) * 100

    @api.depends('sale_payment_schedule_ids', 'sale_payment_schedule_ids.receipt_total')
    def get_paid_installments(self):
        for rec in self:
            if rec.sale_payment_schedule_ids:
                received_total = 0.00
                for line in rec.sale_payment_schedule_ids:
                    received_total += line.receipt_total
                rec.paid_installments = received_total

    @api.depends('matured_pdcs', 'total_spa_value')
    def get_realized_perc(self):
        for rec in self:
            if rec.total_spa_value:
                rec.matured_pdcs_perc = (rec.matured_pdcs / rec.total_spa_value) * 100

    @api.depends('paid_installments', 'amount_total')
    def get_paid_perc(self):
        for rec in self:
            if rec.amount_total:
                rec.paid_installments_perc = (rec.paid_installments / rec.amount_total) * 100

    @api.depends('vat_id')
    def get_vat_amount(self):
        for rec in self:
            rec.vat_amount = rec.price * (rec.vat_id.amount / 100)

    @api.depends('oqood_fee', 'price', 'admin_fee', 'vat_amount')
    def compute_net_receipts(self):
        for rec in self:
            rec.net_receipts = rec.price + rec.oqood_fee + rec.admin_fee + rec.vat_amount

    @api.depends('vat_amount', 'price')
    def get_property_vat_amount(self):
        for rec in self:
            rec.property_inc_vat_amount = rec.price + rec.vat_amount


    @api.depends('receipt_ids')
    def _escrow(self):
        for rec in self:
            escrow = 0
            non_escrow = 0
            for tot in rec.receipt_ids:
                if tot.sub_type.name == 'Escrow' and tot.state == 'posted':
                    escrow += tot.amount
                if tot.sub_type.name != 'Escrow' and tot.state == 'posted':
                    non_escrow += tot.amount
            rec.escrow = escrow
            rec.non_escrow = non_escrow

    @api.depends('escrow', 'total_spa_value')
    def escrow_perct(self):
        for rec in self:
            escrow_perc = 0
            if rec.total_spa_value and rec.escrow:
                escrow_perc = rec.escrow / rec.total_spa_value * 100
            rec.escrow_perc = escrow_perc

    @api.depends('non_escrow', 'total_spa_value')
    def non_escrow_perct(self):
        for rec in self:
            non_escrow_perc = 0
            if rec.total_spa_value and rec.non_escrow:
                non_escrow_perc = rec.non_escrow / rec.total_spa_value * 100
            rec.non_escrow_perc = non_escrow_perc

    @api.depends('escrow', 'non_escrow')
    def escrow_tot(self):
        for rec in self:
            rec.total_escrow = rec.escrow + rec.non_escrow

    @api.depends('total_escrow', 'total_spa_value')
    def tot_escrow_perct(self):
        for rec in self:
            total_escrow_perc = 0
            if rec.total_spa_value and rec.total_escrow:
                total_escrow_perc = rec.total_escrow / rec.total_spa_value * 100
            rec.total_escrow_perc = total_escrow_perc

    @api.depends('discount_value', 'property_price')
    def compute_discount_perc(self):
        for rec in self:
            manual_discount_perc = 0
            if rec.property_price:
                manual_discount_perc = (rec.discount_value / rec.property_price) * 100
            rec.manual_discount_perc = manual_discount_perc

    @api.depends('price', 'down_payment')
    def get_amount_after_dp(self):
        for rec in self:
            rec.property_price_after_dp = rec.price - rec.down_payment

    @api.depends('booking_discount_id', 'property_price', 'manual_discount_amount')
    def compute_discount_value(self):
        for rec in self:
            if rec.booking_discount_id:
                if rec.booking_discount_id.manual:
                    rec.manual_discount = True
                else:
                    rec.manual_discount = False
                    rec.manual_discount_amount = 0.0
            discount_value = 0
            if rec.booking_discount_id:
                if rec.manual_discount_amount:
                    discount_value = rec.manual_discount_amount
                if rec.booking_discount_id.disc_type == 'percent' and not rec.booking_discount_id.manual:
                    discount_value = (rec.booking_discount_id.value / 100) * rec.property_price
                if rec.booking_discount_id.disc_type == 'fixed' and not rec.booking_discount_id.manual:
                    discount_value = rec.booking_discount_id.value
            rec.discount_value = discount_value

    @api.depends('agent_commission_type_id', 'agent_commission_type_id.percentage_value', 'agent_discount_perc')
    def compute_net_comm(self):
        for rec in self:
            rec.net_commission_perc = rec.agent_commission_type_id.percentage_value - rec.agent_discount_perc

    @api.depends('net_commission_perc', 'price')
    def compute_net_commission_sp(self):
        for rec in self:
            rec.net_commission_sp = (rec.net_commission_perc / 100) * rec.price

    def compute_is_invoiced(self):
        for rec in self:
            check = False
            for line in rec.sale_payment_schedule_ids:
                if line.inv:
                    check = True
            rec.invoiced_schedule_check = check

    def compute_schedule_total(self):
        for rec in self:
            total = 0.0
            for line in rec.sale_payment_schedule_ids:
                total += line.amount
            rec.schedule_total = total

    @api.depends('price', 'down_payment_perc')
    def get_down_payment(self):
        for rec in self:
            rec.down_payment = (rec.down_payment_perc / 100) * rec.price

    @api.depends('price', 'each_installment_perc')
    def get_each_installment(self):
        for rec in self:
            rec.each_installment_amount = (rec.each_installment_perc / 100) * rec.price

    @api.depends('no_of_installment', 'each_installment_amount')
    def get_no_of_installment_amount(self):
        for rec in self:
            rec.no_of_installment_amount = rec.each_installment_amount * rec.no_of_installment

    @api.depends('price', 'handover_perc')
    def get_handover(self):
        for rec in self:
            rec.handover_amount = (rec.handover_perc / 100) * rec.price

    @api.depends('each_installment_perc', 'handover_perc', 'down_payment_perc', 'no_of_installment')
    def get_remaining(self):
        for rec in self:
            rec.remaining_perc = 100 - (
                    rec.each_installment_perc * rec.no_of_installment) - rec.handover_perc - rec.down_payment_perc

    @api.depends('price', 'remaining_perc')
    def get_remaining_amount(self):
        for rec in self:
            rec.remaining_amount = (rec.remaining_perc / 100) * rec.price

    @api.depends('remaining_no_of_installment', 'remaining_amount')
    def get_remaining_installments_amount(self):
        for rec in self:
            if rec.remaining_no_of_installment:
                rec.remaining_installments_amount = rec.remaining_amount / rec.remaining_no_of_installment
            else:
                rec.remaining_installments_amount = 0

    @api.model
    def create(self, vals):
        res = super(SaleOrder, self).create(vals)
        if vals.get('booking_number', _(0)) == _(0):
            res.booking_number = self.env['ir.sequence'].next_by_code('crm.booking')
        total = 0.0
        if self.sale_payment_schedule_ids and self.amount_total and self.amount_total:
            for line in self.sale_payment_schedule_ids:
                total += line.amount
            if round(total) >= round(self.amount_total - 1) and round(total) <= round(
                    self.amount_total + 1):
                pass
            # else:
                # raise UserError(_("Installments total is not equal to the Property Sale Price"))
        total_pp = 0.0
        if self.payment_plan_ids:
            for line in self.payment_plan_ids:
                total_pp += line.amount
            if round(total_pp) >= round(self.amount_total - 1) and round(total_pp) <= round(
                    self.amount_total + 1):
                pass
            # else:
            #     raise UserError(_("DLD Schedule total is not equal to the Property Sale Price"))
        return res

    def write(self, vals):
        res = super(SaleOrder, self).write(vals)
        total = 0.0
        # line_total = 0
        # for l in self.order_line:
        #     line_total+= l.price_unit
        # if not vals.get('property_id') and line_total != self.price:
        #     raise UserError(_("The proprty price has beed changed after creation of this booking, you are requested to remove\n"
        #                       "the property number and select again to update SPA Line."))
        if self.sale_payment_schedule_ids and self.amount_total and self.amount_total:
            for line in self.sale_payment_schedule_ids:
                total += line.amount
            if round(total) >= round(self.amount_total - 1) and round(total) <= round(
                    self.amount_total + 1):
                pass
            # else:
            #     raise UserError(_("Installments total is not equal to the Property Sale Price"))
        total_pp = 0.0
        if self.payment_plan_ids:
            for line in self.payment_plan_ids:
                total_pp += line.amount
            if round(total_pp) >= round(self.amount_total - 1) and round(total_pp) <= round(
                    self.amount_total + 1):
                pass
            # else:
            #     raise UserError(_("DLD Schedule total is not equal to the Property Sale Price"))
        return res

    def action_view_reciepts(self):
        ctx = {'default_partner_id': self.partner_id.id, 'default_spa_id': self.id,
               'default_asset_project_id': self.asset_project_id.id,
               'default_property_id': self.property_id.id, 'default_payment_type': 'inbound',
               'default_partner_type': 'customer', 'search_default_inbound_filter': 1}

        return {
            'name': _("Receipts"),
            'view_id': False,
            'view_mode': 'tree,form',
            'context': ctx,
            'domain': [('id', 'in', self.receipt_ids.ids)],
            'res_model': 'account.payment',
            'type': 'ir.actions.act_window'
        }

    def action_view_invoices(self):
        # ctx = {'default_partner_id': self.partner_id.id, 'default_spa_id': self.id,
        #        'default_asset_project_id': self.asset_project_id.id,
        #        'default_property_id': self.property_id.id, 'default_payment_type': 'inbound',
        #        'default_partner_type': 'customer', 'search_default_inbound_filter': 1}

        return {
            'name': _("Invoices"),
            # 'view_id': self.env.ref('account.view_out_invoice_tree').id,
            'view_mode': 'tree,form',
            # 'context': ctx,
            'domain': [('id', 'in', self.all_invoice_ids.ids)],
            'res_model': 'account.move',
            'type': 'ir.actions.act_window',
            'context': {
                'tree_view_ref': 'account.view_out_invoice_tree',
                'create': False,
                'edit': False,
                'duplicate': False
            }
        }

    def action_view_payments(self):
        ctx = {'default_partner_id': self.partner_id.id, 'default_spa_payment_id': self.id,
               'default_asset_project_id': self.asset_project_id.id,
               'default_property_id': self.property_id.id, 'default_payment_type': 'outbound',
               'default_partner_type': 'supplier', 'search_default_outbound_filter': 1}

        return {
            'name': _("FGR Payments"),
            'view_id': False,
            'view_mode': 'tree,form',
            'context': ctx,
            'domain': [('id', 'in', self.payments_ids.ids)],
            'res_model': 'account.payment',
            'type': 'ir.actions.act_window'
        }

    def get_related_attachments(self):
        for rec in self:
            comm_ids = []
            spa = []
            comm_ids = rec.env['commission.invoice'].search([('related_spa_id', '=', rec.id)]).ids
            comm_att = rec.env['ir.attachment'].search(
                [('res_model', '=', 'commission.invoice'), ('res_id', 'in', comm_ids)])
            attachments = rec.env['ir.attachment'].search([('res_model', '=', 'sale.order'), ('res_id', '=', rec.id)])
            tree_id = self.env.ref('spa_customizations.view_attachment_tree_on_model').id
            all_attach = comm_att.ids + attachments.ids
            print(attachments.ids)
            return {
                'name': _('Attachments'),
                'view_type': 'form',
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

    def view_payment_schedule(self):
        for rec in self:
            # attachments = rec.env['ir.attachment'].search(
            #     [('res_model', '=', 'fgr.payment.request'), ('res_id', '=', rec.id)])
            # booking_att = rec.env['ir.attachment'].search(
            #     [('res_model', '=', 'sale.order'), ('res_id', '=', rec.related_booking_id.id)])
            # so_att = rec.env['ir.attachment'].search([('res_model', '=', 'sale.order'), ('res_id', '=', rec.spa_id.id)])
            # tree_id = self.env.ref('sd_settle_and_attachment_req.view_attachment_tree_on_model').id
            # all_attach = booking_att.ids + so_att.ids + attachments.ids

            return {
                'name': _('Installments'),
                'view_mode': 'tree',
                'view_id': self.env.ref('spa_customizations.sale_rent_tree_field').id,
                'res_model': 'sale.rent.schedule',
                'type': 'ir.actions.act_window',
                'domain': [('id', 'in', rec.sale_payment_schedule_ids.ids)],
                # 'context': {
                #     'create': False,
                #     'edit': False
                # },
            }

    def action_remove_schedule(self):
        ctx = dict(
            default_name="This action will remove the full installment plan. Do you still want to proceed?",
            default_booking_id=self.id
        )
        return {
            'name': _('Remove Schedule'),
            'view_mode': 'form',
            'res_model': 'wiz.remove.schedule',
            'view_id': self.env.ref('spa_customizations.remove_schedule_view_wizard').id,
            'type': 'ir.actions.act_window',
            'context': ctx,
            'target': 'new'
        }

    def download_template(self):
        path_directory = os.path.dirname(os.path.realpath(__file__))
        self.file2 = base64.b64encode(open(path_directory + "/template.xlsx", "rb").read())
        return {
            'type': 'ir.actions.act_url',
            'name': 'template',
            'url': '/web/content/sale.order/%s/file2/template.xlsx?download=true' % (self.id),
        }

    def import_srs(self):
        if not self.file:
            raise UserError(_("Please attach template file"))
        wb = open_workbook(file_contents=base64.b64decode(self.file))
        ws = wb.sheets()[0]
        for s in wb.sheets():
            values = []
            for row in range(s.nrows):
                print(row, 'is row')
                col_value = []
                dict = {}
                for col in range(s.ncols):
                    value = (s.cell(row, col).value)
                    try:
                        value = str(value)
                    except:
                        pass
                    if row > 0 and col in range(0, 5):
                        if col == 0 and value != '':
                            val = datetime.strptime(value, '%d/%m/%Y')
                            dict['start_date'] = val
                        if col == 1 and value != '':
                            dict['amount_without_vat'] = value
                        if col == 2 and value != '':
                            dict['value'] = value
                        if col == 3 and value != '':
                            dict['note'] = value
                    col_value.append(value)
                if row > 0 and dict != {}:
                    dict['sale_id'] = self.id
                    dict['partner_id'] = self.partner_id.id
                    dict['property_id'] = self.property_id.id
                    dict['asset_property_id'] = self.asset_project_id.id
                    dict['vat_id'] = self.vat_id.id
                    dict['sale_type'] = self.sale_type
                    self.env['sale.rent.schedule'].create(dict)
                values.append(col_value)
            print(values)
        total = 0.0
        for line in self.sale_payment_schedule_ids:
            total += line.amount
        self.schedule_total = total
        if round(total) >= round(self.amount_total - 1) and round(total) <= round(self.amount_total + 1):
            print(total)
        # else:
        #     raise UserError(_("Installments total is not equal to the Property Sale Price"))
        self.import_done = True

    @api.depends('discount_value', 'property_price', 'agent_discount_perc')
    def compute_price(self):
        for rec in self:
            agent_discount = 0
            if rec.agent_discount_perc:
                agent_discount = (rec.agent_discount_perc / 100) * rec.property_price
            rec.price = rec.property_price - rec.discount_value - agent_discount

    @api.depends('amount_total', 'property_id', 'property_id.gfa_feet')
    def _compute_property_price_per_sqf(self):
        for rec in self:
            if rec.property_id.gfa_feet:
                rec.property_price_per_sqf = rec.amount_total / rec.property_id.gfa_feet

    @api.depends('property_id', 'price')
    def _get_4_percent_of_property(self):
        for rec in self:
            rec.property_four_percent = rec.price * 0.04
            rec.oqood_fee = rec.price * 0.04

    @api.onchange('property_id', 'vat_id', 'price')
    def onchange_property(self):
        self.order_line = False
        odr_lines = self.order_line
        if self.property_id:
            odr_lines = odr_lines.new({
                'name': self.property_id.name,
                'property_id': self.property_id.id,
                'price_unit': self.price,
                'product_uom_qty': 1,
                'tax_id': [(6, 0, self.vat_id.ids)],
            })
        self.order_line = odr_lines

    @api.onchange('asset_project_id')
    def onchange_asset_project_id(self):
        self.schedule_a = self.asset_project_id.schedule_a
        self.schedule_b = self.asset_project_id.schedule_b
        self.schedule_c = self.asset_project_id.schedule_c
        self.schedule_d = self.asset_project_id.schedule_d
        self.schedule_e = self.asset_project_id.schedule_e
        self.schedule_f = self.asset_project_id.schedule_f
        self.schedule_g = self.asset_project_id.schedule_g
        self.schedule_h = self.asset_project_id.schedule_h
        self.schedule_i = self.asset_project_id.schedule_i
        self.schedule_a_eng = self.asset_project_id.schedule_a_eng
        self.schedule_b_eng = self.asset_project_id.schedule_b_eng
        self.schedule_c_eng = self.asset_project_id.schedule_c_eng
        self.schedule_d_eng = self.asset_project_id.schedule_d_eng
        self.schedule_e_eng = self.asset_project_id.schedule_e_eng
        self.schedule_f_eng = self.asset_project_id.schedule_f_eng
        self.schedule_g_eng = self.asset_project_id.schedule_g_eng
        self.schedule_h_eng = self.asset_project_id.schedule_h_eng
        self.schedule_i_eng = self.asset_project_id.schedule_i_eng
        booking_discount_ids = self.env['booking.discount'].search(
            [('asset_project_id', '=', self.asset_project_id.id)])
        payment_schedule_ids = self.env['payment.schedule'].search(
            [('asset_project_id', '=', self.asset_project_id.id)])
        property_ids = self.env['account.asset.asset'].search(
            [('state', '=', 'draft'), ('parent_id', '=', self.asset_project_id.id)])
        sales_terms_ids = self.env['sale.payment.term'].search(
            [('asset_project_id', '=', self.asset_project_id.id)])
        self.sale_term_id = self.asset_project_id.sale_term_id.id
        self.payment_plan_ids = False
        if not self.env.context.get('from_method'):
            self.property_id = False
        pp_lines = self.payment_plan_ids
        if self.asset_project_id:
            for l in self.asset_project_id.payment_plan_ids:
                pp_lines += pp_lines.new({
                    'name': l.name,
                    'percentage': l.percentage,
                    'payment_date_disc': l.payment_date_disc,
                    'sale_id': self.id,
                })
        if pp_lines:
            self.payment_plan_ids = pp_lines
        self.admin_fee = self.asset_project_id.admin_fee + self.asset_project_id.vat_input_amount + self.asset_project_id.other_income_amount
        return {'domain': {'property_id': [('id', 'in', property_ids.ids)],
                           'booking_discount_id': [('id', 'in', booking_discount_ids.ids)],
                           'payment_schedule_id': [('id', 'in', payment_schedule_ids.ids)],
                           'sale_term_id': [('id', 'in', sales_terms_ids.ids)] }}

    @api.depends('create_date', 'booking_date')
    def compute_booking_days(self):
        for rec in self:
            current_date = datetime.now().date()
            if rec.booking_date:
                dates_diff = current_date - rec.booking_date.date()
                rec.booking_days = dates_diff.days

    def create_payment_schedule(self):
        if self.payment_plan_creation == 'standard':
            total_payment = self.price
            if self.sale_payment_schedule_ids:
                self.sale_payment_schedule_ids.unlink()
            if self.payment_schedule_id:
                if not self.installment_start_date:
                    raise UserError(_("Please set installment start date first."))
                new_date = self.installment_start_date
                print(new_date)
                print(self.installment_start_date)
                list_rent = []
                last_line = 0
                c = 1
                tax_lines = self.sale_payment_schedule_ids
                if self.down_payment > 0:
                    new_date = new_date

                    total_payment = total_payment - self.down_payment
                    tax_lines += tax_lines.new({
                        'start_date': str(new_date),
                        'amount_without_vat': self.down_payment,
                        'pen_amt': self.down_payment,
                        'note': 'Down Payment',
                        'vat_id': self.vat_id.id,
                        'sale_type': self.sale_type,
                        'partner_id': self.partner_id.id,
                        'property_id': self.property_id.id,
                        'asset_property_id': self.asset_project_id.id,
                    })
                total_manual = 0
                percent_minus = 0
                all_loops = 0
                per = 0
                bb = 0
                # for c in self.payment_schedule_id.payment_criteria_ids:
                #
                #     if c.period == 'no_of_days':
                #         c.id
                # self.sorted(sorted(key=lambda r: self.payment_schedule_id.payment_criteria_ids.no_of_days))
                for criteria in self.payment_schedule_id.payment_criteria_ids:

                    if criteria.value == 'fixed' or criteria.value == 'percent' and criteria.amount_get == 'manual':
                        if criteria.value_amount > 0:
                            # self.down_payment = criteria.value_amount
                            if criteria.value == 'percent':
                                percentage = criteria.value_amount
                                percent_minus += percentage
                                percent_value = percentage / 100 * total_payment
                                total_manual += percent_value

                                bb = percent_minus
                            else:
                                percent_value = criteria.value_amount
                                total_manual = criteria.value_amount
                                total_payment = total_payment - percent_value
                            if criteria.period == 'monthly':
                                new_date = new_date + relativedelta(months=1)
                            elif criteria.period == 'quarterly':
                                new_date = new_date + relativedelta(months=3)
                            elif criteria.period == 'bi_annulay':
                                new_date = new_date + relativedelta(months=6)
                            elif criteria.period == 'annual':
                                new_date = new_date + relativedelta(months=12)
                            elif criteria.period == 'no_of_days':
                                if self.installment_start_date:
                                    installment_date = self.installment_start_date + relativedelta(
                                        days=criteria.no_of_days)
                                else:
                                    new_date = new_date + relativedelta(days=criteria.no_of_days)
                            elif criteria.period == 'custom_date':
                                new_date = criteria.custom_date
                            else:
                                raise UserError('Please select Period on Payment Schedule')
                            # total_payment = total_payment - percent_value
                            tax_lines += tax_lines.new({
                                'start_date': str(
                                    installment_date) if self.installment_start_date and criteria.period == 'no_of_days' else str(
                                    new_date),
                                'amount_without_vat': percent_value,
                                'calculation': criteria.value,
                                'value': criteria.value_amount,
                                'vat_id': self.vat_id.id,
                                'sale_type': self.sale_type,
                                'partner_id': self.partner_id.id,
                                'property_id': self.property_id.id,
                                'asset_property_id': self.asset_project_id.id,
                            })
                    payment_without_down = total_payment
                    if criteria.value == 'percent' and criteria.amount_get == 'auto':
                        a = criteria.value_amount
                        count = (100 - percent_minus) % criteria.value_amount

                        total_loop = (100 - percent_minus) / criteria.value_amount

                        # total_payment = total_payment - total_manual
                        if criteria.period in ['quarterly', 'monthly', 'bi_annulay', 'annual']:
                            if criteria.no_of_period > 0:
                                per = criteria.value_amount * criteria.no_of_period + per + bb
                                bb = 0
                                percent_minus = percent_minus + (criteria.value_amount * criteria.no_of_period)
                                # total_loop = (100 - percent_minus) / criteria.value_amount
                                total_loop = criteria.no_of_period

                                all_loops = all_loops + criteria.no_of_period
                                count = 0
                            if criteria.no_of_period == 0:
                                # all_loops = all_loops + criteria.no_of_period
                                total_loop = (100 - percent_minus) / criteria.value_amount

                                count = (100 - percent_minus) % criteria.value_amount
                                if not count.is_integer():
                                    count = round(count, 2)

                        if count > 0:
                            total_loop -= 2
                            last_line = count + criteria.value_amount
                            c = 0

                        while total_loop >= c:
                            if count == 0:
                                percentage = criteria.value_amount
                                percent_value = percentage / (100) * total_payment
                                total_loop = total_loop - 1
                                if criteria.period == 'monthly':
                                    new_date = new_date + relativedelta(months=1)
                                elif criteria.period == 'quarterly':
                                    new_date = new_date + relativedelta(months=3)
                                elif criteria.period == 'bi_annulay':
                                    new_date = new_date + relativedelta(months=6)
                                elif criteria.period == 'annual':
                                    new_date = new_date + relativedelta(months=12)
                                elif criteria.period == 'no_of_days':
                                    if self.installment_start_date:
                                        installment_date = self.installment_start_date + relativedelta(
                                            days=criteria.no_of_days)
                                    else:
                                        new_date = new_date + relativedelta(days=criteria.no_of_days)
                                elif criteria.period == 'custom_date':
                                    new_date = criteria.custom_date
                                else:
                                    raise UserError('Please select Period on Payment Schedule')
                                tax_lines += tax_lines.new({
                                    'start_date': str(
                                        installment_date) if self.installment_start_date and criteria.period == 'no_of_days' else str(
                                        new_date),
                                    'amount_without_vat': percent_value,
                                    'calculation': criteria.value,
                                    'value': criteria.value_amount,
                                    'vat_id': self.vat_id.id,
                                    'sale_type': self.sale_type,
                                    'partner_id': self.partner_id.id,
                                    'property_id': self.property_id.id,
                                    'asset_property_id': self.asset_project_id.id,
                                    'sale_id': self.id
                                })
                            if count > 0:
                                percentage = criteria.value_amount
                                percent_value = percentage / 100 * total_payment
                                total_loop = total_loop - 1
                                if criteria.period == 'monthly':
                                    new_date = new_date + relativedelta(months=1)
                                elif criteria.period == 'quarterly':
                                    new_date = new_date + relativedelta(months=3)
                                elif criteria.period == 'bi_annulay':
                                    new_date = new_date + relativedelta(months=6)
                                elif criteria.period == 'annual':
                                    new_date = new_date + relativedelta(months=12)
                                elif criteria.period == 'no_of_days':
                                    if self.installment_start_date:
                                        installment_date = self.installment_start_date + relativedelta(
                                            days=criteria.no_of_days)
                                    else:
                                        new_date = new_date + relativedelta(days=criteria.no_of_days)
                                elif criteria.period == 'custom_date':
                                    new_date = criteria.custom_date
                                else:
                                    raise UserError('Please select Period on Payment Schedule')
                                tax_lines += tax_lines.new({
                                    'start_date': str(
                                        installment_date) if self.installment_start_date and criteria.period == 'no_of_days' else str(
                                        new_date),
                                    'amount_without_vat': percent_value,
                                    'calculation': criteria.value,
                                    'value': criteria.value_amount,
                                    'vat_id': self.vat_id.id,
                                    'sale_type': self.sale_type,
                                    'partner_id': self.partner_id.id,
                                    'property_id': self.property_id.id,
                                    'asset_property_id': self.asset_project_id.id,
                                })
                        if last_line > criteria.value_amount:
                            percent_value = last_line / 100 * total_payment
                            if criteria.period == 'monthly':
                                new_date = new_date + relativedelta(months=1)
                            elif criteria.period == 'quarterly':
                                new_date = new_date + relativedelta(months=3)
                            elif criteria.period == 'bi_annulay':
                                new_date = new_date + relativedelta(months=6)
                            elif criteria.period == 'annual':
                                new_date = new_date + relativedelta(months=12)
                            elif criteria.period == 'no_of_days':
                                if self.installment_start_date:
                                    installment_date = self.installment_start_date + relativedelta(
                                        days=criteria.no_of_days)
                                else:
                                    new_date = new_date + relativedelta(days=criteria.no_of_days)
                            elif criteria.period == 'custom_date':
                                new_date = criteria.custom_date
                            else:
                                raise UserError('Please select Period on Payment Schedule')
                            tax_lines += tax_lines.new({
                                'start_date': str(
                                    installment_date) if self.installment_start_date and criteria.period == 'no_of_days' else str(
                                    new_date),
                                'amount_without_vat': percent_value,
                                'calculation': criteria.value,
                                'value': last_line,
                                'vat_id': self.vat_id.id,
                                'sale_type': self.sale_type,
                                'partner_id': self.partner_id.id,
                                'property_id': self.property_id.id,
                                'asset_property_id': self.asset_project_id.id,
                            })
                if tax_lines:
                    self.sale_payment_schedule_ids = tax_lines
                    self.is_payment_schedule = True
        if self.payment_plan_creation == 'custom':
            total_amt = 0.0
            if self.sale_payment_schedule_ids:
                self.sale_payment_schedule_ids.unlink()
            if not self.installment_start_date:
                raise UserError(_("Please set installment start date first."))
            new_date = self.installment_start_date

            sched_lines = self.sale_payment_schedule_ids
            if self.down_payment > 0:
                sched_lines += sched_lines.new({
                    'start_date': str(new_date),
                    'amount_without_vat': self.down_payment,
                    'note': 'Down Payment',
                    'vat_id': self.vat_id.id,
                    'sale_type': self.sale_type,
                    'value': self.down_payment_perc,
                    'partner_id': self.partner_id.id,
                    'property_id': self.property_id.id,
                    'asset_property_id': self.asset_project_id.id,
                })
                total_amt += self.down_payment
            no_of_installments = self.no_of_installment
            if not self.no_of_installment:
                raise UserError(_("Please set No of Installments first."))
            total = 0
            last_date = False
            while no_of_installments > 0:
                if self.each_installment_amount:
                    if self.installment_interval == 'monthly':
                        new_date = new_date + relativedelta(months=1)
                    elif self.installment_interval == 'quarterly':
                        new_date = new_date + relativedelta(months=3)
                    elif self.installment_interval == 'semi_annually':
                        new_date = new_date + relativedelta(months=6)
                    elif self.installment_interval == 'yearly':
                        new_date = new_date + relativedelta(months=12)
                    elif self.installment_interval == 'custom_days':
                        new_date = new_date + relativedelta(days=self.installment_days_interval)
                    else:
                        raise UserError('Please select Interval on Payment Schedule')
                    total += self.each_installment_amount
                    sched_lines += sched_lines.new({
                        'start_date': str(new_date),
                        'amount_without_vat': self.each_installment_amount,
                        'vat_id': self.vat_id.id,
                        'sale_type': self.sale_type,
                        'value': self.each_installment_perc,
                        'partner_id': self.partner_id.id,
                        'property_id': self.property_id.id,
                        'asset_property_id': self.asset_project_id.id,
                    })
                    total_amt += self.each_installment_amount
                    no_of_installments -= 1
                last_date = new_date
            if self.handover_amount > 0:
                if self.asset_project_id.handover_date:
                    new_date = self.asset_project_id.handover_date
                sched_lines += sched_lines.new({
                    'start_date': str(new_date),
                    'amount_without_vat': self.handover_amount,
                    'note': 'Handover',
                    'vat_id': self.vat_id.id,
                    'sale_type': self.sale_type,
                    'value': self.handover_perc,
                    'partner_id': self.partner_id.id,
                    'property_id': self.property_id.id,
                    'asset_property_id': self.asset_project_id.id,
                })
                total_amt += self.handover_amount
            if self.remaining_amount > 0:
                remaining_no_of_installment = self.remaining_no_of_installment
                if last_date:
                    if last_date < self.asset_project_id.handover_date:
                        new_date = self.asset_project_id.handover_date
                    else:
                        new_date = last_date
                if remaining_no_of_installment:
                    remaining_amount = self.remaining_amount / remaining_no_of_installment
                    remaining_percen = self.remaining_perc / remaining_no_of_installment
                    while remaining_no_of_installment > 0:
                        sched_lines += sched_lines.new({
                            'start_date': str(new_date),
                            'amount_without_vat': remaining_amount,
                            'note': 'Remaining',
                            'vat_id': self.vat_id.id,
                            'sale_type': self.sale_type,
                            'value': remaining_percen,
                            'partner_id': self.partner_id.id,
                            'property_id': self.property_id.id,
                            'asset_property_id': self.asset_project_id.id,
                        })
                        total_amt += remaining_amount
                        remaining_no_of_installment -= 1
                else:
                    sched_lines += sched_lines.new({
                        'start_date': str(new_date),
                        'amount_without_vat': self.remaining_amount,
                        'note': 'Remaining',
                        'vat_id': self.vat_id.id,
                        'sale_type': self.sale_type,
                        'value': self.remaining_perc,
                        'partner_id': self.partner_id.id,
                        'property_id': self.property_id.id,
                        'asset_property_id': self.asset_project_id.id,
                    })
                    total_amt += self.remaining_amount
            if round(total_amt) > round(self.price) + 1:
                raise UserError('Total amount exceed Property Price')
            if round(total_amt + 1) < round(self.price - 1):
                raise UserError('Total installment amount is less then Property Price')
            if sched_lines:
                self.sale_payment_schedule_ids = sched_lines
                self.is_payment_schedule = True
        if self.booking_discount_id and self.booking_discount_id.min_down_payment_perc and self.sale_payment_schedule_ids:
            if self.sale_payment_schedule_ids[0].value < self.booking_discount_id.min_down_payment_perc:
                raise UserError(_('The down payment should be greater then %s percent.') % (
                    self.booking_discount_id.min_down_payment_perc,))


class SaleOrderTemplateLine(models.Model):
    _inherit = "sale.order.template.line"

    _sql_constraints = [
        ('accountable_product_id_required',
         "CHECK(1=1)",
         "Missing required product and UoM on accountable sale quote line."),

        ('non_accountable_fields_null',
         "CHECK(1=1)",
         "Forbidden product, unit price, quantity, and UoM on non-accountable sale quote line"),
    ]


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    _sql_constraints = [
        ('accountable_required_fields',
         "CHECK(1=1)",
         "Missing required fields on accountable sale order line."),
        ('non_accountable_null_fields',
         "CHECK(1=1)",
         "Forbidden values on non-accountable sale order line"),
    ]
