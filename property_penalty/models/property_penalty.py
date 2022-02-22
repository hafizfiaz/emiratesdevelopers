# See LICENSE file for full copyright and licensing details

from dateutil.relativedelta import relativedelta

from odoo import models, fields, api, _
from datetime import datetime


class AccountAnalyticAccount(models.Model):
    _inherit = "account.analytic.account"

    penalty = fields.Float(
        string='Penalty (%)')
    penalty_day = fields.Integer(
        string='Penalty Count After Days')
    penalty_a = fields.Boolean(
        'Penalty',
        default=True)


class TenancyRentSchedule(models.Model):
    _inherit = "tenancy.rent.schedule"
    _rec_name = "tenancy_id"
    _order = 'start_date'

    penalty_amount = fields.Float(
        string='Penalty',
        store=True)

    # @api.multi
    def calculate_penalty(self):
        """
        This Method is used to calculate penalty.
        -----------------------------------------
        @param self: The object pointer
        """
        today_date = datetime.today().date()
        for one_payment_line in self:
            if not one_payment_line.paid:
                ten_date = one_payment_line.start_date
                if one_payment_line.tenancy_id.penalty_day != 0:
                    ten_date = ten_date + \
                        relativedelta(
                            days=int(one_payment_line.tenancy_id.penalty_day))
                if ten_date < today_date:
                    if (today_date - ten_date).days:
                        line_amount_day = (
                            one_payment_line.tenancy_id.rent
                            * one_payment_line.tenancy_id.penalty) / 100
                        self.write({'penalty_amount': line_amount_day})
        return True

    # @api.multi
    def get_invloice_lines(self):
        """TO GET THE INVOICE LINES"""
        for rec in self:
            inv_lines = super(TenancyRentSchedule, self).get_invloice_lines()
            inv_line_values = inv_lines[0][2]
            rec.calculate_penalty()
            if rec.tenancy_id.penalty < 00:
                raise Warning(_(
                    'The Penalty% must be strictly positive.'))
            if rec.tenancy_id.penalty_day < 00:
                raise Warning(_('The Penalty Count After Days must be \
                strictly positive.'))
            amt = rec.amount + rec.penalty_amount
            inv_line_values.update({'price_unit': amt or 0.00})
            return inv_lines
