# from openerp.osv import fields, orm, osv
from odoo import api, models, fields, _
from odoo.tools.misc import format_date
import json

import io
from odoo.tools.misc import xlsxwriter


class MailTracking(models.Model):
    _inherit = 'mail.tracking.value'

    field_groups = fields.Char(compute='_compute_field_groups')


    def _compute_field_groups(self):
        for tracking in self:
            model = self.env[tracking.mail_message_id.model]
            field = model._fields.get(tracking.field.name)
            tracking.field_groups = field.groups if field else 'base.group_user'

