from odoo import models, fields, api, exceptions, _
from odoo.addons.payment.models.payment_acquirer import ValidationError
from datetime import datetime, timedelta


class RefundEoi(models.Model):
    _name = 'refund.eoi'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Refund EOI'

    name = fields.Char('Sequence', readonly=True)
    partner_id = fields.Many2one('res.partner', 'Customer Name', related="receipt_lines.partner_id", store=True)
    mobile = fields.Char('Mobile', related="receipt_lines.mobile", store=True)
    total = fields.Float('EOI Total Receipts Amount', compute='compute_receipt_total', store=True)
    refund_amnt = fields.Float('Amount to be Refunded', required=True)
    remarks = fields.Text('Sale Admin Remarks')
    refund_note = fields.Text('Refund Method Detail')
    receipt_lines = fields.One2many('account.payment', 'reoi_receipt_id', 'Receipts')
    payment_ids = fields.One2many('account.payment', 'reoi_id', string='Payments')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('under_sales', 'Under Sales Manager Review'),
        ('under_accounts', 'Under Accounts for Payment'),
        ('accounts_return', 'Accounts Return Back'),
        ('approved', 'Paid'),
        ('reject', 'Reject'),
        ('cancel', 'Canceled')
    ], string='Status', readonly=True, default='draft')

    @api.depends('receipt_lines', 'receipt_lines.amount')
    def compute_receipt_total(self):
        for rec in self:
            if rec.receipt_lines:
                tot = 0.00
                for receipt in rec.receipt_lines:
                    tot += receipt.amount
                    rec.total = round(tot, 2)

    @api.constrains('refund_amnt')
    def refund_constrains(self):
        for rec in self:
            if rec.refund_amnt > rec.total:
                raise ValidationError(_('The refund amount cannot exceed the EOI receipt amount'))

    @api.model
    def create(self, vals):
        if not vals.get('name', ''):
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'refund.eoi')
        result = super(RefundEoi, self).create(vals)
        mr = self.env['mail.recipients'].search([('name', '=', 'Refund EOI Creation')])
        for rec in mr:
            email_template = rec.env.ref('sd_refund_eoi.refund_eoi_created')
            email_template.send_mail(result.id, force_send=True)
        print("USMAAAAAAAAN")
        return result

    # @api.model
    # def create(self, vals):
    #     result = super(RefundEOIInherit, self).create(vals)
    #     mr = self.env['mail.recipients'].search([('name', '=', 'Refund EOI Creation')])
    #     for rec in mr:
    #         email_template = rec.env.ref('refund_eoi_inherit.refund_eoi_created')
    #         email_template.send_mail(result.id, force_send=True)
    #     print("USMAAAAAAAAN")
    #     return result

    def review(self):
        mr = self.env['mail.recipients'].search([('name', '=', 'Refund EOI Alert')])
        for rec in mr:
            email_template = rec.env.ref('sd_refund_eoi.receipt_approval_id')
            email_template.send_mail(self.id, force_send=True)
        self.write({'state': 'under_accounts'})

    def submit_to_manager(self):
        for rec in self:
            rec.state = "under_sales"

    def account_return(self):
        for rec in self:
            rec.state = "accounts_return"

    def action_cancel(self):
        for rec in self:
            rec.state = "cancel"

    def action_reject(self):
        for rec in self:
            rec.state = "reject"

    def action_paid(self):
        for rec in self:
            payment_form_id = self.env.ref('sd_refund_eoi.view_account_payment_reoi_form').id
            return {
                'view_id': payment_form_id,
                'view_mode': 'form',
                'res_model': 'account.payment',
                'context': {'default_payment_type': 'outbound', 'default_partner_type': 'supplier',
                            'default_partner_id': rec.partner_id.id,
                            'default_reoi_id': rec.id, 'default_communication': rec.name,
                            'default_amount': rec.refund_amnt},
                'type': 'ir.actions.act_window',
                'target': 'new',
            }

    def action_draft(self):
        for rec in self:
            rec.state = "draft"

    # status_log_ids = fields.One2many('status.log', 'roi_id', string='Status Logs')
    # state_change = fields.Char(compute="get_state", store=True, string="State Change")
    #
    # def get_state_name(self, state):
    #     state_return = ''
    #     if state == 'draft':
    #         state_return = 'Draft'
    #     if state == 'under_accounts':
    #         state_return = 'Under Accounts for Payment'
    #     if state == 'accounts_return':
    #         state_return = 'Accounts Return Back'
    #     if state == 'approved':
    #         state_return = 'Paid'
    #     if state == 'cancel':
    #         state_return = 'Canceled'
    #     return state_return

    # @api.depends('state')
    # def get_state(self):
    #     # print("abc")
    #     for rec in self:
    #         old_state = False
    #         days = False
    #         prevous_log = rec.env['status.log'].search([('model_name', '=', rec._name), ('record_id', '=', rec.id)],
    #                                                    order='updated_date DESC', limit=1)
    #         if prevous_log:
    #             old_state = prevous_log.status_to
    #             current_date = datetime.now()
    #             prevous_log_date = prevous_log.updated_date
    #             dates_diff = current_date.date() - prevous_log_date.date()
    #             days = dates_diff.days
    #         rec.env['status.log'].create({
    #             'model_name': rec._name,
    #             'record_id': rec.id,
    #             'roi_id': rec.id,
    #             'status_from': old_state,
    #             'status_to': rec.get_state_name(rec.state),
    #             'days': days
    #         })
    #         rec.state_change = rec.get_state_name(rec.state)


