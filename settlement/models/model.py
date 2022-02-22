from odoo import api, models, fields, _
from datetime import datetime
from odoo.exceptions import UserError, ValidationError

class AccountSettlement(models.Model):
    _name = 'account.settlement'
    _description = "Account Settlement"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Subject', required=True, tracking=True, states={'posted': [('readonly', True)], 'cancel': [('readonly', True)]})
    journal_id = fields.Many2one('account.journal', required=True, string='Journal', tracking=True, states={'posted': [('readonly', True)], 'cancel': [('readonly', True)]})
    ledger_cr_id = fields.Many2one('account.account', 'Journal Ledger for Cr', compute='get_ledger_cr_id',
                                   store=True, tracking=True)
    date_range = fields.Boolean('Date Range', tracking=True, states={'posted': [('readonly', True)], 'cancel': [('readonly', True)]})
    start_date = fields.Date(string='Start Date', tracking=True, states={'posted': [('readonly', True)], 'cancel': [('readonly', True)]})
    end_date = fields.Date(string='End Date', tracking=True, states={'posted': [('readonly', True)], 'cancel': [('readonly', True)]})
    unsettled_receipt_total = fields.Float(compute='compute_unsettled_receipt_total', store=True, string='Unsettled Receipts Total', tracking=True)
    charges_perc = fields.Float(string='Charges %', tracking=True, states={'posted': [('readonly', True)], 'cancel': [('readonly', True)]})
    charges_amount = fields.Float(compute='get_charges_amount', store=True, string='Charges Amount', tracking=True)
    charges_calc_type = fields.Selection(
        [('fixed', 'Fixed Amount'),
         ('percent', 'Percentage')],string='Charges Calculation Type',
         states={'posted': [('readonly', True)], 'cancel': [('readonly', True)]},
         tracking=True)

    vat_perc = fields.Float(string='VAT %', tracking=True, states={'posted': [('readonly', True)], 'cancel': [('readonly', True)]})
    vat_amount = fields.Float(compute='get_vat_amount', store=True, string='VAT Amount', tracking=True)
    vat_calc_type = fields.Selection(
        [('fixed', 'Fixed Amount'),
         ('percent', 'Percentage')],string=' VAT Adjustment Type',
         states={'posted': [('readonly', True)], 'cancel': [('readonly', True)]},
         tracking=True)

    net_of_settlement = fields.Float(compute='get_net_of_settlement', store=True, string='Calculated Net Amount of Settlement', tracking=True)
    actual_as_per_bank = fields.Float(string='Actual Net Amount As Per Bank', tracking=True, states={'posted': [('readonly', True)], 'cancel': [('readonly', True)]})
    difference = fields.Float(compute='get_difference', store=True, string='Difference', tracking=True)
    entry_journal_id = fields.Many2one('account.journal', required=True, string='Entry Journal', tracking=True, states={'posted': [('readonly', True)], 'cancel': [('readonly', True)]})
    debit_ledger_settlement_id = fields.Many2one('account.account', 'Debit Ledger for Settlement Amount', tracking=True, states={'posted': [('readonly', True)], 'cancel': [('readonly', True)]})
    debit_ledger_charges_id = fields.Many2one('account.account', 'Debit Ledger for Charges', tracking=True, states={'posted': [('readonly', True)], 'cancel': [('readonly', True)]})
    debit_ledger_vat_id = fields.Many2one('account.account', 'Debit Ledger for VAT Adjustment', tracking=True, states={'posted': [('readonly', True)], 'cancel': [('readonly', True)]})

    unsettled_receipts_ids = fields.Many2many('account.payment', 'settlement_unsettled_receipts_rel', 'settlement_id', 'receipt_id', 'Unsettled Receipts', states={'posted': [('readonly', True)], 'cancel': [('readonly', True)]})

    journal_entry_id = fields.Many2one('account.move', 'Journal Pending Entry Associate')
    journal_item_ids = fields.One2many(related='journal_entry_id.line_ids', string='Journal Items', readonly=True)

    state = fields.Selection(
        [('draft', 'Draft'),
         ('posted', 'Posted'),
         ('cancel', 'Cancel')], default='draft',string='Status', tracking=True)

    company_id = fields.Many2one(
        'res.company',
        'Company',
        help="Company name which involve",
        default=lambda self: self.env.user.company_id)

    @api.depends('journal_id')
    def get_ledger_cr_id(self):
        for rec in self:
            rec.ledger_cr_id = rec.journal_id.payment_credit_account_id.id

    @api.depends('unsettled_receipt_total','charges_perc')
    def get_charges_amount(self):
        for rec in self:
            rec.charges_amount = rec.charges_perc/100 * rec.unsettled_receipt_total

    @api.depends('unsettled_receipt_total','vat_perc')
    def get_vat_amount(self):
        for rec in self:
            rec.vat_amount = rec.vat_perc/100 * rec.unsettled_receipt_total

    @api.depends('unsettled_receipt_total','charges_amount','vat_amount')
    def get_net_of_settlement(self):
        for rec in self:
            rec.net_of_settlement = rec.unsettled_receipt_total - rec.charges_amount - rec.vat_amount

    @api.depends('net_of_settlement','actual_as_per_bank')
    def get_difference(self):
        for rec in self:
            rec.difference = rec.net_of_settlement - rec.actual_as_per_bank


    @api.onchange('charges_calc_type')
    def onchnage_charges_calc_type(self):
        for rec in self:
            rec.charges_amount = False
            rec.charges_perc = False

    @api.depends('unsettled_receipts_ids','unsettled_receipts_ids.amount','unsettled_receipts_ids.state')
    def compute_unsettled_receipt_total(self):
        for rec in self:
            if rec.unsettled_receipts_ids:
                total = 0.00
                for receipt in rec.unsettled_receipts_ids:
                    if receipt.state not in ['draft'] and receipt.payment_type == 'inbound':
                        total += receipt.amount
                rec.unsettled_receipt_total = round(total, 2)

    # @api.multi
    def action_draft(self):
        print("Draft")
        self.write({'state': 'draft'})

    # @api.multi
    def action_validate(self):
        print('validate')
        for settlement in self:
            debit_charges_line_vals = {}
            account_credit_id = False
            account_debit_charges_id = False
            account_debit_settlement_id = False
            if settlement.journal_id.payment_credit_account_id:
                account_credit_id = settlement.ledger_cr_id.id if settlement.ledger_cr_id else settlement.journal_id.default_credit_account_id.id
            else:
                raise ValidationError("No Default credit account selected in journal")

            if settlement.charges_amount:
                print("charges_amount")
                if settlement.debit_ledger_charges_id:
                    account_debit_charges_id = settlement.debit_ledger_charges_id.id
                else:
                    raise ValidationError("Please Select Debit Ledger for Charges")

                debit_charges_line_vals = {
                    'name': settlement.name + " charges",
                    'date': datetime.now().strftime('%Y-%m-%d'),
                    # 'partner_id': settlement.partner_id.id,
                    'debit': settlement.charges_amount,
                    'credit': 0.0,
                    'account_id': account_debit_charges_id
                }

            if settlement.vat_amount:
                if settlement.debit_ledger_vat_id:
                    account_debit_vat_id = settlement.debit_ledger_vat_id.id
                else:
                    raise ValidationError("Please Select Debit Ledger for VAT Adjustment")

                debit_vat_line_vals = {
                    'name': settlement.name + " charges",
                    'date': datetime.now().strftime('%Y-%m-%d'),
                    # 'partner_id': settlement.partner_id.id,
                    'debit': settlement.vat_amount,
                    'credit': 0.0,
                    'account_id': account_debit_vat_id
                }

            if settlement.net_of_settlement:
                if settlement.debit_ledger_settlement_id:
                    account_debit_settlement_id = settlement.debit_ledger_settlement_id.id
                else:
                    raise ValidationError("Please Select Debit Ledger for Charges")

            debit_settlement_line_vals = {
                'name': settlement.name + " settlement",
                'date': datetime.now().strftime('%Y-%m-%d'),
                # 'partner_id': settlement.partner_id.id,
                'debit': settlement.net_of_settlement,
                'credit': 0.0,
                'account_id': account_debit_settlement_id
            }
            credit_line_vals = {
                'name': settlement.name + " Unsettled Receipt Total",
                'date': datetime.now().strftime('%Y-%m-%d'),
                # 'partner_id': settlement.partner_id.id,
                'debit': 0.0,
                'credit': settlement.unsettled_receipt_total,
                'account_id': account_credit_id
            }
            if settlement.charges_amount or settlement.vat_amount:
                if settlement.charges_amount and settlement.vat_amount:
                    lines = [(0, 0, debit_settlement_line_vals), (0, 0, debit_charges_line_vals), (0, 0, debit_vat_line_vals), (0, 0, credit_line_vals)]
                elif settlement.vat_amount:
                    lines = [(0, 0, debit_settlement_line_vals), (0, 0, debit_vat_line_vals),
                             (0, 0, credit_line_vals)]
                else:
                    lines = [(0, 0, debit_settlement_line_vals), (0, 0, debit_charges_line_vals),
                             (0, 0, credit_line_vals)]
            else:
                lines = [(0, 0, debit_settlement_line_vals), (0, 0, credit_line_vals)]

            settlement_entry_id = self.env['account.move'].create({
                'name': '/',
                'ref': settlement.name,
                'journal_id': settlement.entry_journal_id.id,
                'state': 'draft',
                'company_id': settlement.company_id.id,
                'line_ids': lines,
                'date': datetime.now().strftime('%Y-%m-%d'),
            })

            for receipt in settlement.unsettled_receipts_ids:
                receipt.settlement = 'done'
                receipt.settle = True
            settlement.write({'journal_entry_id': settlement_entry_id.id,
                              'state':'posted'})
            # move = settlement.env['account.move'].search([('id', '=', settlement_entry_id.id)])
            if settlement_entry_id:
                settlement_entry_id.post()

    # @api.multi
    def action_compute(self):
        print("compute")
        domain =[('payment_type','=','inbound'),('journal_id','=', self.journal_id.id)]
        if self.start_date:
            domain.append(('date', '>=', self.start_date))
        if self.end_date:
            domain.append(('date', '<=', self.end_date))

        domain.append(('state', '!=', 'cancelled'))
        receipt_ids = self.env['account.payment'].search(domain)
        if receipt_ids:
            self.unsettled_receipts_ids =  [(6,0, receipt_ids.ids)]


    # @api.multi
    def action_cancel(self):
        print("cancel")
        if self.journal_entry_id:
            self.journal_entry_id.button_cancel()
            self.journal_entry_id.unlink()
            # self.journal_entry_id.action_button_cancel()
            self.write({'state':'cancel'})
            for receipt in self.unsettled_receipts_ids:
                receipt.settlement = 'rejected'
                receipt.settle = True
        else:
            self.write({'state': 'cancel'})
            # for receipt in self.unsettled_receipts_ids:
                # receipt.settlement = 'rejected'
                # receipt.settle = True

