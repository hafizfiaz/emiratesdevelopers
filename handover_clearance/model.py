from odoo import models, fields, api


class HandoverClearance(models.Model):
    _name = 'handover.clearance'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Handover Clearance'

    subject = fields.Char('Subject')
    sequence = fields.Char('Sequence', readonly=True)
    clearance_type = fields.Many2one('clearance.type', 'Approval Type')
    # booking_id = fields.Many2one('crm.booking', 'Booking', related='spa.booking_id')
    spa = fields.Many2one('sale.order', 'Related SPA/Booking')
    project = fields.Many2one('account.asset.asset', 'Project', domain="[('project', '=', True)]")
    property = fields.Many2one('account.asset.asset', 'Property')

    @api.onchange('property')
    def get_spa(self):
        sale_orders = self.env['sale.order'].search(
            [('property_id', '=', self.property.id), ('asset_project_id', '=', self.project.id),
             ('state', 'not in', ['draft', 'cancel', 'rejected'])])
        if sale_orders:
            self.spa = sale_orders[0].id
        else:
            self.spa = False

    # #
    # def approved_status(self):
    #     for rec in self:
    #         rec.project = rec.spa.booking_id.asset_project_id.id
    #         if rec.state == 'approved':
    #             print(rec.cs.id)
    #             rec.spa.status = 'handover_approved'
    #         else:
    #             rec.spa.status = 'handover_not_approved'

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
    ], string='SPA Status', related='spa.state', readonly=True, store=True)

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
    # unit_type_id = fields.Many2one('unit.type', 'Type', related='property.unit_type_id')
    size = fields.Float('Size(Sqft)', related='property.gfa_feet', store=True)
    parking = fields.Selection(
        [('1', '1'), ('2', '2'),
         ('3', '3'), ('4', '4'),
         ('5', '5+')],
        string='Parking', related='property.parking', store=True)
    oqood_status = fields.Many2one('oqood.status', 'Oqood Status', related='spa.oqood_status', store=True)
    admin_status = fields.Many2one('admin.status', 'Admin Status', related='spa.admin_status', store=True)
    receivable_status = fields.Many2one('receivable.status', 'Receivable Status', related='spa.receivable_status_id',
                                        store=True)
    # tag_ids = fields.Many2many('crm.lead.tag', 'crm_lead_tag_rel', 'lead_id', 'tag_id', string='Tags',
    #                            related='spa.tag_ids')
    discount_amount = fields.Float('Discount Amount')
    discount_amount_perc = fields.Float('Discount Percentage', compute="discountperc", store=True)
    notes = fields.Text('Sale Admin Team Remarks')
    handover_lines = fields.One2many('handover.clearance.lines', 'line_id')
    escrow = fields.Float(string="Escrow Receipts", compute='_escrow', store=True)
    escrow_perc = fields.Float(string="Escrow Receipt Percentage", compute='escrow_perct', store=True)
    non_escrow = fields.Float(string="Non Escrow Receipts", compute='_escrow', store=True)
    non_escrow_perc = fields.Float(string="Non Escrow Receipt Percentage", compute="non_escrow_perct", store=True)
    total_escrow = fields.Float("Total", compute="escrow_tot", store=True)
    total_escrow_perc = fields.Float("Total Percentage", compute="tot_escrow_perct", store=True)

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

    @api.model
    def default_get(self, fields):
        res = super(HandoverClearance, self).default_get(fields)
        handover_lines = []
        description = ['Title Deed Fee', 'Hanover Fee', 'Dewa Activation Fee', 'Service Charges']
        for rec in description:
            line = (0, 0, {
                'detail': rec
            })
            handover_lines.append(line)
            res.update({
                'handover_lines': handover_lines
            })
        return res

    @api.depends('discount_amount', 'property.total_price')
    def discountperc(self):
        for rec in self:
            if rec.discount_amount and rec.property.total_price:
                rec.discount_amount_perc = rec.discount_amount / rec.property.total_price * 100

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
        ('under_director_approval', 'Under Director Approval For Discount'),
        ('under_manager_review', 'Under Manager Review'),
        ('under_review', 'Under Review'),
        ('under_approval', 'Under Approval'),
        ('under_sd_admin', 'Under SD Admin'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('cancel', 'Canceled')
    ], string='Status', readonly=True, default='draft')

    def review(self):
        for rec in self:
            rec.state = 'under_accounts_verification'

    def submit_for_manager(self):
        for rec in self:
            rec.state = 'under_manager_review'

    def submit_for_discount(self):
        for rec in self:
            rec.state = 'under_director_approval'

    def discount_approve(self):
        for rec in self:
            rec.state = 'under_manager_review'

    def verify(self):
        for rec in self:
            rec.state = 'under_approval'

    def rollback(self):
        for rec in self:
            rec.state = "under_sd_admin"

    def approve(self):
        for rec in self:
            rec.state = "approved"
            rec.spa.handover_status = 'handover_approved'
            rec.property.handover_status = 'handover_approved'

    def action_reject(self):
        for rec in self:
            rec.state = "rejected"
            rec.spa.handover_status = 'handover_not_approved'
            rec.property.handover_status = 'handover_not_approved'

    def action_cancel(self):
        for rec in self:
            rec.state = "cancel"

    def action_draft(self):
        for rec in self:
            rec.state = "draft"

    def action_create(self):
        for rec in self:
            rec.state = "draft"

    @api.model
    def create(self, vals):
        if not vals.get('sequence', ''):
            vals['sequence'] = self.env['ir.sequence'].next_by_code(
                'handover.clearance')
        result = super(HandoverClearance, self).create(vals)
        return result

    @api.depends('partner_id')
    def get_totals(self):
        for rec in self:
            spa_ids = rec.env['sale.order'].search([('partner_id', '=', rec.partner_id.id), ('state', '!=', 'cancel')])
            # cb_ids = self.env['crm.booking'].search(
            #     [('partner_id', '=', self.partner_id.id), ('is_buy_state', '!=', 'cancel')])
            if spa_ids and rec.partner_id:
                rec.total_spa_customer = len(spa_ids.ids)
            else:
                rec.total_spa_customer = False
            # if cb_ids and self.partner_id:
            #     self.total_bookings = len(cb_ids.ids)
            # else:
            #     self.total_bookings = False

    @api.model
    def old_handover_fields(self):
        sos = self.env['handover.clearance'].search([])
        for rec in sos:
            if rec.spa:
                rec.partner_id = rec.spa.partner_id.id
                rec.mobile = rec.spa.partner_id.mobile
                rec.email = rec.spa.partner_id.email
                rec.address = rec.spa.partner_id.street
                rec.oqood_status = rec.spa.oqood_status
                rec.admin_status = rec.spa.admin_status
                rec.receivable_status = rec.spa.receivable_status_id
                rec.property = rec.spa.property_id
                rec.project = rec.spa.asset_project_id


class SaleOrder_inherit(models.Model):
    _inherit = ['sale.order']

    handover_status = fields.Selection([
        ('handover_approved', 'Handover Approved'),
        ('handover_not_approved', 'Handover Not Approved')
    ], string='Handover Status', default='handover_not_approved', readonly=True)


class PropertyAccount_inherit(models.Model):
    _inherit = ['account.asset.asset']

    handover_status = fields.Selection([
        ('handover_approved', 'Handover Approved'),
        ('handover_not_approved', 'Handover Not Approved')
    ], string='Handover Status', default='handover_not_approved', readonly=True)


class HandoverLines(models.Model):
    _name = 'handover.clearance.lines'
    _description = 'Handover Lines'

    detail = fields.Char('Detail')
    amount = fields.Float('Amount')
    approve_reject = fields.Selection([
        ('yes', 'Yes'), ('no', 'No')], string="Yes/No")
    remarks = fields.Char("Remarks")
    line_id = fields.Many2one("handover.clearance")
