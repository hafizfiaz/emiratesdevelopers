from datetime import datetime
from odoo import models, fields, api, _


class PaymentSchedule(models.Model):
    _inherit = 'sale.rent.schedule'

    aging_date = fields.Integer("Aging Days", compute='calculate_tot_days', store=True, tracking=True)

    @api.depends('start_date')
    def calculate_tot_days(self):
        for rec in self:
            if rec.start_date:
                current_date = datetime.now()
                d1 = datetime.strptime(str(rec.start_date), '%Y-%m-%d')
                d3 = current_date - d1
                rec.aging_date = str(d3.days)


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    state = fields.Selection(
        [('draft', 'Draft'),
         ('under_accounts_verification', 'Under Accounts Verification'),
         ('under_review', 'Under Chief Accountant Review'),
         ('under_fm_review', 'Under FM Review'),
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
         ('settle', 'Settled'),
         ], 'Status', readonly=True, default='draft', tracking=True)

    def action_under_fm_review(self):
        self.write({'state': 'under_fm_review'})

    # @api.model
    # def sent_collected_email(self):
    #     pdc = self.env['account.payment'].search(
    #         [('state', '=', 'collected'), ('payment_type', '=', 'outbound'), ('journal_id.type', '=', 'pdc')])
    #     for rec in pdc:
    #         if rec.maturity_date:
    #             current_date = datetime.now()
    #             dates_diff = rec.maturity_date - current_date
    #             days = dates_diff.days
    #             if days == 7:
    #                 mr = rec.env['mail.recipients'].search([('name', '=', 'FGR Due Alert')])
    #                 for recss in mr:
    #                     if recss.user_ids:
    #                         email_template = rec.env.ref('sd_accounting_workflow_inherit.collected_email')
    #                         if email_template.mail_server_id:
    #                             email_template.email_from = email_template.mail_server_id.name
    #                         email_template.email_to = recss.get_partner_ids(recss.user_ids)
    #                         email_template.send_mail(rec.id, force_send=True)
