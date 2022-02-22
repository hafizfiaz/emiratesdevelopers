from odoo import models, fields, api, _


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    count = fields.Integer('Count', readonly=True, default=1, tracking=True)


class PropertyInherit(models.Model):
    _inherit = 'account.asset.asset'

    count = fields.Integer('Count', readonly=True, default=1, tracking=True)


class TerminationInherit(models.Model):
    _inherit = 'termination.process'

    count = fields.Integer('Count', readonly=True, default=1, tracking=True)


class CommissionInherit(models.Model):
    _inherit = 'commission.invoice'

    count = fields.Integer('Count', readonly=True, default=1, tracking=True)


class AccountMove(models.Model):
    _inherit = 'account.move'

    count = fields.Integer('Count', readonly=True, default=1, tracking=True)


class ApprovalBill(models.Model):
    _inherit = 'approval.approval'

    count = fields.Integer('Count', readonly=True, default=1, tracking=True)


class PaymentReceipts(models.Model):
    _inherit = 'account.payment'

    count = fields.Integer('Count', readonly=True, default=1, tracking=True)