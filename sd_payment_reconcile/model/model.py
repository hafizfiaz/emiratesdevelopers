# -*- coding: utf-8 -*-
from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from datetime import datetime, timedelta, date

import logging
import json
_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    _inherit = 'account.move'

    def _compute_payments_widget_to_reconcile_info(self):
        for move in self:
            move.invoice_outstanding_credits_debits_widget = json.dumps(False)
            move.invoice_has_outstanding = False

            if move.state != 'posted' \
                    or move.payment_state not in ('not_paid', 'partial') \
                    or not move.is_invoice(include_receipts=True):
                continue

            pay_term_lines = move.line_ids\
                .filtered(lambda line: line.account_id.user_type_id.type in ('receivable', 'payable'))

            domain = [
                ('account_id', 'in', pay_term_lines.account_id.ids),
                ('property_id', '=', move.property_id.id),
                ('asset_project_id', '=', move.asset_project_id.id),
                ('move_id.state', '=', 'posted'),
                ('partner_id', '=', move.commercial_partner_id.id),
                ('reconciled', '=', False),
                '|', ('amount_residual', '!=', 0.0), ('amount_residual_currency', '!=', 0.0),
            ]

            payments_widget_vals = {'outstanding': True, 'content': [], 'move_id': move.id}

            if move.is_inbound():
                domain.append(('balance', '<', 0.0))
                payments_widget_vals['title'] = _('Outstanding credits')
            else:
                domain.append(('balance', '>', 0.0))
                payments_widget_vals['title'] = _('Outstanding debits')

            for line in self.env['account.move.line'].search(domain):

                if line.currency_id == move.currency_id:
                    # Same foreign currency.
                    amount = abs(line.amount_residual_currency)
                else:
                    # Different foreign currencies.
                    amount = move.company_currency_id._convert(
                        abs(line.amount_residual),
                        move.currency_id,
                        move.company_id,
                        line.date,
                    )

                if move.currency_id.is_zero(amount):
                    continue

                payments_widget_vals['content'].append({
                    'journal_name': line.ref or line.move_id.name,
                    'amount': amount,
                    'currency': move.currency_id.symbol,
                    'id': line.id,
                    'move_id': line.move_id.id,
                    'position': move.currency_id.position,
                    'digits': [69, move.currency_id.decimal_places],
                    'payment_date': fields.Date.to_string(line.date),
                })

            if not payments_widget_vals['content']:
                continue

            move.invoice_outstanding_credits_debits_widget = json.dumps(payments_widget_vals)
            move.invoice_has_outstanding = True

    def one_recoed_reconcile(self,invoice,receipt):
        sos = invoice
        for inv in sos:
            if inv.state == 'posted':
                while inv.amount_residual > 0:
                    payment = inv.env['account.payment'].search([('id','=', receipt)])
                    to_reconcile = inv.line_ids.filtered(lambda a: a.account_id.internal_type == 'receivable' and not a.reconciled)
                    if payment:
                        lines = to_reconcile
                        # for payment, lines in zip(re[0], to_reconcile):
                        domain = [('account_internal_type', 'in', ('receivable', 'payable')),
                                  ('reconciled', '=', False)]
                        payment_lines = payment.line_ids.filtered_domain(domain)
                        if payment_lines:
                            for account in payment_lines.account_id:
                                (payment_lines + lines) \
                                    .filtered_domain(
                                    [('account_id', '=', account.id), ('reconciled', '=', False)]) \
                                    .reconcile()
                        else:
                            break
                    else:
                        break

                    # for payment, lines in zip(receipts, to_reconcile):
                    #     if payment.state != 'posted':
                    #         continue
                    #     domain = [('account_internal_type', 'in', ('receivable', 'payable')),
                    #               ('reconciled', '=', False)]
                    #     payment_lines = payment.line_ids.filtered_domain(domain)
                    #     for account in payment_lines.account_id:
                    #         (payment_lines + lines) \
                    #             .filtered_domain([('account_id', '=', account.id), ('reconciled', '=', False)]) \
                    #             .reconcile()


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    reconciled_amount = fields.Float(compute="_get_reconciled_values_from_line", store=True, string="Reconciled Amount")
    unreconciled_amount = fields.Float(compute="_get_reconciled_values_from_line", store=True, string="Unreconciled Amount")

    @api.depends('move_entry_ids','move_entry_ids.matched_debit_ids','move_entry_ids.matched_debit_ids.amount','amount')
    def _get_reconciled_values_from_line(self):
        for payment in self:
            if payment.move_entry_ids:
                for line in payment.move_entry_ids:
                    if line.credit:
                        if line.matched_debit_ids:
                            total = 0
                            for line2 in line.matched_debit_ids:
                                total+=line2.amount
                            payment.unreconciled_amount = round(payment.amount - total)
                            payment.reconciled_amount = total
                        else:
                            payment.unreconciled_amount = payment.amount
                            payment.reconciled_amount = 0


