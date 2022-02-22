from odoo import models, fields, api, _
from datetime import datetime


class ReceiptsInherit(models.Model):
    _inherit = 'account.payment'

    @api.constrains('check_number', 'journal_id')
    def _constrains_check_number(self):
        return