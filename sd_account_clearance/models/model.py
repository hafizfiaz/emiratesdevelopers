from odoo import models, fields, api


class AccountClearance(models.Model):
    _name = 'account.clearance'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Account Clearance'

    subject = fields.Char('Subject')
    sequence = fields.Char('Sequence', readonly=True)
    clearance_type = fields.Many2one('clearance.type', 'Clearance Type')
    # booking_id = fields.Many2one('crm.booking', 'Booking', related='spa.booking_id')
    spa = fields.Many2one('sale.order', 'Related SPA/Booking')
    project = fields.Many2one('account.asset.asset', 'Project', domain="[('project', '=', True)]")
    property = fields.Many2one('account.asset.asset', 'Property')
    spa_status = fields.Selection([
        ('draft', 'Draft'),
        ('under_legal_review_print', 'Under legal Review for Print'),
        ('under_acc_verification_print', 'Under Account Verification for Print'),
        ('under_confirmation_print', 'Under Confirmation for Print'),
        ('unconfirmed_print', 'Unconfirmed SPA OK for Print'),
        ('under_legal_review', 'Under Legal Review'),
        ('under_acc_verification', 'Under Accounts Verify'),
        ('under_approval', 'Under Approval'),
        ('sale', 'Approved SPA'),
        ('refund_cancellation', 'Refund Cancellation'),
        ('reject', 'Rejected'),
        ('paid', 'Approved SPA-Paid'),
        ('done', 'Locked'),
        ('cancel', 'Cancelled')
    ], string='SPA Status', related='spa.state', readonly=True)

    # booking_status = fields.Selection([
    #     ('draft', 'Draft'),
    #     ('under_discount_approval', 'Under Discount Approval'),
    #     ('tentative_booking', 'Tentative Booking'),
    #     ('review', 'Under Review'),
    #     ('confirm_spa', 'Confirmed for SPA'),
    #     ('approved', 'Approved'),
    #     ('rejected', 'Rejected'),
    #     ('cancel', 'Cancel')
    # ], string='Booking Status', related='booking_id.is_buy_state', readonly=True)
    total_spa = fields.Float('Total SPA Value', compute='_spavalue', store=True)
    total_collection = fields.Float('Total Collection', compute='totalcoll', store=True)
    total_collection_perc = fields.Float(string="Total Collection(%)", compute='totalCollection', store=True)
    realized_collection = fields.Float('Total Amount (Realized Collections)', compute='_spapdc', store=True)
    realized_collection_perc = fields.Float(string="Total Amount(%)", compute='realizedCollection', store=True)
    pending_collections = fields.Float('Pending Collections', compute='pending', store=True)
    pending_collections_perc = fields.Float(string="Pending Collections(%)", compute='pendingCollection', store=True)
    total_due_amount = fields.Float('Total Due Amount', compute='installment', store=True)
    total_due_amount_perc = fields.Float(string="Total Due Amount(%)", compute='dueamountperc', store=True)
    due_balance_collections = fields.Float('Balance Due Collection', compute='dueamount', store=True)
    due_balance_perc = fields.Float(string="Balance Due Collection(%)", compute='duebalanceperc', store=True)
    escrow = fields.Float(string="Escrow Receipts", compute='_escrow', store=True)
    escrow_perc = fields.Float(string="Escrow Receipt Percentage", compute='escrow_perct', store=True)
    non_escrow = fields.Float(string="Non Escrow Receipts", compute='_escrow', store=True)
    non_escrow_perc = fields.Float(string="Non Escrow Receipt Percentage", compute="non_escrow_perct", store=True)
    total_escrow = fields.Float("Total", compute="escrow_tot", store=True)
    total_escrow_perc = fields.Float("Total Percentage", compute="tot_escrow_perct", store=True)

    @api.onchange('property')
    def get_spa(self):
        sale_orders = self.env['sale.order'].search(
            [('property_id', '=', self.property.id), ('asset_project_id', '=', self.project.id),
             ('state', 'not in', ['draft', 'cancel', 'rejected'])])
        if sale_orders:
            self.spa = sale_orders[0].id
        else:
            self.spa = False

    @api.depends('spa.receipt_ids')
    def _escrow(self):
        for rec in self:
            for tot in rec.spa.receipt_ids:
                if tot.sub_type.name == 'Escrow' and tot.state == 'posted':
                    rec.escrow += tot.amount
                if tot.sub_type.name != 'Escrow' and tot.state == 'posted':
                    rec.non_escrow += tot.amount

    @api.depends('escrow', 'spa.total_spa_value')
    def escrow_perct(self):
        for rec in self:
            if rec.spa.total_spa_value and rec.escrow:
                rec.escrow_perc = rec.escrow / rec.spa.total_spa_value * 100

    @api.depends('non_escrow', 'spa.total_spa_value')
    def non_escrow_perct(self):
        for rec in self:
            if rec.spa.total_spa_value and rec.non_escrow:
                rec.non_escrow_perc = rec.non_escrow / rec.spa.total_spa_value * 100

    @api.depends('escrow', 'non_escrow')
    def escrow_tot(self):
        for rec in self:
            rec.total_escrow = rec.escrow + rec.non_escrow

    @api.depends('total_escrow', 'spa.total_spa_value')
    def tot_escrow_perct(self):
        for rec in self:
            if rec.spa.total_spa_value and rec.total_escrow:
                rec.total_escrow_perc = rec.total_escrow / rec.spa.total_spa_value * 100


    @api.depends('total_collection', 'spa.total_spa_value')
    def totalCollection(self):
        for rec in self:
            if rec.spa.total_spa_value:
                rec.total_collection_perc = rec.total_collection / rec.spa.total_spa_value * 100

    @api.depends('realized_collection', 'spa.total_spa_value')
    def realizedCollection(self):
        for rec in self:
            if rec.spa.total_spa_value:
                rec.realized_collection_perc = rec.realized_collection / rec.spa.total_spa_value * 100

    @api.depends('pending_collections', 'spa.total_spa_value')
    def pendingCollection(self):
        for rec in self:
            if rec.spa.total_spa_value:
                rec.pending_collections_perc = rec.pending_collections / rec.spa.total_spa_value * 100

    @api.depends('total_due_amount', 'spa.total_spa_value')
    def dueamountperc(self):
        for rec in self:
            if rec.spa.total_spa_value:
                rec.total_due_amount_perc = rec.total_due_amount / rec.spa.total_spa_value * 100

    @api.depends('due_balance_collections', 'spa.total_spa_value')
    def duebalanceperc(self):
        for rec in self:
            if rec.spa.total_spa_value and rec.due_balance_collections:
                rec.due_balance_perc = rec.due_balance_collections / rec.spa.total_spa_value * 100

    @api.depends('spa', 'spa.total_spa_value')
    def _spavalue(self):
        for rec in self:
            rec.total_spa = rec.spa.total_spa_value

    @api.depends('spa', 'spa.matured_pdcs')
    def _spapdc(self):
        for rec in self:
            rec.realized_collection = rec.spa.matured_pdcs

    @api.depends('spa', 'spa.total_receipts')
    def totalcoll(self):
        for rec in self:
            rec.total_collection = rec.spa.total_receipts

    @api.depends('spa', 'spa.pending_balance')
    def pending(self):
        for rec in self:
            rec.pending_collections = rec.spa.pending_balance

    @api.depends('spa', 'spa.instalmnt_bls_pend_plus_admin_oqood')
    def installment(self):
        for rec in self:
            rec.total_due_amount = rec.spa.instalmnt_bls_pend_plus_admin_oqood

    @api.depends('spa', 'spa.balance_due_collection')
    def dueamount(self):
        for rec in self:
            rec.due_balance_collections = rec.spa.balance_due_collection

    name = fields.Char('Name', related='spa.partner_id.name', store=True)
    partner_id = fields.Many2one('res.partner', string='Name', related='spa.partner_id', store=True)
    mobile = fields.Char('Mobile', related='spa.partner_id.mobile', store=True)
    email = fields.Char("Email", related='spa.partner_id.email', store=True)
    # nationality = fields.Char("Nationality", related='spa.partner_id.nationality')
    address = fields.Char("Address", related='spa.partner_id.street', store=True)
    total_spa_customer = fields.Integer('Total SPA', compute="get_totals", store=True)
    # total_bookings = fields.Integer("Total Bookings", compute="get_totals")
    due_amount_to_clear = fields.Char("Due Amount to Clear")
    account_remarks = fields.Text("Accounts Remarks")

    state = fields.Selection([
        ('draft', 'Draft'),
        ('under_accounts_verification', 'Under Accounts Verification'),
        ('under_review', 'Under Review'),
        ('under_approval', 'Under Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('cancel', 'Canceled')
    ], string='Status', readonly=True, default='draft')

    def submit(self):
        for rec in self:
            rec.state = 'under_accounts_verification'

    def verify(self):
        for rec in self:
            rec.state = 'under_review'

    def review(self):
        for rec in self:
            rec.state = "under_approval"

    def approve(self):
        for rec in self:
            rec.state = "approved"

    def action_reject(self):
        for rec in self:
            rec.state = "rejected"

    def action_cancel(self):
        for rec in self:
            rec.state = "cancel"

    def action_draft(self):
        for rec in self:
            rec.state = "draft"

    @api.model
    def create(self, vals):
        if not vals.get('sequence', ''):
            vals['sequence'] = self.env['ir.sequence'].next_by_code(
                'account.clearance')
        result = super(AccountClearance, self).create(vals)
        return result

    @api.depends('partner_id')
    def get_totals(self):
        for rec in self:
            spa_ids = rec.env['sale.order'].search([('partner_id', '=', rec.partner_id.id), ('state', '!=', 'cancel')])
            if spa_ids and rec.partner_id:
                rec.total_spa_customer = len(spa_ids.ids)
            else:
                rec.total_spa_customer = False

    @api.model
    def old_account_clearance(self):
        sos = self.env['account.clearance'].search([])
        for rec in sos:
            if rec.spa:
                rec.partner_id = rec.spa.partner_id.id
                rec.mobile = rec.spa.partner_id.mobile
                rec.email = rec.spa.partner_id.email
                rec.address = rec.spa.partner_id.street
                rec.property = rec.spa.property_id
                rec.project = rec.spa.asset_project_id


class ClearanceType(models.Model):
    _name = 'clearance.type'
    _description = 'Clearance Type Form'

    name = fields.Char('Name')
    active = fields.Boolean(string='Active', default=True)
    handover = fields.Boolean(string='Handover', default=True)