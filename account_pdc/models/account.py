# -*- coding: utf-8 -*-
from odoo import fields, models, api, _, tools
# from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError, ValidationError


class ResPartnerBank(models.Model):
    _inherit = 'res.partner.bank'

    # @api.multi
    def name_get(self):
        return [(rpb.id, "%s %s %s" % (rpb.bank_id.name, rpb.acc_holder_name, rpb.acc_number)) for rpb in self]


# class AccountMoveLine(models.Model):
#     _inherit = 'account.move.line'
#
#     remarks = fields.Char('Remarks')
#     check_number = fields.Char('Check Number')
#     maturity_date = fields.Datetime('Maturity Date')
#     counterpart_name = fields.Char(compute='_get_counterpart', string="Counterpart")
#     move_line_ids = fields.One2many(related='move_id.line_ids', string='Entry Lines', readonly=True)
#
#     @api.depends('move_line_ids')
#     def _get_counterpart(self):
#         for journal_item in self:
#             if journal_item.move_line_ids:
#                 if len(journal_item.move_line_ids) == 2:
#                     for line in journal_item.move_line_ids:
#                         if line.id != journal_item.id:
#                             journal_item.counterpart_name = str(line.account_id.code) + ' ' + str(line.account_id.name)
