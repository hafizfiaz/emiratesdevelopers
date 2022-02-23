from odoo import models, fields, api, _


class AccountMove(models.Model):
    _inherit = 'account.move'

    new_fields_invoice = fields.Boolean("New Workflow", default=True)

    def submit_for_review(self):
        self.write({'state': 'under_review'})

    def action_review(self):
        self.write({'state': 'under_approval'})

    def action_validate(self):
        self.write({'state': 'posted'})

    def action_reject(self):
        self.write({'state': 'rejected'})

    def action_cancel(self):
        self.write({'state': 'cancel'})

    def action_draft(self):
        self.write({'state': 'draft'})



