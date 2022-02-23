from odoo import models, fields, api, _
from datetime import datetime
from odoo.exceptions import ValidationError


class SaleOrder_inherit(models.Model):
    _inherit = 'sale.order'

    early_settlment = fields.Char('Total Settlement')

    def early_settlement(self):
        # settlement = [-1]
        # st = self.env['early.settlement'].search([('spa','=',self.id)])
        # if st:
        #     settlement = st.ids
        ctx = {'default_spa': self.id}
        return {
            'name': _("'Early Settlement'"),
            'view_id': self.env.ref('sd_early_settlement.early_settlement').id,
            'view_mode': 'form',
            'context': ctx,
            'res_model': 'early.settlement',
            'type': 'ir.actions.act_window'
        }


class PartnerId_inherit(models.Model):
    _inherit = 'res.partner'

    early_settlment = fields.Many2one('early.settlement', 'Total Settlement')

    def early_settlement(self):
        ctx = {'default_spa':self.id}
        return{
            'name': _("'Early Settlement'"),
            'view_id': self.env.ref('sd_early_settlement.early_settlement').id,
            'view_mode': 'form',
            'context': ctx,
            'res_model': 'early.settlement',
            'type': 'ir.actions.act_window'
        }


class EarlySettlement(models.Model):
    _name = 'early.settlement'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Early Settlement'

    subject = fields.Char('Subject')
    sequence = fields.Char('Sequence', readonly=True)
    # clearance_type = fields.Many2one('clearance.type', 'Clearance Type')
    # booking_id = fields.Many2one('crm.booking', 'Related Booking', related='spa.booking_id')
    spa = fields.Many2one('sale.order', 'Related SPA/Booking')
    project = fields.Many2one('account.asset.asset', 'Project', related='spa.asset_project_id',domain="[('project', '=', True)]")
    property = fields.Many2one('account.asset.asset', 'Property', related='spa.property_id')
    spa_status = fields.Selection([
        ('draft', 'Unconfirmed SPA'),
        ('under_legal_review_print', 'Under Legal Review for Print'),
        ('under_acc_verification_print', 'Under Accounts Verification for Print'),
        ('under_confirmation_print', 'Under Confirmation for Print'),
        ('unconfirmed_ok_for_print', 'Unconfirmed SPA OK for Print'),
        ('under_legal_review', 'Under Legal Review'),
        ('under_accounts_verification', 'Under Accounts Verify'),
        ('under_approval', 'Under Approval'),
        ('under_spa_termination', 'Under SPA Termination'),
        ('under_termination', 'Under Termination'),
        ('sale', 'Approved SPA'),
        ('sent', 'Quotation Sent'),
        ('refund_cancellation', 'Refund Cancellation'),
        ('rejected', 'Rejected'),
        ('under_sd_admin_review', 'Under SD Admin Review'),
        ('paid', 'Approved SPA - Paid'),
        ('done', 'Locked'),
        ('cancel', 'Cancelled'),
    ], string='SPA Status', readonly=True)

    # booking_status = fields.Selection([
    #     ('draft', 'Draft'),
    #     ('under_discount_approval', 'Under Approval'),
    #     ('tentative_booking', 'Tentative Booking'),
    #     ('review', 'Under Review'),
    #     ('under_cancellation', 'Booking Under Cancellation'),
    #     ('confirm_spa', 'Confirmed for SPA'),
    #     ('approved', 'Approved'),
    #     ('rejected', 'Rejected'),
    #     ('cancel', 'Cancel')
    # ], string='Booking Status', related='booking_id.is_buy_state', readonly=True)
    total_spa = fields.Float('Total SPA Value', compute='_spavalue', store=True)
    discount = fields.Many2one('discount.type', 'Discount %')
    eligible_discount = fields.Float('Eligible Amount', compute='eligible_disc', store=True)
    early_settlement_amount = fields.Float('Early Settlement Amount')
    discount_amount = fields.Float('Discount Amount', compute='discamnt', store=True)
    amount_collect = fields.Float('Amount To Collect', compute='amnttocol', store=True)
    officer_remarks = fields.Text('Officers Remarks')
    note = fields.Text('Note*',
                       default='The Early Settlement amount will be adjusted with last dated installment first and so on.',
                       readonly=True)

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
    name = fields.Char('Name', related='spa.partner_id.name')
    partner_id = fields.Many2one('res.partner', string='Customer', related='spa.partner_id')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('under_accounts_approval', 'Under Accounts Approval'),
        ('under_sales', 'Under Sales Manager Review'),
        ('under_approval', 'Under Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('cancel', 'Canceled')
    ], string='Status', readonly=True, default='draft')

    def submit(self):
        for rec in self:
            rec.state = 'under_accounts_approval'

    def verify(self):
        for rec in self:
            rec.state = 'under_sales'

    def review(self):
        for rec in self:
            rec.state = 'under_approval'

    def action_reject(self):
        for rec in self:
            rec.state = "rejected"

    def action_cancel(self):
        for rec in self:
            rec.state = "cancel"

    def action_draft(self):
        for rec in self:
            rec.state = "draft"

    def approve(self):
        print('validate')
        for settlement in self:
            debit_charges_line_vals = {}
            account_credit_id = False
            account_debit_charges_id = False
            account_debit_settlement_id = False
            if not settlement.entry_journal:
                raise ValidationError("No journal selected")
            if not settlement.dr_entry_journal:
                raise ValidationError("Debit account not selected")
            if not settlement.cr_entry_journal:
                raise ValidationError("Credit account not selected")
            if not settlement.realized_collection:
                raise ValidationError("Total Amount not found")

            debit_line_vals = {
                'name': settlement.name + " charges",
                'date': datetime.now().strftime('%Y-%m-%d'),
                'asset_project_id': settlement.spa.asset_project_id.id,
                'property_id': settlement.spa.property_id.id,
                'partner_id': settlement.spa.partner_id.id,
                # 'partner_id': settlement.partner_id.id,
                'debit': settlement.discount_amount,
                'credit': 0.0,
                'account_id': settlement.dr_entry_journal.id
            }

            credit_line_vals = {
                'name': settlement.name + " settlement",
                'date': datetime.now().strftime('%Y-%m-%d'),
                # 'partner_id': settlement.partner_id.id,
                'asset_project_id': settlement.spa.asset_project_id.id,
                'property_id': settlement.spa.property_id.id,
                'partner_id': settlement.spa.partner_id.id,
                'debit': 0.0,
                'credit': settlement.discount_amount,
                'account_id': settlement.cr_entry_journal.id
            }

            lines = [(0, 0, debit_line_vals), (0, 0, credit_line_vals)]

            settlement_entry_id = self.env['account.move'].create({
                'name': '/',
                'ref': settlement.name,
                'journal_id': settlement.entry_journal.id,
                'state': 'draft',
                'company_id': settlement.company_id.id,
                'line_ids': lines,
                'date': datetime.now().strftime('%Y-%m-%d'),
            })
            settlement.write({'journal_entry_id': settlement_entry_id.id,
                              'state': 'approved'})
            if settlement_entry_id:
                settlement_entry_id.post()

    entry_journal = fields.Many2one('account.journal', "Accounting Entry Journal")
    dr_entry_journal = fields.Many2one('account.account', "Dr Accounting Ledger")
    cr_entry_journal = fields.Many2one('account.account', "Cr Accounting Ledger")
    # company_id = fields.Many2one(
    #     'res.company',
    #     'Company',
    #     help="Company name which involve")
    journal_entry_id = fields.Many2one('account.move', 'Journal Entry')
    journal_item_ids = fields.One2many(related='journal_entry_id.line_ids', string='Journal Items', readonly=True)

    @api.onchange('partner_id.property_account_receivable_id')
    def onchange_entry(self):
        for rec in self:
            rec.cr_entry_journal = rec.partner_id.property_account_receivable_id.name

    @api.depends('partner_id.property_account_receivable_id')
    def cr_entry(self):
        for rec in self:
            if rec.partner_id.property_account_receivable_id:
                rec.cr_entry_journal = rec.partner_id.property_account_receivable_id

    @api.depends('total_collection', 'spa.total_spa_value')
    def totalCollection(self):
        for rec in self:
            if rec.spa.total_spa_value:
                rec.total_collection_perc = rec.total_collection / rec.spa.total_spa_value * 100

    #
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

    @api.onchange('spa')
    def eligible_disc(self):
        current_date = datetime.now().date()
        for rec in self:
            if rec.spa:
                sum = 0
                if rec.spa.matured_pdcs == rec.spa.total_spa_value:
                    rec.eligible_discount = 0
                else:
                    for line in rec.spa.sale_payment_schedule_ids:
                        if line.state == 'confirm' and line.installment_status == 'unpaid' and line.start_date:
                            dates_diff = line.start_date - current_date
                            if dates_diff.days > 329:
                                sum = rec.total_spa - rec.realized_collection
                            else:
                                sum = 0
                    rec.eligible_discount = sum

    @api.model
    def cron_eligible_disc(self):
        so = self.env['early.settlement'].search([])
        current_date = datetime.now().date()
        for rec in so:
            if rec.spa:
                sum = 0
                if rec.spa.matured_pdcs == rec.spa.total_spa_value:
                    rec.eligible_discount = 0
                else:
                    for line in rec.spa.sale_payment_schedule_ids:
                        if line.state == 'confirm' and line.installment_status == 'unpaid' and line.start_date:
                            dates_diff = rec.start_date - current_date
                            if dates_diff.days > 329:
                                sum += line.amount
                    rec.eligible_discount = sum

    @api.depends('early_settlement_amount', 'discount.amnt')
    def discamnt(self):
        for rec in self:
            if rec.early_settlement_amount:
                rec.discount_amount = rec.early_settlement_amount * rec.discount.amnt / 100

    @api.depends('early_settlement_amount', 'discount_amount')
    def amnttocol(self):
        for rec in self:
            if rec.early_settlement_amount:
                rec.amount_collect = rec.early_settlement_amount - rec.discount_amount

    @api.model
    def create(self, vals):
        if not vals.get('sequence', ''):
            vals['sequence'] = self.env['ir.sequence'].next_by_code(
                'early.settlement')
        result = super(EarlySettlement, self).create(vals)
        return result


class ClearanceType(models.Model):
    _name = 'discount.type'
    _description = 'Discount Form'

    name = fields.Char('Name')
    amnt = fields.Float('Discount %')
    active = fields.Boolean(string='Active', default=True)
    project = fields.Char('Project')