class AccountJournal(models.Model):
    _inherit = 'account.journal'

    settlement = fields.Boolean('Settlement')


class Payment(models.Model):
    _inherit = 'account.payment'

    state = fields.Selection(selection_add=[('settle', 'Settled')])

    settle = fields.Boolean('settle', default=False)
    settlement_check = fields.Boolean('settlement', compute='compute_settlement_check', store=True)
    settlement = fields.Selection(
        [('not_applicable', 'Not Applicable'),
         ('in_process', 'In Process'),
         ('done', 'Done'),
         ('rejected', 'Rejected')],string='Settlement', compute='compute_settlement', store=True, tracking=True)

    # @api.multi
    def action_settle(self):
        self.write({'state': 'settle'})

    @api.depends('journal_id','journal_id.settlement')
    def compute_settlement_check(self):
        for rec in self:
            print("RunRun")
            if rec.journal_id.settlement != False:
                rec.settlement_check = True
                print("Check True")
            else:
                rec.settlement_check = False

    @api.depends('state','journal_id')
    def compute_settlement(self):
        for rec in self:
            if not rec.settle:
                if rec.state != 'posted' or not rec.journal_id.settlement:
                    rec.settlement = 'not_applicable'
                if rec.state == 'posted' and rec.journal_id.settlement:
                    rec.settlement = 'in_process'

    @api.model
    def old_compute_settlement(self):
        receipts = self.env['account.payment'].search([])
        for rec in receipts:
            if not rec.settle:
                if rec.state != 'posted' or not rec.journal_id.settlement:
                    rec.settlement = 'not_applicable'
                if rec.state == 'posted' and rec.journal_id.settlement:
                    rec.settlement = 'in_process'

    # @api.multi
    def create_settlement(self):
        ctx = self._context.copy()
        # settlement = self.env['account.settlement'].create({
        #     'name': self.name,
        #     'journal_id':self.journal_id.id,
        #     'entry_journal_id':self.journal_id.id,
        #     'unsettled_receipt_total': self.amount,
        #     'unsettled_receipts_ids': [(6, 0, self.ids)],
        # })
        ctx.update(
            {'default_name': self.name, 'default_journal_id': self.journal_id.id, 'default_entry_journal_id': self.journal_id.id,
             'default_unsettled_receipt_total': self.amount, 'default_unsettled_receipts_ids': [(6, 0, self.ids)]})
        return {
            'view_type': 'form',
            'view_id': self.env.ref('settlement.view_account_settlement_form').id,
            'view_mode': 'form',
            'res_model': 'account.settlement',
            # 'res_id': settlement.id,
            'type': 'ir.actions.act_window',
            'context': ctx,
            'target': 'new',
        }