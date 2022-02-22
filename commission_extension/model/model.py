# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import AccessError, UserError
from odoo.tools import float_compare
import time
from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT


class MileStone(models.Model):
    _name = "mile.stone"
    _description = "Mile-Stone"

    name = fields.Char('Name', required=True)


class AccountPaymentCriteria(models.Model):
    _name = "account.payment.criteria"
    _description = "Account Payment Criteria"

    commission_invoice_id = fields.Many2one('commission.invoice', 'Commission Invoice')
    milestone_id = fields.Many2one('mile.stone', 'Mile-Stone')
    details = fields.Char('Details')
    percentage = fields.Float('%')
    amount = fields.Float(compute='get_amount', string='Amount', store=True)

    @api.depends('commission_invoice_id', 'commission_invoice_id.total_commission_amount', 'percentage')
    def get_amount(self):
        for rec in self:
            if rec.commission_invoice_id and rec.percentage:
                rec.amount = (rec.percentage / 100) * rec.commission_invoice_id.total_commission_amount


class CommissionType(models.Model):
    _name = "commission.type"
    _description = "Commission Type"

    name = fields.Char(string='Name', required=True)
    percentage = fields.Boolean(string='Percentage')
    fixed = fields.Boolean(string='Fixed')
    percentage_value = fields.Float(string='Percentage Value')
    amount_value = fields.Float(string='Amount Value')
    asset_project_id = fields.Many2one('account.asset.asset', 'Project', domain="[('project', '=', True)]")
    property_id = fields.Many2one('account.asset.asset', string='Property')
    payment_schedule_id = fields.Many2one('payment.schedule', string='Payment Schedule')
    active = fields.Boolean(string='Active', default=True)
    unit_type_ids = fields.Many2many('unit.type', string="Unit Types")
    is_agent = fields.Boolean(string="Agent")
    is_internal_user = fields.Boolean(string="Internal User")

    @api.onchange('asset_project_id')
    def onchange_asset_project_id(self):
        property_ids = self.env['account.asset.asset'].search(
            [('state', '=', 'draft'), ('parent_id', '=', self.asset_project_id.id)])
        payment_schedule_ids = self.env['payment.schedule'].search(
            [('asset_project_id', '=', self.asset_project_id.id)])
        return {'domain': {'property_id': [('id', 'in', property_ids.ids)],
                           'payment_schedule_id': [('id', 'in', payment_schedule_ids.ids)]}}

    @api.onchange('percentage', 'fixed')
    def onchange_type(self):
        if self.percentage:
            self.fixed = False
            self.amount_value = False
        if self.fixed:
            self.percentage = False
            self.percentage_value = False


class CommissionInvoiceLine(models.Model):
    _inherit = "commission.invoice.line"

    rent_amt = fields.Float(string='Rent Amount')