class SaleOrder(models.Model):
    _inherit = "sale.order"

    posted_receipts_reconcile = fields.Float('Posted Receipts Reconciled', compute="get_receipt_reconcile_values",
                                             store=True, tracking=True)
    paid_invoices = fields.Float('Paid Invoices')
    posted_receipts_unreconciled = fields.Float('Posted Receipts Unreconciled', compute="get_receipt_reconcile_values",
                                                store=True, tracking=True)
    unpaid_open_invoices = fields.Float('Unpaid Open Invoices')
    total_comm_sale = fields.Float("Total Commission on Sale", compute="get_comms", store=True, tracking=True)
    tot_comm_paid = fields.Float("Total Commission Paid", compute="get_comms", store=True, tracking=True)
    property_size_sqft = fields.Float("Property Size", compute="get_comms", store=True,
                                      tracking=True)
    net_sale_value = fields.Float("Net Sale Value", compute="get_comms", store=True, tracking=True)
    net_sale_value_sqft = fields.Float("Net Sale Value PSQft", compute="get_comms", store=True, tracking=True)
    comm_psqft = fields.Float("Commission PSQft", compute="get_comms", store=True, tracking=True)
    comm_paid_psqft = fields.Float("Commission Paid PSQft", compute="get_comms", store=True, tracking=True)
    investor_field_margin = fields.Float("Investor Deal Margin")

    @api.depends('investor_field_margin', 'net_commission_sp', 'price', 'property_id', 'property_id.gfa_feet')
    def get_comms(self):
        for rec in self:
            commission_tot = 0
            net_tot_sale = 0
            comm_ids = rec.env['commission.invoice'].search(
                [('state', '=', 'paid'), ('property_id', '=', rec.property_id.id),
                 ('asset_project_id', '=', rec.asset_project_id.id)])
            rec.tot_comm_paid = len(comm_ids)
            commission_tot = rec.price * (
                    rec.agent_commission_type_id.percentage_value / 100.0)
            rec.total_comm_sale = commission_tot + rec.total_commission + rec.total_commission2 + rec.total_commission3
            rec.net_sale_value = rec.property_price - rec.total_comm_sale - rec.investor_field_margin
            rec.property_size_sqft = rec.property_id.gfa_feet
            if rec.property_id.gfa_feet:
                rec.net_sale_value_sqft = rec.net_sale_value / rec.property_id.gfa_feet
            if rec.property_size_sqft:
                rec.comm_psqft = rec.total_comm_sale / rec.property_size_sqft
                rec.comm_paid_psqft = rec.tot_comm_paid / rec.property_size_sqft

    def action_spa_view_summary(self):
        for rec in self:
            ctx = dict(
                default_sale_id=rec.id,
                default_amount_untaxed=rec.amount_untaxed,
                default_amount_tax=rec.amount_tax,
                default_amount_total=rec.amount_total,
                default_amount_till_date=rec.amount_till_date,
                default_paid_installments=rec.paid_installments,
                default_paid_installments_perc=rec.paid_installments_perc,
                default_matured_pdcs_perc=rec.matured_pdcs_perc,
                default_unsecured_collections_perc=rec.unsecured_collections_perc,
                default_pending_balance=rec.pending_balance,
                default_balance_due_collection=rec.balance_due_collection,
                default_total_unsecured_collections=rec.total_unsecured_collections,
                default_installment_balance_pending=rec.installment_balance_pending,
                default_instalmnt_bls_pend_plus_admin_oqood=rec.instalmnt_bls_pend_plus_admin_oqood,
                default_pending_balance_perc=rec.pending_balance_perc,
                default_receipts_perc=rec.receipts_perc,
                default_matured_pdcs=rec.matured_pdcs,
                default_hold_pdcs=rec.hold_pdcs,
                default_deposited_pdcs=rec.deposited_pdcs,
                default_un_matured_pdcs=rec.un_matured_pdcs,
                default_bounced_pdcs=rec.bounced_pdcs,
                default_total_receipts=rec.total_receipts,
                default_total_spa_value=rec.total_spa_value,
                default_oqood_fee=rec.oqood_fee,
                default_admin_fee=rec.admin_fee,
                default_oqood_received=rec.oqood_received,
                default_admin_received=rec.admin_received,
                default_balance_due_oqood=rec.balance_due_oqood,
                default_balance_due_admin=rec.balance_due_admin,
                default_other_received=rec.other_received,
                default_balance_due_other=rec.balance_due_other,
                default_escrow=rec.escrow,
                default_escrow_perc=rec.escrow_perc,
                default_non_escrow=rec.non_escrow,
                default_non_escrow_perc=rec.non_escrow_perc,
                default_total_escrow=rec.total_escrow,
                default_total_escrow_perc=rec.total_escrow_perc,
                default_other_charges=rec.other_charges,
                default_posted_receipts_reconcile=rec.posted_receipts_reconcile,
                default_paid_invoices=rec.paid_invoices,
                default_posted_receipts_unreconciled=rec.posted_receipts_unreconciled,
                default_unpaid_open_invoices=rec.unpaid_open_invoices,
                default_total_comm_sale=rec.total_comm_sale,
                default_tot_comm_paid=rec.tot_comm_paid,
                default_property_size_sqft=rec.property_size_sqft,
                default_net_sale_value=rec.net_sale_value,
                default_net_sale_value_sqft=rec.net_sale_value_sqft,
                default_comm_psqft=rec.comm_psqft,
                default_comm_paid_psqft=rec.comm_paid_psqft,
                default_investor_field_margin=rec.investor_field_margin,

            )
            return {
                'name': _('SPA Summary View'),
                # 'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'spa.summary.view',
                'view_id': rec.env.ref('spa_customizations.view_spa_summary_view').id,
                'type': 'ir.actions.act_window',
                'context': ctx,
                'target': 'new'
            }

    @api.depends('receipt_ids', 'receipt_ids.reconciled_amount', 'receipt_ids.unreconciled_amount', 'receipt_ids.state')
    def get_receipt_reconcile_values(self):
        for rec in self:
            reconciled = 0
            unreconciled = 0
            for receipt in rec.receipt_ids:
                if receipt.state == 'posted' and receipt.partner_id.id == rec.partner_id.id:
                    reconciled += receipt.reconciled_amount
                    unreconciled += receipt.unreconciled_amount
            rec.posted_receipts_reconcile = reconciled
            rec.posted_receipts_unreconciled = unreconciled

    @api.model
    def old_reconciled_values_from_line(self):
        ap = self.env['account.payment'].search([('payment_type', '=', 'inbound')])
        for payment in ap:
            if payment.move_entry_ids:
                for line in payment.move_entry_ids:
                    if line.credit:
                        if line.matched_debit_ids:
                            total = 0
                            for line2 in line.matched_debit_ids:
                                total+=line2.amount
                            payment.unreconciled_amount = round(payment.amount - total)
                            payment.reconciled_amount = total
                        else:
                            payment.unreconciled_amount = payment.amount
                            payment.reconciled_amount = 0


