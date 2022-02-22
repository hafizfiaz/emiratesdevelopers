from odoo import _, api, models, fields
from odoo.exceptions import UserError
import time


class ChargeType(models.Model):
    _name = 'charge.type'
    _description = "Charge Type"

    name = fields.Char('Name')
    active = fields.Boolean(string='Active', default=True)


class AccountMove_inherit(models.Model):
    _inherit = 'account.move'

    charge_type = fields.Many2one('charge.type', 'Charge Type')


class SaleOrder_inherit(models.Model):
    _inherit = 'sale.order'

    def get_charges_details(self, charges):
        result_rec = []
        if charges.add_charges_ids:
            for line in charges.add_charges_ids:
                vals = {'name': line.charge_type.name, 'amount': round(line.amount, 2), 'received': 0, 'balance': 0}
                for jv_line in line.line_ids:
                    total = 0
                    if jv_line.full_reconcile_id:
                        if jv_line.matched_debit_ids:
                            for mdids in jv_line.matched_debit_ids:
                                total += mdids.amount
                        if jv_line.matched_credit_ids:
                            for mdids in jv_line.matched_credit_ids:
                                total += mdids.amount
                    vals['received'] = total
                    vals['balance'] = line.amount - total
                result_rec.append(vals)
        return result_rec
