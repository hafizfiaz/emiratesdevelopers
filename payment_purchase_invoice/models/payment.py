# -*- coding: utf-'8' "-*-"
from odoo import models, fields, api, _


class AccountMove(models.Model):
    _inherit = 'account.move'

    purchase_payment_id = fields.Many2one('account.payment', string='Payment',
                                          domain=[('payment_type', '=', 'outbound')])
    old_invoice_id = fields.Integer('Old Invoice Id')


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    invoice_lines = fields.One2many('account.move', 'purchase_payment_id', string='Purchase Invoices')
    invoices_not_used = fields.Many2many('account.move', 'invoice_ids', 'payment_id',
                                         'user_id', compute='get_inv_not_used', string='Invoices Not Used')

    def get_inv_not_used(self):
        for rec in self:
            paymnts = rec.env['account.payment'].search([('payment_type', '=', 'outbound'),('invoice_lines', '!=', False),('state', 'not in', ['draft', 'cancelled'])])
            invs=[]
            for line in paymnts:
                for line1 in line.invoice_lines:
                    invs.append(line1.id)
            invoices = rec.env['account.move'].search(
                    [('state', 'in', ['paid', 'posted']),('move_type', '=', 'in_invoice'),('id', 'not in', list(set(invs)))])
            rec.invoices_not_used = [(6, 0, invoices.ids)]
