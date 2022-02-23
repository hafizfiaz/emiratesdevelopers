from odoo import models, fields, api, _


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    collection_type_id = fields.Many2one('collection.type', string="Collection Type",
                                         related='payment_id.collection_type_id', store=True, tracking=True)
    maturity_date = fields.Datetime('Maturity Date', related='payment_id.maturity_date', store=True, tracking=True)
    collection_date = fields.Datetime('Collection Date', related='payment_id.collection_date', store=True,
                                      tracking=True)
    nets_amount = fields.Float(string="Net Amount", related='payment_id.nets_amount', store=True)
    posting_date = fields.Datetime('Posting Date', related='payment_id.posting_date', store=True, tracking=True)
    paid_date = fields.Datetime('Paid Date', related='payment_id.paid_date', store=True, tracking=True)
    bounced_date = fields.Date('Bounced Date', related='payment_id.bounced_date', store=True, tracking=True)
    officer_id = fields.Many2one('res.users', 'Collection Officer', related='payment_id.officer_id', store=True,
                                 tracking=True)
    hold_date = fields.Date('Hold Date', related='payment_id.hold_date', store=True)
    bank_deposit = fields.Many2one('res.partner.bank', 'Bank where the check is deposit/cashed',
                                   related='payment_id.bank_deposit', store=True)
    amount_payment = fields.Monetary('Payment Amount', related='payment_id.amount', store=True)
    vendor_type = fields.Many2one('vendor.type', 'Vendor Type', related='payment_id.vendor_type', store=True)
    posting_greater = fields.Boolean('Posting Date Greater Then Payment Date', compute='posting_greater_then_payment', store=True)
    # approval_from_ids = fields.Many2many('res.users', 'receipt_approval_rel', 'receipt_approval_id', 'user_id', related='payment_id.approval_from_ids',
    #                                      string='Approval From', store=True)
    state_receipt = fields.Selection(
        [('draft', 'Draft'),
         ('under_accounts_verification', 'Under Accounts Verification'),
         ('under_review', 'Under Review'),
         ('under_approval', 'Under Approval'),
         ('approved', 'Approved'),
         ('rejected', 'Rejected'),
         ('proforma', 'Pro-forma'),
         ('pending', 'Pending for Collection'),
         ('collected', 'Collected'),
         ('outsourced', 'Withdraw'),
         ('stale', 'Stale'),
         ('replaced', 'Replaced'),
         ('hold', 'Hold'),
         ('deposited', 'Deposited'),
         ('posted', 'Posted'),
         ('sent', 'Sent'),
         ('reconciled', 'Reconciled'),
         ('cancelled', 'Cancelled'),
         ('refused', 'Bounced'),
         ], 'Receipt Status', readonly=True, related='payment_id.state', store=True, tracking=True)

    @api.depends('posting_date', 'date')
    def posting_greater_then_payment(self):
        for rec in self:
            check = False
            if rec.posting_date and rec.date:
                if rec.posting_date.date() > rec.date:
                    check = True
                else:
                    check = False
            rec.posting_greater = check

