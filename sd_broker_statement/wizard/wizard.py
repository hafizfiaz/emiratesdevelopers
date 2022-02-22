# -*- coding: utf-8 -*-
from odoo import _, api, fields, models
import json
import datetime
import io
from odoo.tools import date_utils
try:
    from odoo.tools.misc import xlsxwriter
except ImportError:
    import xlsxwriter


class BrokerStatement(models.Model):
    _name = 'broker.statement.report'
    _description = 'Broker Statement Report'

    name = fields.Char('Name')

    def print_broker_statement(self):
        data = {}
        if self.env.context.get('active_model'):
            data.update({'active_model':self.env.context['active_model'],'active_ids':self.env.context['active_ids']})
        else:
            data.update({'active_model':'res.partner','active_ids':self.env.user.partner_id.ids})

        return self.env.ref('sd_broker_statement.action_broker_statement').report_action(self, data=data)
# class BrokerStatement(models.TransientModel):
#     _name = "broker.statement.reports"
#     _description = "Broker Statement Reports"
#
#     name = fields.Char('Name')
#
#     def check_report(self):
#         context = self._context
#         context.update({'wiz':1})
#         data = {}
#         data['form'] = self.read(['name'])[0]
#         return self._print_report(data)
#
#     def _print_report(self, data):
#         data['form'].update(self.read(['name'])[0])
#         return self.env.ref('partner_schedule_report.partner_schedule_fgr').report_action(self, data=data)
#
#


class CommissionInvoice(models.Model):
    _inherit = "commission.invoice"

    state = fields.Selection(
        [('draft', 'Draft'),
         ('under_legal_review', 'Under Legal Review'),
         ('under_manager_review', 'Under Manager Review'),
         ('under_sales_hod_review', 'Under Sales HOD Review'),
         ('under_verification', 'Under Accounts Verification'),
         ('under_fc_authorization', 'Under Fin Manager Review'),
         ('under_cfo_authorization', 'Under FC Authorization'),
         ('under_approval', 'Under Approval'),
         ('approved', 'Approved'),
         ('rejected', 'Rejected'),
         ('cancel', 'Cancel'),
         ('invoice', 'Invoiced'),
         ('paid', 'Paid')
         ], 'State', readonly=True,
        default='draft', track_visibility="onchange")

# class CommissionInvoiceReport(models.Model):
#     _inherit = "commission.invoice.report"
#
#     state = fields.Selection(
#         [('draft', 'Draft'),
#          ('under_legal_review', 'Under Legal Review'),
#          ('under_manager_review', 'Under Manager Review'),
#          ('under_sales_hod_review', 'Under Sales HOD Review'),
#          ('under_verification', 'Under Accounts Verification'),
#          ('under_fc_authorization', 'Under Fin Manager Review'),
#          ('under_cfo_authorization', 'Under FC Authorization'),
#          ('under_approval', 'Under Approval'),
#          ('approved', 'Approved'),
#          ('rejected', 'Rejected'),
#          ('cancel', 'Cancel'),
#          ('invoice', 'Invoiced'),
#          ('paid', 'Paid')
#          ], 'State')
#