# class SaleOrder(models.Model):
#     _inherit = "sale.order"
#
#     posted_receipts_reconcile = fields.Float('Posted Receipts Reconciled', compute="get_receipt_reconcile_values", store=True, tracking=True)
#     paid_invoices = fields.Float('Paid Invoices', compute="get_inv_paid_values", store=True, tracking=True)
#     posted_receipts_unreconciled = fields.Float('Posted Receipts Unreconciled', compute="get_receipt_reconcile_values", store=True, tracking=True)
#     unpaid_open_invoices = fields.Float('Unpaid Open Invoices', compute="get_inv_paid_values", store=True, tracking=True)
#
#
#     def action_spa_view_summary(self):
#         for rec in self:
#             ctx = dict(
#                 default_sale_id=rec.id,
#                 default_amount_untaxed=rec.amount_untaxed,
#                 default_amount_tax=rec.amount_tax,
#                 default_amount_total=rec.amount_total,
#                 default_amount_till_date=rec.amount_till_date,
#                 default_paid_installments=rec.paid_installments,
#                 default_paid_installments_perc=rec.paid_installments_perc,
#                 default_matured_pdcs_perc=rec.matured_pdcs_perc,
#                 default_unsecured_collections_perc=rec.unsecured_collections_perc,
#                 default_pending_balance=rec.pending_balance,
#                 default_balance_due_collection=rec.balance_due_collection,
#                 default_total_unsecured_collections=rec.total_unsecured_collections,
#                 default_installment_balance_pending=rec.installment_balance_pending,
#                 default_instalmnt_bls_pend_plus_admin_oqood=rec.instalmnt_bls_pend_plus_admin_oqood,
#                 default_pending_balance_perc=rec.pending_balance_perc,
#                 default_receipts_perc=rec.receipts_perc,
#                 default_matured_pdcs=rec.matured_pdcs,
#                 default_hold_pdcs=rec.hold_pdcs,
#                 default_deposited_pdcs=rec.deposited_pdcs,
#                 default_un_matured_pdcs=rec.un_matured_pdcs,
#                 default_bounced_pdcs=rec.bounced_pdcs,
#                 default_total_receipts=rec.total_receipts,
#                 default_total_spa_value=rec.total_spa_value,
#                 default_oqood_fee=rec.oqood_fee,
#                 default_admin_fee=rec.admin_fee,
#                 default_oqood_received=rec.oqood_received,
#                 default_admin_received=rec.admin_received,
#                 default_balance_due_oqood=rec.balance_due_oqood,
#                 default_balance_due_admin=rec.balance_due_admin,
#                 default_other_received=rec.other_received,
#                 default_balance_due_other=rec.balance_due_other,
#                 default_escrow=rec.escrow,
#                 default_escrow_perc=rec.escrow_perc,
#                 default_non_escrow=rec.non_escrow,
#                 default_non_escrow_perc=rec.non_escrow_perc,
#                 default_total_escrow=rec.total_escrow,
#                 default_total_escrow_perc=rec.total_escrow_perc,
#                 default_other_charges=rec.other_charges,
#                 default_posted_receipts_reconcile=rec.posted_receipts_reconcile,
#                 default_paid_invoices=rec.paid_invoices,
#                 default_posted_receipts_unreconciled=rec.posted_receipts_unreconciled,
#                 default_unpaid_open_invoices=rec.unpaid_open_invoices,
#             )
#             return {
#                 'name': _('SPA Summary View'),
#                 # 'view_type': 'form',
#                 'view_mode': 'form',
#                 'res_model': 'spa.summary.view',
#                 'view_id': rec.env.ref('spa_customizations.view_spa_summary_view').id,
#                 'type': 'ir.actions.act_window',
#                 'context': ctx,
#                 'target': 'new'
#             }
#
#     @api.depends('receipt_ids','receipt_ids.reconciled_amount','receipt_ids.unreconciled_amount','receipt_ids.state')
#     def get_receipt_reconcile_values(self):
#         for rec in self:
#             reconciled = 0
#             unreconciled = 0
#             for receipt in rec.receipt_ids:
#                 if receipt.state == 'posted' and receipt.partner_id.id == rec.partner_id.id:
#                     reconciled+= receipt.reconciled_amount
#                     unreconciled+= receipt.unreconciled_amount
#             rec.posted_receipts_reconcile = reconciled
#             rec.posted_receipts_unreconciled = unreconciled
#
#     @api.model
#     def old_receipt_reconcile_values(self):
#         sos = self.env['sale.order'].search([])
#         for rec in sos:
#             reconciled = 0
#             unreconciled = 0
#             for receipt in rec.receipt_ids:
#                 if receipt.state == 'posted' and receipt.partner_id.id == rec.partner_id.id:
#                     reconciled+= receipt.reconciled_amount
#                     unreconciled+= receipt.unreconciled_amount
#             rec.posted_receipts_reconcile = reconciled
#             rec.posted_receipts_unreconciled = unreconciled


    # @api.depends('all_invoice_ids','all_invoice_ids.amount_total','all_invoice_ids.state','all_invoice_ids.amount_residual')
    # def get_inv_paid_values(self):
    #     for rec in self:
    #         self.env.cr.execute('SELECT SUM (amount_residual) AS total FROM account_move WHERE partner_id = %s and property_id = %s and state = %s and payment_state in %s and move_type = %s', (rec.partner_id.id, rec.property_id.id or -1, 'posted', ('not_paid','partial'), 'out_invoice'))
    #         open_sum = self.env.cr.dictfetchone()
    #         self.env.cr.execute('SELECT SUM (amount_total-amount_residual) AS total FROM account_move WHERE partner_id = %s and property_id = %s and state = %s and payment_state in %s and move_type = %s', (rec.partner_id.id, rec.property_id.id or -1, 'posted', ('in_payment','paid','partial'), 'out_invoice'))
    #         paid_sum = self.env.cr.dictfetchone()
    #         rec.paid_invoices = paid_sum['total'] or 0
    #         rec.unpaid_open_invoices = open_sum['total'] or 0

    # # # amount_residual
    # @api.model
    # def invoice_amount_residual_cron(self):
    #     sos = self.env['account.move'].search([('id','=',5636),('state','=','posted'),('move_type','in',['in_invoice','out_invoice'])])
    #     count = 0
    #     for rec in sos:
    #         if rec.invoice_payments_widget:
    #             a = json.loads(rec.invoice_payments_widget)
    #             if a:
    #                 # a = json.loads(self.env['account.move'].search([('id', '=', 7617)]).invoice_payments_widget)
    #                 reconcile_sum = sum([s['amount'] for s in a['content']])
    #                 new_amount = rec.amount_total-reconcile_sum
    #                 rec.amount_residual = new_amount
    #                 rec.amount_residual_signed = new_amount
    #                 count+=1
    #                 print('count=========='+str(count))

    # # amount_residual
    @api.model
    def invoice_amount_residual_cron(self):
        sos = self.env['account.move'].search([('id','=',5636),('state','=','posted'),('move_type','in',['in_invoice','out_invoice'])])
        count = 0
        for rec in sos:
            if rec.invoice_payments_widget:
                a = json.loads(rec.invoice_payments_widget)
                if a:
                    # a = json.loads(self.env['account.move'].search([('id', '=', 7617)]).invoice_payments_widget)
                    reconcile_sum = sum([s['amount'] for s in a['content']])
                    new_amount = rec.amount_total-reconcile_sum
                    rec.amount_residual = new_amount
                    rec.amount_residual_signed = new_amount
                    count+=1
                    print('count=========='+str(count))
    # amount_residual

    @api.model
    def unreconcile_cron(self):
        sos = self.env['account.move'].search(
            [('state', '=', 'posted'), ('move_type', 'in', ['in_invoice', 'out_invoice'])])
        count = 0
        for rec in sos:
            print(rec)
            # res_list = [1378,1379]
            # for b in res_list:
            #     rec.one_recoed_reconcile(rec, b)
            if rec.invoice_payments_widget and rec.invoice_payments_widget != 'false':
                a = json.loads(rec.invoice_payments_widget)
                if a:
                    res_list = []
                    for l in a['content']:
                        res_list.append(l['account_payment_id'])
                    rec.line_ids.remove_move_reconcile()
                    self._cr.commit()
                    for b in res_list:
                        rec.one_recoed_reconcile(rec,b)
                    count+=1
                    print(count)

    @api.model
    def unreconcile_spa_invoices(self):
        sos = self.env['account.move'].search(
            [('id', 'in', self.all_invoice_ids.ids), ('state', '=', 'posted'), ('move_type', 'in', ['in_invoice', 'out_invoice'])])
        count = 0
        for rec in sos:
            print(rec)
            # res_list = [1378,1379]
            # for b in res_list:
            #     rec.one_recoed_reconcile(rec, b)
            if rec.invoice_payments_widget and rec.invoice_payments_widget != 'false':
                a = json.loads(rec.invoice_payments_widget)
                if a:
                    res_list = []
                    for l in a['content']:
                        res_list.append(l['account_payment_id'])
                    rec.line_ids.remove_move_reconcile()
                    self._cr.commit()
                    for b in res_list:
                        rec.one_recoed_reconcile(rec,b)
                        display_msg = """Please ignore if payment status duplication there. Its due to reconciliation fix"""
                        rec.message_post(body=display_msg)
                    count+=1
                    print(count)


            # rec.line_ids.remove_move_reconcile()

    @api.model
    def cron_inv_paid_values(self):
        sos = self.env['sale.order'].search([])
        for rec in sos:
            self.env.cr.execute('SELECT SUM (amount_residual) AS total FROM account_move WHERE partner_id = %s and property_id = %s and state = %s and payment_state in %s and move_type = %s',(rec.partner_id.id, rec.property_id.id or -1, 'posted', ('not_paid', 'partial'), 'out_invoice'))
            open_sum = self.env.cr.dictfetchone()
            self.env.cr.execute('SELECT SUM (amount_total-amount_residual) AS total FROM account_move WHERE partner_id = %s and property_id = %s and state = %s and payment_state in %s and move_type = %s',(rec.partner_id.id, rec.property_id.id or -1, 'posted', ('in_payment', 'paid', 'partial'),'out_invoice'))
            paid_sum = self.env.cr.dictfetchone()
            rec.paid_invoices = paid_sum['total'] or 0
            rec.unpaid_open_invoices = open_sum['total'] or 0

    def one_recoed_reconcile(self,invoice,receipt):
        sos = invoice
        for inv in sos:
            if inv.state == 'posted':
                while inv.amount_residual > 0:
                    receipts = inv.env['account.payment'].search([('id','=', receipt)])
                    to_reconcile = inv.line_ids.filtered(lambda a: a.account_id.internal_type == 'receivable' and not a.reconciled)
                    for payment, lines in zip(receipts, to_reconcile):
                        if payment.state != 'posted':
                            continue
                        domain = [('account_internal_type', 'in', ('receivable', 'payable')),
                                  ('reconciled', '=', False)]
                        payment_lines = payment.line_ids.filtered_domain(domain)
                        for account in payment_lines.account_id:
                            (payment_lines + lines) \
                                .filtered_domain([('account_id', '=', account.id), ('reconciled', '=', False)]) \
                                .reconcile()

    def reconcile_receipt(self):
        for so in self:
            so.unreconcile_spa_invoices()
            if so.other_charges_inv_ids:
                for inv in sorted(so.other_charges_inv_ids, key=lambda x: x.invoice_date_due):
                    if inv.state == 'posted' and inv.payment_state != 'reversed':
                        while inv.amount_residual > 0:
                            print(inv.id)
                            to_reconcile = inv.line_ids.filtered(
                                lambda a: a.account_id.internal_type == 'receivable' and not a.reconciled)
                            receipts = so.env['account.payment'].search(
                                [('partner_id', '=', inv.partner_id.id),
                                 ('spa_id', '=', so.id), ('state', '=', 'posted'), ('unreconciled_amount', '>', 0)], order="date ASC")
                            if receipts:
                                re = sorted(receipts.filtered(lambda p: p.spa_id.internal_type == 'spa'
                                                                    and p.collection_type_id.auto_reconcile),
                                        key=lambda x: x.date)
                                if re:
                                    payment = re[0]
                                    lines = to_reconcile
                                    # for payment, lines in zip(re[0], to_reconcile):
                                    domain = [('account_internal_type', 'in', ('receivable', 'payable')),
                                              ('reconciled', '=', False)]
                                    payment_lines = payment.line_ids.filtered_domain(domain)
                                    if payment_lines:
                                        for account in payment_lines.account_id:
                                            (payment_lines + lines) \
                                                .filtered_domain(
                                                [('account_id', '=', account.id), ('reconciled', '=', False)]) \
                                                .reconcile()
                                    else:
                                        break
                                else:
                                    break
                            else:
                                break
            srs = self.env['sale.rent.schedule'].search([('state', '=', 'confirm'),('sale_id','=', so.id)], order="start_date ASC")
            for rec in srs:
                if rec.invoice_ids:
                    for inv in sorted(rec.invoice_ids, key=lambda x: x.invoice_date_due):
                        if inv.state == 'posted' and inv.payment_state != 'reversed':
                            while inv.amount_residual > 0:
                                print(inv.id)
                                to_reconcile = inv.line_ids.filtered(
                                    lambda a: a.account_id.internal_type == 'receivable' and not a.reconciled)
                                receipts = so.env['account.payment'].search(
                                    [('partner_id', '=', inv.partner_id.id),
                                     ('spa_id', '=', so.id), ('state', '=', 'posted'), ('unreconciled_amount', '>', 0)],
                                    order="date ASC")
                                if receipts:
                                    re = sorted(receipts.filtered(lambda p: p.spa_id.internal_type == 'spa'
                                                                            and p.collection_type_id.auto_reconcile),
                                                key=lambda x: x.date)
                                    if re:
                                        payment = re[0]
                                        lines = to_reconcile
                                        # for payment, lines in zip(re[0], to_reconcile):
                                        domain = [('account_internal_type', 'in', ('receivable', 'payable')),
                                                  ('reconciled', '=', False)]
                                        payment_lines = payment.line_ids.filtered_domain(domain)
                                        if payment_lines:
                                            for account in payment_lines.account_id:
                                                (payment_lines + lines) \
                                                    .filtered_domain(
                                                    [('account_id', '=', account.id), ('reconciled', '=', False)]) \
                                                    .reconcile()
                                        else:
                                            break
                                    else:
                                        break
                                else:
                                    break

    @api.model
    def reconcile_receipt_auto(self):
        june_30 = date(2019, 6, 30)
        sos = self.env['sale.order'].search([])
        for so in sos:
            so.unreconcile_spa_invoices()
            if so.other_charges_inv_ids:
                for inv in sorted(so.other_charges_inv_ids, key=lambda x: x.invoice_date_due):
                    if inv.state == 'posted' and inv.payment_state != 'reversed':
                        while inv.amount_residual > 0:
                            print(inv.id)
                            to_reconcile = inv.line_ids.filtered(
                                lambda a: a.account_id.internal_type == 'receivable' and not a.reconciled)
                            receipts = so.env['account.payment'].search(
                                [('partner_id', '=', inv.partner_id.id),
                                 ('spa_id', '=', so.id), ('state', '=', 'posted'), ('unreconciled_amount', '>', 0)],
                                order="date ASC")
                            if receipts:
                                re = sorted(receipts.filtered(lambda p: p.spa_id.internal_type == 'spa'
                                                                        and p.collection_type_id.auto_reconcile
                                                                        and p.date > june_30),
                                            key=lambda x: x.date)
                                if re:
                                    payment = re[0]
                                    lines = to_reconcile
                                    # for payment, lines in zip(re[0], to_reconcile):
                                    domain = [('account_internal_type', 'in', ('receivable', 'payable')),
                                              ('reconciled', '=', False)]
                                    payment_lines = payment.line_ids.filtered_domain(domain)
                                    if payment_lines:
                                        for account in payment_lines.account_id:
                                            (payment_lines + lines) \
                                                .filtered_domain(
                                                [('account_id', '=', account.id), ('reconciled', '=', False)]) \
                                                .reconcile()
                                    else:
                                        break
                                else:
                                    break
                            else:
                                break
            srs = self.env['sale.rent.schedule'].search([('state', '=', 'confirm'),('sale_id','=', so.id)], order="start_date ASC")
            for rec in srs:
                if rec.invoice_ids:
                    for inv in sorted(rec.invoice_ids, key=lambda x: x.invoice_date_due):
                        if inv.state == 'posted' and inv.payment_state != 'reversed':
                            while inv.amount_residual > 0:
                                print(inv.id)
                                to_reconcile = inv.line_ids.filtered(
                                    lambda a: a.account_id.internal_type == 'receivable' and not a.reconciled)
                                receipts = so.env['account.payment'].search(
                                    [('partner_id', '=', inv.partner_id.id),
                                     ('spa_id', '=', so.id), ('state', '=', 'posted'), ('unreconciled_amount', '>', 0)],
                                    order="date ASC")
                                if receipts:
                                    re = sorted(receipts.filtered(lambda p: p.spa_id.internal_type == 'spa'
                                                                            and p.collection_type_id.auto_reconcile
                                                                            and p.date > june_30),
                                                key=lambda x: x.date)
                                    if re:
                                        payment = re[0]
                                        lines = to_reconcile
                                        # for payment, lines in zip(re[0], to_reconcile):
                                        domain = [('account_internal_type', 'in', ('receivable', 'payable')),
                                                  ('reconciled', '=', False)]
                                        payment_lines = payment.line_ids.filtered_domain(domain)
                                        if payment_lines:
                                            for account in payment_lines.account_id:
                                                (payment_lines + lines) \
                                                    .filtered_domain(
                                                    [('account_id', '=', account.id), ('reconciled', '=', False)]) \
                                                    .reconcile()
                                        else:
                                            break
                                    else:
                                        break
                                else:
                                    break



class SPASummaryView(models.TransientModel):
    _inherit = 'spa.summary.view'

    posted_receipts_reconcile = fields.Float('Posted Receipts Reconciled', readonly=True)
    paid_invoices = fields.Float('Paid Invoices', readonly=True)
    posted_receipts_unreconciled = fields.Float('Posted Receipts Unreconciled', readonly=True)
    unpaid_open_invoices = fields.Float('Unpaid Open Invoices', readonly=True)
    investor_field_margin = fields.Float("Investor Deal Margin")
    total_comm_sale = fields.Float("Total Commission on Sale", readonly=True)
    tot_comm_paid = fields.Float("Total Commission Paid", readonly=True)
    property_size_sqft = fields.Float("Property Size", readonly=True)
    net_sale_value = fields.Float("Net Sale Value", readonly=True)
    comm_psqft = fields.Float("Commission PSQft", readonly=True)
    comm_paid_psqft = fields.Float("Commission Paid PSQft", readonly=True)
    net_sale_value_sqft = fields.Float("Net Sale Value PSQft", readonly=True)
