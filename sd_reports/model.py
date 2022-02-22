import odoo.exceptions
from odoo import _, api, models
from odoo.exceptions import UserError, ValidationError, except_orm
import time


class ReservationForm(models.AbstractModel):
    _name = 'report.sd_sale_order_report.reservation_form'

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['sale.order'].search([('id', 'in', docids)])
        display_msg = """The Reservation Print Report is printed by """ + self.env.user.name + ""
        docs.message_post(body=display_msg)
        return {
            'doc_ids': docids,
            'doc_model': 'sale.order',
            'docs': docs,
        }


class HandoverReport(models.AbstractModel):
    _name = 'report.sd_handover_report.handover_report'

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['sale.order'].search([('id', 'in', docids)])
        display_msg = """The Handover Report Print Report is printed by """ + self.env.user.name + ""
        docs.message_post(body=display_msg)
        return {
            'doc_ids': docids,
            'doc_model': 'sale.order',
            'docs': docs,
        }


class ClosureForm(models.AbstractModel):
    _name = 'report.sd_sale_order_report.report_closure_form_template'

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['sale.order'].search([('id', 'in', docids)])
        display_msg = """The Closure Form Report is printed by """ + self.env.user.name + ""
        docs.message_post(body=display_msg)
        return {
            'doc_ids': docids,
            'doc_model': 'sale.order',
            'docs': docs,
        }


class PaymentReceiptsReport(models.AbstractModel):
    _name = 'report.account.report_payment_receipt'

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['account.payment'].search([('id', 'in', docids)])
        flag = self.env['res.users'].has_group('account.group_account_user')
        if not flag:
            if docs.state not in ['approved','collected','posted']:
                raise UserError(_('You are not allowed to perform this action'))
        display_msg = """The Payment Receipts Report is printed by """ + self.env.user.name + ""
        docs.message_post(body=display_msg)
        return {
            'doc_ids': docids,
            'doc_model': 'account.payment',
            'docs': docs,
        }


class ReceiptCustomerCopy(models.AbstractModel):
    _name = 'report.sd_receipts_report.report_receipt_customer_copy'

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['account.payment'].search([('id', 'in', docids)])
        flag = self.env['res.users'].has_group('account.group_account_user')
        if not flag:
            if docs.state not in ['approved','collected','posted']:
                raise UserError(_('You are not allowed to perform this action'))
        display_msg = """The Receipt Customer Copy Report is printed by """ + self.env.user.name + ""
        docs.message_post(body=display_msg)
        return {
            'doc_ids': docids,
            'doc_model': 'account.payment',
            'docs': docs,
        }


class PDCAcknowledgment(models.AbstractModel):
    _name = 'report.sd_receipts_report.report_remaining_cheques_template'

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['account.payment'].search([('id', 'in', docids)])
        flag = self.env['res.users'].has_group('account.group_account_user')
        if not flag:
            if docs.state not in ['approved','collected','posted']:
                raise UserError(_('You are not allowed to perform this action'))
        display_msg = """The PDC Acknowledgment Report is printed by """ + self.env.user.name + ""
        docs.message_post(body=display_msg)
        return {
            'doc_ids': docids,
            'doc_model': 'account.payment',
            'docs': docs,
        }


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def print_report_saleorder_english(self):
        data = {}
        data['english'] = True
        display_msg = """The SPA Report is printed by """ + self.env.user.name + ""
        self.message_post(body=display_msg)
        return self.env.ref('spa_customizations.report_sale_form').report_action(self, data=data)

    def print_report_golf(self):
        data = {}
        display_msg = """The
        SPA Report is printed by """ + self.env.user.name + ""
        self.message_post(body=display_msg)
        return self.env.ref('spa_customizations.report_golf_form').report_action(self, data=data)


class CustomerStatement(models.AbstractModel):
    _name = 'report.sd_sale_order_report.report_sale_penalty_template'

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['sale.order'].search([('id', 'in', docids)])
        display_msg = """The Customer Statement with Penalty Report is printed by """ + self.env.user.name + ""
        docs.message_post(body=display_msg)
        return {
            'doc_ids': docids,
            'doc_model': 'sale.order',
            'docs': docs,
        }


class AgentEoi(models.AbstractModel):
    _name = 'report.sd_sale_order_report.report_agent_expression_of_interest'

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['sale.order'].search([('id', 'in', docids)])
        display_msg = """The Agent Expression of Interest Report is printed by """ + self.env.user.name + ""
        docs.message_post(body=display_msg)
        return {
            'doc_ids': docids,
            'doc_model': 'sale.order',
            'docs': docs,
        }


class CustomerStatementWithPenalty(models.AbstractModel):
    _name = 'report.sd_sale_order_report.report_expression_of_interest'

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['sale.order'].search([('id', 'in', docids)])
        display_msg = """The Expression of Interest Report is printed by """ + self.env.user.name + ""
        docs.message_post(body=display_msg)
        return {
            'doc_ids': docids,
            'doc_model': 'sale.order',
            'docs': docs,
        }