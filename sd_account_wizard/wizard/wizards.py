from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError


class AccountPDCsWizard(models.TransientModel):
    _name = "account.pdcs.wizard"
    _description = "Shift Receipts Wizard"

    def _get_payments(self):
        return self.env['account.payment'].browse(self.env.context.get('active_ids'))[0]

    customer = fields.Boolean(string='Shift to New Customer')
    project = fields.Boolean(string='Shift to New Project')
    property = fields.Boolean(string='Shift to New Property')
    booking = fields.Boolean(string='Shift to New Booking')
    partners = fields.Many2one('res.partner', "Customer", tracking=True)
    bookings = fields.Many2one('sale.order', "Booking", tracking=True)
    projects = fields.Many2one('account.asset.asset', 'Project', tracking=True)
    property_id = fields.Many2one('account.asset.asset', 'Property', tracking=True)
    payment = fields.Many2one('account.payment', 'Account', default=_get_payments)
    note = fields.Text('Note*', default='You cannot Shift Customer and Booking on Payment Form.', readonly=True)
    collection_type = fields.Boolean(string='Shift to New Collection Type')
    collection_type_id = fields.Many2one('collection.type', string="Collection Type")
    type = fields.Selection(
        [('inbound', 'Receive Money'), ('outbound', 'Send Money'), ('transfer', 'Internal Transfer')],
        related='payment.payment_type')

    def action_account_pdcs(self):
        line = self.env['account.payment'].search([('id', '=', self._context.get('active_ids', []))])
        # lines = self.env['account.move.line'].search([('id', '=', self._context.get('active_ids', []))])
        # move_line_obj = self.env['account.move.line'].search([('payment_id', '=', self.id)])
        if self.customer:
            for sd in line:
                sd.partner_id = self.partners.id
                for rec in sd.move_entry_ids:
                    if sd.move_entry_ids:
                        rec.partner_id = self.partners.id
                # for so in sd.move_outsourced_ids:
                #     if sd.move_outsourced_ids:
                #         so.partner_id = self.partners.id
                # for ac in sd.move_deposited_ids:
                #     if sd.move_deposited_ids:
                #         ac.partner_id = self.partners.id
                # for av in sd.move_bank_ids:
                #     if sd.move_bank_ids:
                #         av.partner_id = self.partners.id
                # for ax in sd.move_rejected_ids:
                #     if sd.move_rejected_ids:
                #         ax.partner_id = self.partners.id
                # for az in sd.bounced_move_deposited_ids:
                #     if sd.bounced_move_deposited_ids:
                #         az.partner_id = self.partners.id
        if self.booking:
            for ab in line:
                ab.spa_id = self.bookings.id

        if self.project:
            for av in line:
                av.asset_project_id = self.projects.id

        if self.property:
            for av in line:
                av.property_id = self.property_id
        
        if self.collection_type:
            for av in line:
                av.collection_type_id = self.collection_type_id