class AccountPayment(models.Model):
    _inherit = "account.payment"

    line_id = fields.Many2one("refund.eoi")
    # eoi = fields.Boolean("Refund EOI", compute="compute_collection_check")
    reoi_id = fields.Many2one('refund.eoi', 'Refund Id')
    reoi_receipt_id = fields.Many2one('refund.eoi', 'Refund EOI')
    refund_eoi_status = fields.Selection([
        ('draft', 'Draft'),
        ('under_accounts', 'Under Accounts for Payment'),
        ('accounts_return', 'Accounts Return Back'),
        ('approved', 'Paid'),
        ('cancel', 'Canceled')
    ], string='Refund EOI Status', related='reoi_receipt_id.state', store=True)

    refund_count = fields.Integer(compute="_refund_count", string="Refund Count")

    def _refund_count(self):
        for rec in self:
            refunds = 0
            refunds_ids = rec.env['refund.eoi'].search([])
            for line in refunds_ids:
                for r in line.receipt_lines:
                    if rec.id == r.id:
                        refunds += 1
            rec.refund_count = refunds

    def action_reoi_pay(self):
        for rec in self:
            if rec.reoi_id:
                mr = self.env['mail.recipients'].search([('name', '=', 'Refund Paid Email')])
                for sd in mr:
                    email_template = sd.env.ref('sd_refund_eoi.payment_approval_id')
                    email_template.send_mail(self.id, force_send=True)
                rec.post()
                rec.reoi_id.state = 'approved'

    def get_related_refund(self):
        for rec in self:
            refunds = []
            refunds_ids = rec.env['refund.eoi'].search([])
            for line in refunds_ids:
                for r in line.receipt_lines:
                    if rec.id == r.id:
                        refunds.append(line.id)
            ctx = self._context.copy()
            ctx.update(
                {'default_name': self.name,
                 'default_total': self.amount, 'default_receipt_lines': [(6, 0, self.ids)]})
            return {
                'name': _('Refund EOIs'),
                'view_mode': 'tree,form',
                'view_id': False,
                'res_model': 'refund.eoi',
                'type': 'ir.actions.act_window',
                'domain': [('id', 'in', refunds)],
                'context': ctx,
            }

    # @api.depends('collection_type_id.eoi')
    # def compute_collection_check(self):
    #     for rec in self:
    #         if rec.collection_type_id.name == 'Expression of Interest Collection':
    #             rec.eoi = True
    #             print("Check True")
    #         else:
    #             rec.eoi = False

    def create_eoi(self):
        ctx = self._context.copy()
        ctx.update(
            {'default_name': self.name,
             'default_total': self.amount, 'default_receipt_lines': [(6, 0, self.ids)]})
        return {
            'view_id': self.env.ref('sd_refund_eoi.refund_eoi_clearance').id,
            'view_mode': 'form',
            'res_model': 'refund.eoi',
            'type': 'ir.actions.act_window',
            'context': ctx,
            'target': 'new',
        }

# class CollectionType(models.Model):
#     _inherit = 'collection.type'
#
#     eoi = fields.Boolean("Refund EOI", default=False)
#
#
# class StatusLog(models.Model):
#     _inherit = "status.log"
#
#     roi_id = fields.Many2one('refund.eoi', 'Refund Id')