class CommissionInvoice(models.Model):
    _name = "commission.invoice"
    _inherit = ['commission.invoice', 'mail.thread', 'mail.activity.mixin', 'portal.mixin']
    _rec_name = 'number'
    _description = "Commission Invoice"

    # _inherit= "commission.invoice"

    @api.depends('commission_line.amount')
    def _amount_all(self):
        """
        Compute the total amounts of the SO.
        """
        for rec in self:
            rec.amount_total = 0.0
            for data in rec.commission_line:
                rec.amount_total += data.amount

    amount_total = fields.Float(
        string='Total',
        store=True,
        readonly=True,
        compute='_amount_all',
        tracking=True)
    partner_id = fields.Many2one(
        comodel_name='res.partner', string='Customer Name', tracking=True)
    # domain=[('is_tenant', '=', True)])
    commission_for_rent = fields.Boolean(string='Commission For Rent', tracking=True)
    commission_for_sale = fields.Boolean(string='Commission For Sale', tracking=True)

    customer_id = fields.Many2one('res.partner', string='Customer Name', tracking=True)
    mobile = fields.Char(string='Mobile', tracking=True)
    related_booking_id = fields.Many2one('sale.order', string='Related Booking', tracking=True)
    # related_spa_id = fields.Many2one('sale.order', string='Related SPA', compute='compute_booking_spa', tracking=True)
    all_related_commissions = fields.One2many(related='related_booking_id.commission_ids', string='All Commissions',
                                              tracking=True)
    all_related_commissions_of_agent = fields.Many2many('commission.invoice', 'commission_commission_rel2', 'com1',
                                                        'com2', string='All Commissions for this Agent',
                                                        compute='compute_agent_commission', tracking=True)
    # asset_project_id = fields.Many2one('account.asset.asset', 'Project', domain="[('project', '=', True)]")
    # property_id = fields.Many2one('account.asset.asset',string='Property')
    # booking_status = fields.Selection(related='related_booking_id.is_buy_state', string='Booking Status', tracking=True)
    booking_date = fields.Date('Booking Date', tracking=True)
    # booking_status = fields.Char('Booking Status',related='related_booking_id.booking_state')
    # spa_status = fields.Selection(related='related_spa_id.state', string='SPA Status', tracking=True)
    total_price = fields.Float('Total Price', tracking=True)
    total_received_amount = fields.Float('Total received Amount', tracking=True, compute='compute_received_amount')
    # state = fields.Selection(
    #     [('draft', 'Open'),
    #      ('under_manager_review', 'Under Manager Review'),
    #      ('under_legal_review', 'Under Legal Review'),
    #      ('under_verification', 'Under Accounts Verification'),
    #      ('under_fc_authorization', 'Under Fin Manager Review'),
    #      ('under_cfo_authorization', 'Under FC Authorization'),
    #      ('under_approval', 'Under Approval'),
    #      ('approved', 'Approved'),
    #      ('rejected', 'Rejected'),
    #      ('cancel', 'Cancel'),
    #      ('invoice', 'Invoiced'),
    #      ('paid', 'Paid')
    #      ], 'State', readonly=True,
    #     default='draft', tracking=True)

    number = fields.Char(
        string='Commission ID',
        default='/', tracking=True)
    patner_id = fields.Many2one(
        comodel_name='tenant.partner',
        string='Partner',
        help='Name of tenant where from commission is taken', tracking=True)
    date = fields.Date(
        String='Commission Date', tracking=True,
        default=lambda *a: time.strftime(DEFAULT_SERVER_DATE_FORMAT))
    tenancy = fields.Many2one(
        comodel_name='account.analytic.account',
        string='Tenancy', tracking=True)
    description = fields.Text(
        string='Terms & Conditions', tracking=True)
    property_id = fields.Many2one(
        comodel_name='account.asset.asset',
        string='Property', tracking=True)
    commission_type = fields.Selection(
        selection=[('fixed', 'Fixed percentage'),
                   ('fixedcost', 'By Fixed Cost')],
        string='Type',
        default='fixed', tracking=True)
    commission_line = fields.One2many(
        comodel_name='commission.invoice.line',
        inverse_name='commission_id',
        string='Commission', tracking=True)
    currency_id = fields.Many2one(
        comodel_name="res.currency",
        string="Currency", tracking=True)
    agent = fields.Many2one(
        comodel_name='res.partner',
        domain=[('agent', '=', True)], tracking=True)
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company', tracking=True,
        default=lambda self: self.env['res.company']._company_default_get(
            'commission.invoice'))
    invc_id = fields.Many2one(
        comodel_name='account.move',
        string='Invoice', tracking=True)
    inv = fields.Boolean(
        string='INV', tracking=True)
    color = fields.Integer('Color Index', tracking=True)
    previous_state = fields.Char(string='Previous State')
    asset_project_id = fields.Many2one('account.asset.asset', 'Project', domain="[('project', '=', True)]")
    total_commission_amount = fields.Float(string='Total Commission Amount', compute='compute_matured_pdcs',
                                           store=True)
    # total_commission_paid = fields.Float(string='Total Commission Paid', compute='compute_matured_pdcs', store=True)
    # balance_commission = fields.Float(string='Balance Commission', compute='compute_matured_pdcs', store=True)
    commission_type_id = fields.Many2one('commission.type', string='Commission Type',
                                         compute='compute_matured_pdcs', store=True)
    team_up = fields.Boolean(string='Team Up')
    agent_ref = fields.Boolean(string='Agent Ref.')
    commission_share_perc = fields.Float(string='Commission Share (%)')
    commission_share_amount = fields.Float(string='Commission Share Amount')
    ten_perc_of_price = fields.Float(compute='get_ten_perc_of_price', store=True,
                                     string='Commission Eligibility 10% Price')
    fifteen_perc_of_price = fields.Float(compute='get_ten_perc_of_price', store=True,
                                         string='Commission Eligibility 15% Price')
    oqood_charge = fields.Float(compute='get_oqood_charge', store=True, string='Oqood Charged')
    admin_fee_charge = fields.Float(compute='get_admin_fee_charge', store=True, string='Oqood Charged')
    eligible_amount = fields.Float(compute='get_eligible_amount', store=True, string='10%+Oqood+Admin')
    fifteen_perc_amount = fields.Float(compute='get_eligible_amount', store=True, string='15%+Oqood+Admin')
    # realized_collections = fields.Float('Realized Collections Perc', store=True, compute='compute_realized_collections')
    realized_collection_perc = fields.Float('Realized Collections Perc', store=True,
                                            compute='compute_realized_collections')
    diff_four_five = fields.Float('Difference', store=True, compute='get_diff_four_five')
    ten_in_perc = fields.Float('Ten in %', store=True, compute='get_eligiblty_in_perc')
    fifteen_in_perc = fields.Float('Fifteen in %', store=True, compute='get_eligiblty_in_perc')
    diffrence2 = fields.Float('Difference2', store=True, compute='get_diff_four_five')
    matured_pdcs = fields.Float(string='Amount Received (Realized Collections)', compute='compute_matured_pdcs',
                                store=True)
    collection_perc = fields.Float(compute='get_perc_total_received_amount', string='Total Collection %', store=True)
    unsecured_collections = fields.Float(string='Unsecured Collections', compute='compute_matured_pdcs', store=True)
    amount_receive1 = fields.Float(string='Amount Received1', compute='get_diff_four_five')
    amount_receive2 = fields.Float(string='Amount Received2', compute='get_diff_four_five')
    unsecured_collections_perc = fields.Float(string='Unsecured Collections %', compute='compute_unsecured_collections',
                                              store=True)
    commission_ten_perc = fields.Float(string='Commission Eligibility 10% Price',
                                       compute='get_perc_total_received_amount', store=True)
    unit_commission_history = fields.Many2many('commission.invoice', 'commission_unit_rel2', 'com1', 'com2',
                                               string='Unit Commission History',
                                               compute='compute_unit_commission')
    total_collection_ids = fields.Many2many('account.payment', 'commission_receipt_rel1', 'com1', 'receipt1',
                                            string='Total Collections',
                                            compute='compute_received_amount')
    # spa_status = fields.Selection(related='related_spa_id.state', string='SPA Status', tracking=True)
    amount_received_ids = fields.Many2many('account.payment', 'commission_receipt_rel2', 'com1', 'receipt2',
                                           string='Amount Received',
                                           compute='compute_received_amount')
    agent_chk = fields.Boolean(string='Agent Ref.', compute='get_agent_chk', store=True)
    com1_chk = fields.Boolean(string='Com1 chk.', compute='compute_matured_pdcs', store=True)
    com2_chk = fields.Boolean(string='Com2 chk.', compute='compute_matured_pdcs', store=True)
    com3_chk = fields.Boolean(string='Com3 chk.', compute='compute_matured_pdcs', store=True)

    # agent_ref = fields.Boolean(string='Agent Ref.', related='related_booking_id.agent_ref')
    agent_discount_perc = fields.Float(related='related_booking_id.agent_discount_perc', string='Agent Discount(%)',
                                       tracking=True)
    net_commission_perc = fields.Float(related='related_booking_id.net_commission_perc', string='Net Commission(%)',
                                       tracking=True)

    subject = fields.Char('Subject')
    # related_invoices_ids = fields.Many2many('account.invoice', 'commission_related_inv_rel1', 'com1', 'rinv1', string='Related Invoices',
    #                                                    compute='compute_related_inv_pay')
    # related_payments_ids = fields.Many2many('account.payment', 'commission_payments_rel1', 'com1', 'rpay2', string='Related Payments',
    #                                                    compute='compute_related_inv_pay')
    account_payment_criteria_lines = fields.One2many('account.payment.criteria', 'commission_invoice_id',
                                                     'Payment Criteria for Accounts')
    invoiced_amount = fields.Float(string='Commission Invoiced', compute='compute_related_inv_pay', store=True)
    state = fields.Selection(
        [('draft', 'Open'),
         ('under_legal_review', 'Under Legal Review'),
         ('under_manager_review', 'Under Manager Review'),
         ('under_sales_hod_review', 'Under Sales HOD Review'),
         ('under_verification', 'Under Accounts Verification'),
         ('under_fc_authorization', 'Under Fin Manager Review'),
         ('under_cfo_authorization', 'Under FC Authorization'),
         ('under_approval', 'Under Approval'),
         ('approved', 'Approved'),
         ('rejected', 'Rejected'),
         ('cancel', 'Cancel'),
         ('invoice', 'Invoiced'),
         ('paid', 'Paid')
         ], 'State', readonly=True,
        default='draft', tracking=True)

    comm_payment_type = fields.Selection([('full', 'Full Commission'),
                                          ('partial', 'Partial Commission'),
                                          ('balance', 'Balance Commission')], 'Comm Payment Type',
                                         tracking=True)
    realized_collections = fields.Float(string='Realized Collections (%)', compute='compute_realized_collections')
    related_spa_id = fields.Many2one('sale.order', string='Related SPA/Booking', store=True, compute='compute_booking_spa',
                                     tracking=True)

    related_invoices_ids = fields.Many2many('account.move', 'commission_related_inv_rel1', 'com1', 'rinv1',
                                            string='Related Invoices',
                                            compute='compute_related_inv_pay')
    related_payments_ids = fields.Many2many('account.payment', 'commission_payments_rel1', 'com1', 'rpay2',
                                            string='Related Payments',
                                            compute='compute_related_inv_pay')
    total_commission_paid = fields.Float(string='Total Commission Paid', compute='compute_related_inv_pay', store=True)
    balance_commission = fields.Float(string='Balance Commission', compute='compute_balance_comm', store=True)

    @api.depends('invc_id', 'invc_id.amount_total', 'invc_id.amount_residual')
    def compute_related_inv_pay(self):
        for rec in self:
            if rec.invc_id:
                payments = rec.env['account.payment'].search([('reconciled_invoice_ids', 'in', rec.invc_id.ids)])
                rec.invoiced_amount = rec.invc_id.amount_total
                rec.total_commission_paid = rec.invc_id.amount_total - rec.invc_id.amount_residual
                rec.related_invoices_ids = [(6, 0, rec.invc_id.ids)]
                rec.related_payments_ids = [(6, 0, payments.ids)]
            else:
                rec.invoiced_amount = 0
                rec.total_commission_paid = 0
                rec.related_invoices_ids = []
                rec.related_payments_ids = []

    @api.depends('total_commission_amount', 'total_commission_paid')
    def compute_balance_comm(self):
        for rec in self:
            rec.balance_commission = rec.total_commission_amount - rec.total_commission_paid

    def create_invoice(self):
        """
        This method is used to create supplier invoice.
        ------------------------------------------------------------
        @param self: The object pointer
        """
        account_jrnl_obj = self.env['account.journal'].search(
            [('type', '=', 'purchase')], limit=1)
        for data in self:
            inv_line_values = {
                'name': 'Commission For ' + data.number or "",
                'property_id': data.property_id.id,
                'asset_project_id': data.asset_project_id.id,
                'analytic_account_id': data.tenancy.id or False,
                # 'origin': 'Commission',
                'quantity': 1,
                'account_id': data.property_id.expense_account_id.id or False,
                'price_unit': data.amount_total or 0.00,
            }
            inv_values = {
                # 'origin': 'Commission For ' + data.number or "",
                'move_type': 'in_invoice',
                'property_id': data.property_id.id,
                'asset_project_id': data.asset_project_id.id,
                'partner_id': data.agent.id or False,
                'invoice_line_ids': [(0, 0, inv_line_values)],
                'invoice_date': datetime.now().strftime(
                    DEFAULT_SERVER_DATE_FORMAT) or False,
                # 'account_id': data.agent.property_account_payable_id.id or False,
                'journal_id': account_jrnl_obj and account_jrnl_obj.id or False,
            }
            acc_id = self.env['account.move'].create(inv_values)
            data.write({'inv': True, 'invc_id': acc_id.id, 'state': 'invoice'})
            # wiz_form_id = self.env['ir.model.data'].get_object_reference(
            #     'account', 'invoice_supplier_form')[1]
        return {
            # 'view_type': 'form',
            # 'view_id': wiz_form_id,
            'view_mode': 'form',
            'res_model': 'account.move',
            'res_id': self.invc_id.id,
            'type': 'ir.actions.act_window',
            'target': 'current',
            'context': self._context,
        }

    def get_related_attachments(self):
        for rec in self:
            # attachments =  rec.env['ir.attachment'].search([('res_model','=','commission.invoice'),('res_id','=',rec.id)])

            comm_ids = rec.env['commission.invoice'].search([('related_booking_id', '=', rec.related_booking_id.id)])
            comm_att = rec.env['ir.attachment'].search(
                [('res_model', '=', 'commission.invoice'), ('res_id', 'in', comm_ids.ids)])

            spa = []
            spa_obj = self.env['sale.order'].search([('id', '=', rec.related_booking_id.id)])
            if spa_obj:
                spa = spa_obj.ids
            so_att = rec.env['ir.attachment'].search([('res_model', '=', 'sale.order'), ('res_id', 'in', spa)])
            tree_id = self.env.ref('commission_extension.view_attachment_tree_on_model').id
            # print(attachments.ids)
            all_attach =  so_att.ids + comm_att.ids

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

    @api.model
    def old_inv_pay(self):
        comm = self.env['commission.invoice'].search([])
        for rec in comm:
            if rec.invc_id:
                payments = rec.env['account.payment'].search([('reconciled_invoice_ids', 'in', rec.invc_id.ids)])
                rec.invoiced_amount = rec.invc_id.amount_total
                rec.total_commission_paid = rec.invc_id.amount_residual
                rec.related_invoices_ids = [(6, 0, rec.invc_id.ids)]
                rec.related_payments_ids = [(6, 0, payments.ids)]
            rec.balance_commission = rec.total_commission_amount - rec.total_commission_paid

    @api.depends('related_booking_id', 'related_spa_id', 'related_spa_id.matured_pdcs',
                 'related_spa_id.total_unsecured_collections', 'agent')
    def compute_matured_pdcs(self):
        for rec in self:
            matured_pdcs = 0
            unsecured_collections = 0
            if rec.related_spa_id:
                matured_pdcs = rec.related_spa_id.matured_pdcs
                unsecured_collections = rec.related_spa_id.total_unsecured_collections
            rec.matured_pdcs = matured_pdcs
            rec.unsecured_collections = unsecured_collections

            com1_chk = 0
            com2_chk = 0
            com3_chk = 0
            agent_chk = 0
            commission_type_id = False
            total_commission_amount = 0
            if rec.related_booking_id:
                if rec.related_booking_id.team_up_agents:
                    for l in rec.related_booking_id.team_up_agents:
                        if l.id == rec.agent.id:
                            com1_chk = True
                            commission_type_id = rec.related_booking_id.agent_commission_type_id.id
                            total_commission_amount = rec.related_booking_id.net_commission_sp
                if rec.related_booking_id.agent_id == rec.agent:
                    agent_chk = True
                    commission_type_id = rec.related_booking_id.agent_commission_type_id.id
                    total_commission_amount = rec.related_booking_id.net_commission_sp
                if rec.related_booking_id.commission and rec.related_booking_id.agent == rec.agent:
                    com1_chk = True
                    commission_type_id = rec.related_booking_id.commission_type_id.id
                    total_commission_amount = rec.related_booking_id.total_commission
                if rec.related_booking_id.commission2 and rec.related_booking_id.agent2 == rec.agent:
                    com2_chk = True
                    commission_type_id = rec.related_booking_id.commission_type_id2.id
                    total_commission_amount = rec.related_booking_id.total_commission2
                if rec.related_booking_id.commission3 and rec.related_booking_id.agent3 == rec.agent:
                    com3_chk = True
                    commission_type_id = rec.related_booking_id.commission_type_id3.id
                    total_commission_amount = rec.related_booking_id.total_commission3
            rec.com1_chk = com1_chk
            rec.com2_chk = com2_chk
            rec.com3_chk = com3_chk
            rec.agent_chk = agent_chk
            rec.commission_type_id = commission_type_id
            rec.total_commission_amount = total_commission_amount
            # if rec.all_related_commissions:
            #     total_commission_paid = 0.0
            #     for line in rec.all_related_commissions:
            #         if (line.related_booking_id == rec.related_booking_id or line.related_spa_id == rec.related_spa_id) and line.agent == rec.agent and line.state in ['invoice']:
            #             total_commission_paid += line.amount_total
            #     rec.total_commission_paid = total_commission_paid
            # rec.balance_commission = rec.total_commission_amount - rec.total_commission_paid

    # @api.model
    # def create(self, vals):
    #     commission = False
    #     if vals.get('related_booking_id') or vals.get('agent'):
    #         commission = self.search(
    #             [('related_booking_id', '=', vals.get('related_booking_id')), ('agent', '=', vals.get('agent'))])
    #     if commission:
    #         if commission.balance_commission == 0:
    #             raise UserError(
    #                 'The commission amount for this agent is already paid. You are not allowed to create the invoice more then the commission amount ')
    #
    #     # if vals.get('name', _('/')) == _('/'):
    #     #     vals['name'] = self.env['ir.sequence'].next_by_code('account.voucher.replacement')
    #     return super(CommissionInvoice, self).create(vals)

    @api.model
    def create(self, vals):
        res = super(CommissionInvoice, self).create(vals)
        property = res.property_id.id
        agent = res.agent.id
        booking = res.related_booking_id.id
        spa = res.related_spa_id.id
        if property and agent and booking:
            reqs = res.env['commission.invoice'].search(
                [('agent', '=', agent), ('related_booking_id', '=', booking), ('property_id', '=', property)])
            if len(reqs) > 1:
                # if vals.get('subject', False):
                res.subject = str(res.agent.name) + str(res.related_spa_id.name) + ' Commission Request ' + str(
                    len(reqs))
        commission = False
        if vals.get('related_booking_id') or vals.get('agent'):
            commission = self.search(
                [('related_booking_id', '=', vals.get('related_booking_id')), ('agent', '=', vals.get('agent'))])
        if commission and res.id not in commission.ids:
            for commi in commission:
                if commi.balance_commission == 0:
                    raise UserError(
                        'The commission amount for this agent is already paid. You are not allowed to create the invoice more then the commission amount ')
        # else:
        #     UserError(_("Form content is missing, this report cannot be printed."))
        return res

    # @api.depends('invc_id','invc_id.amount_total', 'invc_id.amount_residual')
    # def compute_related_inv_pay(self):
    #     for rec in self:
    #         if rec.invc_id:
    #             payments = rec.env['account.payment'].search([('reconciled_invoice_ids', 'in', rec.invc_id.ids)])
    #             rec.invoiced_amount = rec.invc_id.amount_total
    #             rec.related_invoices_ids = [(6,0, rec.invc_id.ids)]
    #             rec.related_payments_ids = [(6,0, payments.ids)]

    @api.model
    def send_commission_update_email(self, state):
        return True
        group = False
        if state == 'under_manager_review':
            group = self.env.ref('sales_team.group_sale_manager')
        if state == 'under_sales_hod_review':
            group = self.env.ref('property_commission.groups_commission_pay_manager')
        if state == 'under_legal_review':
            group = self.env.ref('commission_extension.group_legal_consultant')
        if state == 'under_verification':
            group = self.env.ref('account.group_account_user')
        if state == 'under_fc_authorization':
            group = self.env.ref('commission_extension.group_financial_controller')
        if state == 'under_cfo_authorization':
            group = self.env.ref('account_voucher_collection.group_general_manager')
        if state == 'under_approval':
            group = self.env.ref('account_voucher_collection.group_ceo')
        for rec in group:
            if rec.users:
                email_template = rec.env.ref('commission_extension.commission_update_email')
                email_template.email_from = email_template.mail_server_id.name
                email_template.email_to = self.get_partner_ids(rec.users)
                email_template.send_mail(self.id, force_send=True)

    def action_send_back(self):
        for rec in self:
            if not rec.subject:
                if rec.state == 'under_legal_review':
                    rec.state = 'draft'
                if rec.state == 'under_manager_review':
                    rec.state = 'under_legal_review'
                if rec.state == 'under_sales_hod_review':
                    rec.state = 'under_manager_review'
                if rec.state == 'under_verification':
                    rec.state = 'under_sales_hod_review'
                if rec.state == 'under_fc_authorization':
                    rec.state = 'under_verification'
                # if rec.state == 'under_cfo_authorization':
                #     rec.state = 'under_fc_authorization'
                if rec.state == 'under_approval':
                    rec.state = 'under_fc_authorization'
                if rec.state == 'approved':
                    rec.state = 'under_approval'
            else:
                if rec.state == 'under_verification':
                    rec.state = 'draft'
                if rec.state == 'under_approval':
                    rec.state = 'under_verification'
                if rec.state == 'approved':
                    rec.state = 'under_approval'

    #
    # def action_send_back(self):
    #     for rec in self:
    #         if rec.state == 'under_legal_review':
    #             rec.state = 'draft'
    #         if rec.state == 'under_manager_review':
    #             rec.state = 'under_legal_review'
    #         if rec.state == 'under_sales_hod_review':
    #             rec.state = 'under_manager_review'
    #         if rec.state == 'under_verification':
    #             rec.state = 'under_sales_hod_review'
    #         if rec.state == 'under_fc_authorization':
    #             rec.state = 'under_verification'
    #         if rec.state == 'under_cfo_authorization':
    #             rec.state = 'under_fc_authorization'
    #         if rec.state == 'under_approval':
    #             rec.state = 'under_cfo_authorization'
    #         if rec.state == 'approved':
    #             rec.state = 'under_approval'

    #
    # def action_fc_authorize(self):
    #     self.write({'previous_state': self.state})
    #     self.write({'state':'under_cfo_authorization'})
    #     self.send_commission_update_email('under_cfo_authorization')

    def action_fc_authorize(self):
        self.write({'previous_state': self.state})
        self.write({'state': 'under_approval'})
        self.send_commission_update_email('under_approval')

    def action_cfo_authorize(self):
        self.write({'previous_state': self.state})
        self.write({'state': 'under_approval'})
        self.send_commission_update_email('under_approval')

    def action_verify(self):
        self.write({'previous_state': self.state})
        if not self.subject:
            self.write({'state': 'under_fc_authorization'})
            self.send_commission_update_email('under_fc_authorization')
        else:
            self.write({'state': 'under_approval'})
            self.send_commission_update_email('under_approval')

    def submit_for_verification(self):
        self.write({'previous_state': self.state})
        self.write({'state': 'under_verification'})
        self.send_commission_update_email('under_verification')

    def submit_for_review(self):
        self.write({'state': 'under_manager_review'})
        self.send_commission_update_email('under_manager_review')

    def action_manager_review(self):
        self.write({'previous_state': self.state})
        self.write({'state': 'under_sales_hod_review'})
        self.send_commission_update_email('under_sales_hod_review')

    def action_send_legal_review(self):
        self.write({'previous_state': self.state})
        self.write({'state': 'under_legal_review'})
        self.send_commission_update_email('under_legal_review')

    @api.depends('commission_type_id', 'commission_type_id.is_agent')
    def get_agent_chk(self):
        for rec in self:
            agent_chk = False
            if rec.commission_type_id:
                if rec.commission_type_id and rec.commission_type_id.is_agent and rec.related_booking_id.agent_commission_type_id.is_agent:
                    agent_chk = True
            rec.agent_chk = agent_chk

    @api.model
    def get_old_agent_chk(self):
        coms = self.env['commission.invoice'].search([])
        for rec in coms:
            agent_chk = False
            if rec.commission_type_id and rec.commission_type_id.is_agent and rec.related_booking_id.agent_commission_type_id.is_agent:
                agent_chk = True
            rec.agent_chk = agent_chk

    @api.depends('property_id')
    def compute_unit_commission(self):
        for record in self:
            invoices_obj = record.env['commission.invoice'].search([('property_id', '=', record.property_id.id)])
            record.unit_commission_history = [(6, 0, invoices_obj.ids)]

    @api.depends('related_booking_id')
    def compute_received_amount(self):
        for record in self:
            record.total_collection_ids = []
            record.amount_received_ids = []
            total_received_amount = 0.0
            collections = []
            posted = []
            for rec in record.related_booking_id.receipt_ids:
                if rec.state not in ['draft', 'cancelled', 'rejected', 'refused']:
                    collections.append(rec.id)
                    total_received_amount += rec.amount
                if rec.state == 'posted':
                    posted.append(rec.id)
            if collections:
                record.total_collection_ids = [(6, 0, collections)]
            if posted:
                record.amount_received_ids = [(6, 0, collections)]
            record.total_received_amount = total_received_amount

    @api.model
    def com_old_received_amount(self):
        com = self.env['commission.invoice'].search([])
        for record in com:
            total_received_amount = 0.0
            for rec in record.related_booking_id.receipt_ids:
                if rec.state not in ['draft', 'cancelled', 'rejected', 'refused']:
                    total_received_amount += rec.amount
            record.total_received_amount = total_received_amount

    @api.depends('total_received_amount', 'total_price', 'related_spa_id')
    def get_perc_total_received_amount(self):
        for rec in self:

            rec.collection_perc = 0
            rec.commission_ten_perc = 0
            if rec.total_received_amount and rec.total_price:
                rec.collection_perc = (rec.total_received_amount / rec.total_price) * 100
                ten_perc = rec.total_price * 0.1
                rec.commission_ten_perc = ten_perc

    @api.depends('fifteen_perc_amount', 'eligible_amount', 'matured_pdcs')
    def get_eligiblty_in_perc(self):
        for rec in self:
            ten_in_perc = 9
            fifteen_in_perc = 0
            if rec.fifteen_perc_amount > 0:
                ten_in_perc = (rec.matured_pdcs / rec.eligible_amount) * 100.0
            if rec.eligible_amount > 0:
                fifteen_in_perc = (rec.matured_pdcs / rec.fifteen_perc_amount) * 100.0
            rec.ten_in_perc = ten_in_perc
            rec.fifteen_in_perc = fifteen_in_perc

    @api.depends('matured_pdcs', 'total_price')
    def compute_realized_collections(self):
        for rec in self:
            realized_collections = 0
            realized_collection_perc = 0
            if rec.total_price:
                realized_collections = (rec.matured_pdcs / rec.total_price) * 100.0
                realized_collection_perc = (rec.matured_pdcs / rec.total_price) * 100.0
            rec.realized_collections = realized_collections
            rec.realized_collection_perc = realized_collection_perc

    @api.depends('unsecured_collections', 'total_price')
    def compute_unsecured_collections(self):
        for rec in self:
            unsecured_collections_perc = 0
            if rec.unsecured_collections > 0 and rec.total_price:
                unsecured_collections_perc = (rec.unsecured_collections / rec.total_price) * 100.0
            rec.unsecured_collections_perc = unsecured_collections_perc

    # @api.depends('related_booking_id','related_spa_id','related_spa_id.matured_pdcs','related_spa_id.total_unsecured_collections','agent')
    # def compute_matured_pdcs(self):
    #     for rec in self:
    #         if rec.related_spa_id:
    #             # rec
    #             # print("pppppp")
    #             # print(rec.related_spa_id)
    #             # print(rec.related_booking_id.sale_id)
    #             rec.matured_pdcs = rec.related_spa_id.matured_pdcs
    #             rec.unsecured_collections = rec.related_spa_id.total_unsecured_collections
    #         if rec.related_booking_id:
    #             if rec.related_booking_id.team_up_agents:
    #                 for l in rec.related_booking_id.team_up_agents:
    #                     if l.id == rec.agent.id:
    #                         rec.com1_chk = True
    #                         rec.commission_type_id = rec.related_booking_id.agent_commission_type_id.id
    #                         rec.total_commission_amount = rec.related_booking_id.net_commission_sp
    #             if rec.related_booking_id.agent_id == rec.agent:
    #                 rec.agent_chk = True
    #                 rec.commission_type_id = rec.related_booking_id.agent_commission_type_id.id
    #                 rec.total_commission_amount = rec.related_booking_id.net_commission_sp
    #             if rec.related_booking_id.agent == rec.agent:
    #                 rec.com1_chk = True
    #                 rec.commission_type_id = rec.related_booking_id.commission_type_id.id
    #                 rec.total_commission_amount = rec.related_booking_id.total_commission
    #             if rec.related_booking_id.agent2 == rec.agent:
    #                 rec.com2_chk = True
    #                 rec.commission_type_id = rec.related_booking_id.commission_type_id2.id
    #                 rec.total_commission_amount = rec.related_booking_id.total_commission2
    #             if rec.related_booking_id.agent3 == rec.agent:
    #                 rec.com3_chk = True
    #                 rec.commission_type_id = rec.related_booking_id.commission_type_id3.id
    #                 rec.total_commission_amount = rec.related_booking_id.total_commission3
    #         if rec.all_related_commissions:
    #             total_commission_paid = 0.0
    #             for line in rec.all_related_commissions:
    #                 if (line.related_booking_id == rec.related_booking_id or line.related_spa_id == rec.related_spa_id) and line.agent == rec.agent and line.state in ['invoice']:
    #                     total_commission_paid += line.amount_total
    #             rec.total_commission_paid = total_commission_paid
    #         rec.balance_commission = rec.total_commission_amount - rec.total_commission_paid

    @api.depends('related_booking_id', 'related_booking_id.price')
    def get_ten_perc_of_price(self):
        for rec in self:
            if rec.related_booking_id.price:
                rec.ten_perc_of_price = rec.related_booking_id.price * 0.1
                rec.fifteen_perc_of_price = rec.related_booking_id.price * 0.15
            else:
                rec.ten_perc_of_price = 0.0
                rec.fifteen_perc_of_price = 0.0

    @api.depends('related_booking_id', 'related_booking_id.oqood_fee')
    def get_oqood_charge(self):
        for rec in self:
            if rec.related_booking_id.oqood_fee:
                rec.oqood_charge = rec.related_booking_id.oqood_fee
            else:
                rec.oqood_charge = 0.0

    @api.depends('related_booking_id', 'related_booking_id.admin_fee')
    def get_admin_fee_charge(self):
        for rec in self:
            if rec.related_booking_id.admin_fee:
                rec.admin_fee_charge = rec.related_booking_id.admin_fee
            else:
                rec.admin_fee_charge = 0.0

    @api.depends('ten_perc_of_price', 'oqood_charge', 'admin_fee_charge', 'fifteen_perc_of_price')
    def get_eligible_amount(self):
        for rec in self:
            rec.eligible_amount = rec.ten_perc_of_price + rec.oqood_charge + rec.admin_fee_charge
            rec.fifteen_perc_amount = rec.fifteen_perc_of_price + rec.oqood_charge + rec.admin_fee_charge

    @api.depends('eligible_amount', 'matured_pdcs', 'fifteen_perc_amount')
    def get_diff_four_five(self):
        for rec in self:
            rec.diff_four_five = rec.matured_pdcs - rec.eligible_amount
            rec.diffrence2 = rec.matured_pdcs - rec.fifteen_perc_amount
            rec.amount_receive1 = rec.matured_pdcs
            rec.amount_receive2 = rec.matured_pdcs

    @api.onchange('asset_project_id')
    def onchange_asset_project_id(self):
        property_ids = self.env['account.asset.asset'].search(
            [('parent_id', '=', self.asset_project_id.id)])
        return {'domain': {'property_id': [('id', 'in', property_ids.ids)]}}

    @api.model
    def old_project_from_property(self):
        ci = self.env['commission.invoice'].search([])
        for rec in ci:
            if rec.property_id:
                rec.asset_project_id = rec.property_id.parent_id.id

    @api.onchange('property_id')
    def onchange_property_id(self):
        if self.property_id:
            booking_ids = self.env['sale.order'].search([('property_id', '=', self.property_id.id)])
            if booking_ids:
                self.related_booking_id = booking_ids[0].id
            return {'domain': {'related_booking_id': [('id', 'in', booking_ids.ids)]}}

    @api.onchange('related_booking_id')
    def onchange_booking_id(self):
        if self.related_booking_id:
            self.booking_date = self.related_booking_id.booking_date or False
            self.total_price = self.related_booking_id.price
            self.total_received_amount = self.related_booking_id.total_receipts

    @api.onchange('partner_id')
    def onchange_partner_id(self):
        if self.partner_id:
            self.mobile = self.partner_id.mobile

    @api.depends('related_booking_id')
    def compute_booking_spa(self):
        for data in self:
            data.related_spa_id = False
            if data.related_booking_id:
                spa_obj = self.env['sale.order'].search([('id', '=', data.related_booking_id.id)])
                if spa_obj:
                    data.related_spa_id = spa_obj[0].id

    def get_partner_ids(self, user_ids):
        if user_ids:
            anb = str([user.partner_id.email for user in user_ids]).replace('[', '').replace(']', '')
            return anb.replace("'", '')

    @api.model
    def send_commission_update_email(self, state):
        return True
        group = False
        if state == 'under_manager_review':
            group = self.env.ref('sales_team.group_sale_manager')
        if state == 'under_legal_review':
            group = self.env.ref('commission_extension.group_legal_consultant')
        if state == 'under_verification':
            group = self.env.ref('account.group_account_user')
        if state == 'under_fc_authorization':
            group = self.env.ref('commission_extension.group_financial_controller')
        if state == 'under_cfo_authorization':
            group = self.env.ref('account_voucher_collection.group_general_manager')
        if state == 'under_approval':
            group = self.env.ref('account_voucher_collection.group_ceo')
        for rec in group:
            if rec.users:
                email_template = rec.env.ref('commission_extension.commission_update_email')
                email_template.email_from = email_template.mail_server_id.name
                email_template.email_to = self.get_partner_ids(rec.users)
                email_template.send_mail(self.id, force_send=True)

    @api.onchange('commission_for_rent')
    def onchange_commission_rent(self):
        if self.commission_for_rent:
            self.commission_for_sale = False

    @api.onchange('commission_for_sale')
    def onchange_commission_sale(self):
        if self.commission_for_sale:
            self.commission_for_rent = False

    def action_draft(self):
        self.write({'state': 'draft'})

    def action_reject(self):
        self.write({'previous_state': self.state})
        self.write({'state': 'rejected'})

    def action_approve(self):
        self.write({'previous_state': self.state})
        # self.write({'state': 'approved'})
        account_jrnl_obj = self.env['account.journal'].search(
            [('type', '=', 'purchase')], limit=1)
        for data in self:
            inv_line_values = {
                'name': 'Commission For ' + data.number or "",
                'property_id': data.property_id.id,
                'asset_project_id': data.asset_project_id.id,
                'analytic_account_id': data.tenancy.id or False,
                'quantity': 1,
                'account_id': data.property_id.expense_account_id.id or False,
                'price_unit': data.amount_total or 0.00,
            }
            inv_values = {
                'move_type': 'in_invoice',
                'property_id': data.property_id.id,
                'asset_project_id': data.asset_project_id.id,
                'partner_id': data.agent.id or False,
                'invoice_line_ids': [(0, 0, inv_line_values)],
                'invoice_date': datetime.now().strftime(
                    DEFAULT_SERVER_DATE_FORMAT) or False,
                'journal_id': account_jrnl_obj and account_jrnl_obj.id or False,
            }
            acc_id = self.env['account.move'].create(inv_values)
            data.write({'inv': True, 'invc_id': acc_id.id, 'state': 'invoice'})
        return {
            # 'view_type': 'form',
            # 'view_id': wiz_form_id,
            'view_mode': 'form',
            'res_model': 'account.move',
            'res_id': self.invc_id.id,
            'type': 'ir.actions.act_window',
            'target': 'current',
            'context': self._context,
        }
    # def action_approve(self):
    #     self.write({'previous_state': self.state})
    #     self.write({'state': 'approved'})

        # ('under_manager_review', 'Under Manager Review'),
        #  ('under_legal_review', 'Under Legal Review'),
        #  ('under_verification', 'Under Accounts Verification'),
        #  ('under_fc_authorization', 'Under FC Authorization'),
        #  ('under_cfo_authorization', 'Under CFO Authorization'),
        #  ('under_approval', 'Under Approval'),
        #  ('approved', 'Approved'),

    # def action_send_back(self):
    #     for rec in self:
    #         if rec.state == 'under_legal_review':
    #             rec.state = 'under_manager_review'
    #         if rec.state == 'under_verification':
    #             rec.state = 'under_legal_review'
    #         if rec.state == 'under_fc_authorization':
    #             rec.state = 'under_verification'
    #         if rec.state == 'under_cfo_authorization':
    #             rec.state = 'under_fc_authorization'
    #         if rec.state == 'under_approval':
    #             rec.state = 'under_cfo_authorization'
    #         if rec.state == 'approved':
    #             rec.state = 'under_approval'

    @api.onchange('type')
    def onchange_type(self):
        if self.type:
            self.letter_body = self.type.text

    def action_cancel(self):
        self.write({'state': 'cancel'})

    @api.depends('agent')
    def compute_agent_commission(self):
        for record in self:
            invoices_obj = record.env['commission.invoice'].search([('agent', '=', record.agent.id)])
            record.all_related_commissions_of_agent = [(6, 0, invoices_obj.ids)]

    # @api.depends('related_booking_id')
    # def compute_received_amount(self):
    #     for record in self:
    #         total_received_amount = 0.0
    #         for rec in record.related_booking_id.receipt_ids:
    #             total_received_amount += rec.amount
    #         record.total_received_amount = total_received_amount

    @api.onchange('tenancy')
    def onchange_tenancy_id(self):
        if self.tenancy:
            self.patner_id = self.tenancy.tenant_id.id
            self.property_id = self.tenancy.property_id.id


