# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.tools import safe_eval
from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from odoo.exceptions import UserError, ValidationError


class AccountAssetAsset(models.Model):
    _inherit = "account.asset.asset"

    premium_finish_ledger_id = fields.Many2one('account.account','Premium Finish Ledger')


class PremiumFinishPaymentSchedule(models.Model):
    _name = "premium.finish.ps"

    name = fields.Char('Description', required=True)
    date = fields.Date('Payment Date', required=True)
    amount = fields.Float('Amount', required=True)
    sale_id = fields.Many2one('sale.order', string='SPA', ondelete="cascade")
    invc_id = fields.Many2one('account.move', string='Invoice', tracking=True)
    inv = fields.Boolean(string='Invoiced?', tracking=True)

    def get_invloice_lines(self):
        for rec in self:
            inv_line = {
                'name': rec.name,
                'price_unit': rec.amount or 0.00,
                'quantity': 1,
                'property_id': rec.sale_id.property_id.id,
                'asset_project_id': rec.sale_id.asset_project_id.id,
                'account_id': rec.sale_id.asset_project_id.premium_finish_ledger_id.id or False,
                'tax_ids': [(6, 0, [1])],
            }
            return [(0, 0, inv_line)]

    @api.model
    def create_premium_invoice_auto(self):
        inv_obj = self.env['account.invoice']
        premium_sche = self.env['premium.finish.ps'].search(
            [('date', '<=', datetime.now().date()), ('inv', '!=', True)])
        for rec in premium_sche:
            if not rec.sale_id:
                pass
            if not rec.sale_id.asset_project_id.premium_finish_ledger_id:
                pass
            if rec.sale_id.internal_type == 'spa' and rec.sale_id.state not in ['refund_cancellation','cancel'] and rec.sale_id.finish_type == 'premium_finish':
                inv_line_values = rec.get_invloice_lines()
                inv_values = {
                    'premium_schedule_id': rec.id,
                    'partner_id': rec.sale_id.partner_id.id or False,
                    'move_type': 'out_invoice',
                    'invoice_date_due': rec.date,
                    'property_id': rec.sale_id.property_id.id or False,
                    'asset_project_id': rec.sale_id.asset_project_id.id or False,
                    'invoice_date': rec.date or False,
                    'invoice_line_ids': inv_line_values,
                }
                invoice_id = inv_obj.create(inv_values)
                rec.write({'invc_id': invoice_id.id, 'inv': True})

    def create_invoice(self):
        inv_obj = self.env['account.move']
        for rec in self:
            if not rec.sale_id:
                raise UserError('SPA not selected!')
            if not rec.sale_id.asset_project_id.premium_finish_ledger_id:
                raise UserError('Premium Finish Ledger not selected on Project')
            if rec.sale_id.internal_type == 'spa' and rec.sale_id.state not in ['refund_cancellation','cancel'] and rec.sale_id.finish_type == 'premium_finish':
                inv_line_values = rec.get_invloice_lines()
                inv_values = {
                    'premium_schedule_id': rec.id,
                    'partner_id': rec.sale_id.partner_id.id or False,
                    'move_type': 'out_invoice',
                    'invoice_date_due': rec.date,
                    'property_id': rec.sale_id.property_id.id or False,
                    'asset_project_id': rec.sale_id.asset_project_id.id or False,
                    'invoice_date': rec.date or False,
                    'invoice_line_ids': inv_line_values,
                }
                invoice_id = inv_obj.create(inv_values)
                rec.write({'invc_id': invoice_id.id, 'inv': True})
                inv_form_id = rec.env.ref('account.view_move_form').id

                return {
                    'view_type': 'form',
                    'view_id': inv_form_id,
                    'view_mode': 'form',
                    'res_model': 'account.move',
                    'res_id': rec.invc_id.id,
                    'type': 'ir.actions.act_window',
                    'target': 'current',
                }

    def open_invoice(self):
        return {
            'view_id': self.env.ref('account.view_move_form').id,
            'view_mode': 'form',
            'res_model': 'account.move',
            'res_id': self.invc_id.id,
            'type': 'ir.actions.act_window',
            'target': 'current',
        }

class AccountMove(models.Model):
    _inherit = "account.move"

    premium_schedule_id = fields.Many2one('premium.finish.ps', 'Premium Schedule')