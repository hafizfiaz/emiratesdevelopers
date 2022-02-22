# See LICENSE file for full copyright and licensing details
from odoo import fields, models


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    # asset_project_id = fields.Many2one(
    #     comodel_name='account.asset.asset',
    #     string='Project')
    property_id = fields.Many2one(
        comodel_name='account.asset.asset',
        string='Property')
    is_property = fields.Boolean(
        string='Is Property')

    # _sql_constraints = [
    #     ('accountable_required_fields',
    #         "CHECK(display_type IS NOT NULL OR (property_id IS NOT NULL AND product_uom IS NOT NULL))",
    #         "Missing required fields on accountable sale order line."),
    #
    # ]

class SaleOrder(models.Model):
    _inherit = "sale.order"

    is_property = fields.Boolean(
        string='Is Property',
        default=False)