class SaleOrder(models.Model):
    _inherit = "sale.order"

    # salesperson_id = fields.Many2one('res.users', 'Salesperson', tracking=True)

    commission_ids = fields.One2many('commission.invoice', 'related_booking_id', string='All Commissions')
    commission_type_id = fields.Many2one('commission.type', string='Type')
    agent = fields.Many2one(
        comodel_name='res.partner', string='Agent1')
    commission = fields.Boolean(
        'Commission')
    commission_create = fields.Boolean(
        'Create')
    # total_commission2 = fields.Float(
    #     string="Total Commission")

    total_commission = fields.Float(
        string="Total Commission", compute='calculate_commission1')

    commission_type_id2 = fields.Many2one('commission.type', string='Type')
    agent2 = fields.Many2one(
        comodel_name='res.partner', string='Agent2')
    commission2 = fields.Boolean(
        '2nd Commission')
    commission_create2 = fields.Boolean(
        'Create')
    # total_commission2 = fields.Float(
    #     string="Total Commission")

    total_commission2 = fields.Float(
        string="Total Commission", compute='calculate_commission2')

    commission_type_id3 = fields.Many2one('commission.type', string='Type')
    agent3 = fields.Many2one(
        comodel_name='res.partner', string='Agent3')
    commission3 = fields.Boolean(
        '3rd Commission')
    commission_create3 = fields.Boolean('Create')
    # total_commission3 = fields.Float(
    #     string="Total Commission")

    total_commission3 = fields.Float(string="Total Commission")
    # total_commission3 = fields.Float(string="Total Commission", compute='calculate_commission3')
    agent_ref = fields.Boolean(string='Agent Ref.', tracking=True)
    agent_id = fields.Many2one('res.partner', string='Agent Name', tracking=True)

    @api.onchange('agent_ref')
    def onchange_agent_ref(self):
        if not self.agent_ref:
            self.agent_id = False

    agent_commission_remarks = fields.Text('Agent Commission Remarks')
    team_up = fields.Boolean('Team Up')
    commission_share_perc = fields.Float('Commission Share (%)')
    commission_share_amount = fields.Float(compute='get_commission_share_amount', store=True,
                                           string='Commission Share Amount')
    team_up_agents = fields.Many2many('res.users', string='Team Up Agents')

    @api.depends('total_commission', 'commission_share_perc')
    def get_commission_share_amount(self):
        for rec in self:
            if rec.commission_share_perc:
                rec.commission_share_amount = (rec.commission_share_perc / 100) * rec.total_commission

    def view_commissions(self):
        for rec in self:
            return {
                'name': _('Commissions'),
                'view_mode': 'tree,form',
                # 'view_id': tree_id,
                'res_model': 'commission.invoice',
                'type': 'ir.actions.act_window',
                'domain': [('id', 'in', rec.commission_ids.ids)],
                'context': {
                    'create': False,
                    'edit': False
                },
            }

    # def action_create_commission(self):
    #     ctx = dict(
    #         default_booking_id=self.id
    #     )
    #     # default_name = "Are You Sure, You Have Reviewed All The Data , Payment Schedule, Price and other things",
    #
    #     return {
    #         'name': _('Create Commission'),
    #         'view_mode': 'form',
    #         'res_model': 'create.commission.wiz',
    #         'view_id': self.env.ref('commission_extension.view_create_commission_wizard').id,
    #         'type': 'ir.actions.act_window',
    #         'context': ctx,
    #         'target': 'new'
    #     }

    def action_create_commission(self):
        ctx = dict(
            default_booking_id=self.id
        )
        return {
            'name': _('Create Commission'),
            'view_mode': 'form',
            'res_model': 'create.commission.wiz',
            'view_id': self.env.ref('commission_extension.view_create_commission_wizard').id,
            'type': 'ir.actions.act_window',
            'context': ctx,
            'target': 'new'
        }

    def create_commission(self):
        """
        This button method is used to Change Tenancy state to Open.
        @param self: The object pointer
        """
        for data in self:
            if data.commission:
                if data.total_commission == 0.00:
                    raise Warning(
                        _('Total Commission must be grater than zero.'))
                line_vlas = {
                    'name': 'Commission',
                    'commission_type_id': data.commission_type_id.id,
                    'rent_amt': data.price,
                    'amount': data.total_commission,
                }
                vals = {
                    'commission_for_sale': True,
                    'partner_id': data.partner_id.id,
                    'related_booking_id': data.id,
                    'property_id': data.property_id.id,
                    'agent': data.agent.id,
                    'booking_date': data.booking_date,
                    'total_price': data.price,
                    'description': "1.	SPA is signed & in all sense correct.\n"
                                   "2.	Advance has been received (10% with PDC, 20% without PDCs).\n"
                                   "3.	Oqood has been received.\n"
                                   "4.	Admin has been received.\n"
                                   "5.	PDCs have been received (where applicable).\n",
                    'commission_line': [(0, 0, line_vlas)],
                }
                # if self._context.get('is_tenancy_rent'):
                #     vals.update({
                #         'property_id': data.prop_ids.id
                #     })
                self.env['commission.invoice'].create(vals)
                data.write({'commission_create': True})

            if data.commission2:
                if data.total_commission2 == 0.00:
                    raise Warning(
                        _('Total Commission2 must be grater than zero.'))
                line_vlas2 = {
                    'name': 'Commission2',
                    'commission_type_id': data.commission_type_id2.id,
                    'rent_amt': data.price,
                    'amount': data.total_commission2,
                }
                vals2 = {
                    'commission_for_sale': True,
                    'partner_id': data.partner_id.id,
                    'related_booking_id': data.id,
                    'property_id': data.property_id.id,
                    'agent': data.agent2.id,
                    'booking_date': data.booking_date,
                    'total_price': data.price,
                    'description': "1.	SPA is signed & in all sense correct.\n"
                                   "2.	Advance has been received (10% with PDC, 20% without PDCs).\n"
                                   "3.	Oqood has been received.\n"
                                   "4.	Admin has been received.\n"
                                   "5.	PDCs have been received (where applicable).\n",
                    'commission_line': [(0, 0, line_vlas2)],
                }
                self.env['commission.invoice'].create(vals2)
                data.write({'commission_create': True})

            if data.commission3:
                if data.total_commission3 == 0.00:
                    raise Warning(
                        _('Total Commission must be grater than zero.'))
                line_vlas3 = {
                    'name': 'Commission3',
                    'commission_type_id': data.commission_type_id3.id,
                    'rent_amt': data.price,
                    'amount': data.total_commission3,
                }
                vals3 = {
                    'commission_for_sale': True,
                    'partner_id': data.partner_id.id,
                    'related_booking_id': data.id,
                    'property_id': data.property_id.id,
                    'agent': data.agent3.id,
                    'booking_date': data.booking_date,
                    'total_price': data.price,
                    'description': "1.	SPA is signed & in all sense correct.\n"
                                   "2.	Advance has been received (10% with PDC, 20% without PDCs).\n"
                                   "3.	Oqood has been received.\n"
                                   "4.	Admin has been received.\n"
                                   "5.	PDCs have been received (where applicable).\n",
                    'commission_line': [(0, 0, line_vlas3)],
                }
                # if self._context.get('is_tenancy_rent'):
                #     vals.update({
                #         'property_id': data.prop_ids.id
                #     })
                self.env['commission.invoice'].create(vals3)
                data.write({'commission_create': True})

    @api.depends('commission_type_id', 'price')
    def calculate_commission1(self):
        for data in self:
            total_commission = 0
            if data.commission is True:
                if data.commission_type_id.percentage:
                    total_commission = data.price * (
                            data.commission_type_id.percentage_value / 100.0)
                if data.commission_type_id.fixed:
                    total_commission = data.commission_type_id.amount_value
            data.total_commission = total_commission

    @api.depends('commission_type_id2', 'price')
    def calculate_commission2(self):
        for data in self:
            total_commission2 = 0
            if data.commission2 is True:
                if data.commission_type_id2.percentage:
                    total_commission2 = data.price * (
                            data.commission_type_id2.percentage_value / 100.0)
                if data.commission_type_id2.fixed:
                    total_commission2 = data.commission_type_id2.amount_value
            data.total_commission2 = total_commission2

    @api.onchange('commission_type_id3', 'price')
    def calculate_commission3(self):
        for data in self:
            total_commission3 = 0
            if data.commission3 is True:
                if data.commission_type_id3.percentage:
                    total_commission3 = data.price * (
                            data.commission_type_id3.percentage_value / 100.0)
                if data.commission_type_id3.fixed:
                    total_commission3 = data.commission_type_id3.amount_value
            data.total_commission3 = total_commission3

    @api.onchange('commission', 'commission2', 'commission3')
    def onchange_commissions(self):
        if self.commission is False:
            self.agent = False
            self.commission_type_id = False
            self.total_commission = 0.00
        if self.commission2 is False:
            self.agent2 = False
            self.commission_type_id2 = False
            self.total_commission2 = 0.00
        if self.commission3 is False:
            self.agent3 = False
            self.commission_type_id3 = False
            self.total_commission3 = 0.00

    # @api.onchange('user_id')
    # def onchange_salesperson(self):
    #     if self.user_id:
    #         self.agent = self.user_id.partner_id.id
    #         self.agent2 = self.user_id.partner_id.id
    #         self.agent3 = self.user_id.partner_id.id

# class SaleOrder(models.Model):
#     _inherit = "sale.order"
#
#     commission_ids = fields.One2many('commission.invoice', 'related_spa_id',
#                                      related='booking_id.commission_ids', string='All Commissions',
#                                      readonly=True)
#
#     @api.model
#     def get_old_partners_spa(self):
#         sos = self.env['sale.order'].search([])
#         for rec in sos:
#             if rec.payment_schedule_ids:
#                 for line in rec.payment_schedule_ids:
#                     line.partner_id = rec.partner_id.id
