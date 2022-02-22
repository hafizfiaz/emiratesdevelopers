from datetime import datetime
from odoo import models, fields, api, _


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    unit_type = fields.Many2one('unit.type', 'Unit Type', related='property_id.unit_type_id', store=True, tracking=True)
    down_payment_amnt = fields.Float("Down Payment", compute='down_pmnt_amnt', tracking=True, store=True)
    down_payment_perct = fields.Float("Down Payment Percentage", compute='down_pmnt_amnt', tracking=True, store=True)
    future_installments = fields.Float('Future Installments', compute="future_instlmnts", tracking=True, store=True)
    handover_dates = fields.Date(string="Handover Date", related='asset_project_id.handover_date', store=True,
                                 tracking=True)
    installment_till_handover = fields.Float('Installment Till Handover', compute="future_instlmnts", tracking=True, store=True)
    installment_after_handover = fields.Float('Installment After Handover', compute="future_instlmnts", tracking=True, store=True)

    @api.depends('sale_payment_schedule_ids', 'sale_payment_schedule_ids.start_date',
                 'sale_payment_schedule_ids.amount')
    def future_instlmnts(self):
        for rec in self:
            if rec.sale_payment_schedule_ids:
                total = 0.00
                totals = 0.00
                totals1 = 0.00
                for recss in rec.sale_payment_schedule_ids:
                    d1 = datetime.now().date()
                    if recss.start_date >= d1:
                        total += recss.amount
                    if rec.handover_dates:
                        if recss.start_date <= rec.handover_dates:
                            totals += recss.amount
                        if recss.start_date >= rec.handover_dates:
                            totals1 += recss.amount
                rec.future_installments = total
                rec.installment_till_handover = totals
                rec.installment_after_handover = totals1

    @api.depends('sale_payment_schedule_ids','sale_payment_schedule_ids.amount','sale_payment_schedule_ids.value')
    def down_pmnt_amnt(self):
        for rec in self:
            if rec.sale_payment_schedule_ids:
                rec.down_payment_amnt = rec.sale_payment_schedule_ids[0].amount
                rec.down_payment_perct = rec.sale_payment_schedule_ids[0].value

    @api.model
    def get_down_amnt_perc(self):
        sos = self.env['sale.order'].search([])
        for rec in sos:
            if rec.sale_payment_schedule_ids:
                rec.down_payment_amnt = rec.sale_payment_schedule_ids[0].amount
                rec.down_payment_perct = rec.sale_payment_schedule_ids[0].value

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
                default_future_installments=rec.future_installments,
                default_handover_dates=rec.handover_dates,
                default_installment_till_handover=rec.installment_till_handover,
                default_installment_after_handover=rec.installment_after_handover,

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

    commission_type_id4 = fields.Many2one('commission.type', string='Type')
    agent4 = fields.Many2one(
        comodel_name='res.partner', string='Agent4')
    commission4 = fields.Boolean(
        '4th Commission')
    total_commission4 = fields.Float(string="Total Commission")
    commission_type_id5 = fields.Many2one('commission.type', string='Type')
    agent5 = fields.Many2one(
        comodel_name='res.partner', string='Agent5')
    commission5 = fields.Boolean(
        '5th Commission')
    total_commission5 = fields.Float(string="Total Commission")


class SPASummaryView(models.TransientModel):
    _inherit = 'spa.summary.view'

    future_installments = fields.Float('Future Installments', tracking=True, readonly=True)
    handover_dates = fields.Date(string="Handover Date", tracking=True, readonly=True)
    installment_till_handover = fields.Float('Installment Till Handover', tracking=True, readonly=True)
    installment_after_handover = fields.Float('Installment After Handover', tracking=True, readonly=True)