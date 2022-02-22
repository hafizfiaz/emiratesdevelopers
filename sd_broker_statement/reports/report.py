# -*- coding: utf-8 -*-
import time
from odoo import api, fields, models, _
from dateutil.parser import parse
from odoo.exceptions import UserError
from odoo.tools.translate import _


class BrokerStatementPrint(models.AbstractModel):
    _name = 'report.sd_broker_statement.report_broker_statement'
    _description = 'Get broker statement PDF.'

    def get_state_values(self, status):
        state = ''
        if status:
            if status == 'draft':
                state = 'Created'
            elif status == 'under_discount_approval':
                state = 'Under Approval'
            elif status == 'tentative_booking':
                state = 'Tentative Booking'
            elif status == 'review':
                state = 'Under Review'
            elif status == 'confirm_spa':
                state = 'Confirmed for SPA'
            elif status == 'approved':
                state = 'Approved'
            elif status == 'rejected':
                state = 'Rejected'
            elif status == 'cancel':
                state = 'Cancel'
        return state

    @api.model
    def _get_report_values(self, docids, data=None):
        data = data if data is not None else {}
        total_comm_invoiced = 0
        total_comm_paid = 0
        total_comm_bls = 0
        fifteen_perc = 0
        fifteen_oqood_admin = 0
        fifteen_received = 0
        fifteen_diff = 0
        oqood_charged = 0
        oqood_paid = 0
        admin_charged = 0
        admin_paid = 0
        booking_ids=[-1]
        commissions = []
        payments_ids = []
        partner = False
        # if data['active_model'] == 'crm.booking':
        #     booking_ids = data['active_ids']
        #     if not booking_ids[0].agent_id:
        #         raise UserError(_("No agent commission selected"))
        self = self.sudo()
        if data['active_model'] == 'res.partner':
            partner = self.env['res.partner'].search([('id', 'in', data['active_ids'])])
            bokings = self.env['sale.order'].search([('state', 'not in', ['cancel','rejected']),
                                                      '|','|','|',('agent_id', 'in', data['active_ids']),
                                                      ('agent', 'in', data['active_ids']),
                                                      ('agent2', 'in', data['active_ids']),
                                                      ('agent3', 'in', data['active_ids'])])
            booking_ids = bokings.ids
            commissions = self.env['commission.invoice'].search(
                [('agent', '=', data['active_ids']), ('state', '!=', 'cancel')])
            if not booking_ids:
                raise UserError(_("No result found against this agent"))

        if data['active_model'] == 'commission.invoice':
            com = self.env['commission.invoice'].search([('id', 'in', data['active_ids'])])
            partner = self.env['res.partner'].search([('id', '=', com[0].agent.id)])
            bokings = self.env['sale.order'].search([('state', 'not in', ['cancel','rejected']),
                                                      '|', '|', '|', ('agent_id', '=', com[0].agent.id),
                                                      ('agent', '=', com[0].agent.id),
                                                      ('agent2', '=', com[0].agent.id),
                                                      ('agent3', '=', com[0].agent.id)])
            booking_ids = bokings.ids
            commissions = self.env['commission.invoice'].search(
                [('agent', '=', com.agent.id), ('state', '!=', 'cancel')])

            if not booking_ids:
                raise UserError(_("No result found against this agent"))
        # commissions =  self.env['commission.invoice'].search([('agent', '=', booking.agent_id.id),('state', '!=', 'cancel')])

        cb = self.env['sale.order'].search([('id','in',  booking_ids)])
        sales_and_commission_res = []
        eligibility = []
        properties = []
        for cms1 in sorted(commissions, key=lambda x: x.asset_project_id.id):
            if cms1.property_id.id not in properties:
                properties.append(cms1.property_id.id)
        vals1 = ['project', 'property', 'oqood_charge', 'oqood_paid', 'admin_charge', 'admin_paid',
                 'fifteen_oqood_admin', 'amount_realized', 'collection']
        payments_ids = self.env['account.payment'].search([('state', '=', 'posted'),('visible_on_broker_statement', '=', True), ('partner_id', '=', partner.id)])

        for p in properties:
            res1 = dict((fn, 0.0) for fn in vals1)
            for cms in commissions.filtered(lambda a: a.property_id.id == p):
                res1['project'] = cms.asset_project_id.name
                res1['property'] = cms.property_id.name
                # if cms.invc_id:
                #     payments = cms.env['account.payment'].search([('invoice_ids', 'in', cms.invc_id.ids)])
                #     if payments:
                #         payments_ids = payments_ids + payments.ids
                total_comm_invoiced += cms.invoiced_amount
                total_comm_paid += cms.total_commission_paid
                total_comm_bls += cms.balance_commission

                # fifteen_perc += cms.fifteen_perc_of_price
                res1['fifteen_oqood_admin'] = cms.fifteen_perc_amount
                res1['amount_realized'] = cms.matured_pdcs
                res1['collection'] = cms.related_booking_id.total_receipts
                # fifteen_diff += cms.diffrence2
                if cms.related_booking_id.other_charges_inv_ids:
                    for oinvs in cms.related_booking_id.other_charges_inv_ids:
                        for ol in oinvs.invoice_line_ids:
                            if 'oqood' in ol.account_id.name.lower():
                                res1['oqood_charge'] = oinvs.amount_total
                                res1['oqood_paid'] = oinvs.amount_total - oinvs.amount_residual
                            if 'admin' in ol.account_id.name.lower():
                                res1['admin_charge'] = oinvs.amount_total
                                res1['admin_paid'] = oinvs.amount_total - oinvs.amount_residual
                else:
                    res1['oqood_charge'] = cms.related_booking_id.oqood_fee
                    res1['oqood_paid'] = cms.related_booking_id.oqood_received
                    res1['admin_charge'] = cms.related_booking_id.admin_fee
                    res1['admin_paid'] = cms.related_booking_id.admin_received
            eligibility.append(res1)

        for booking in cb:
            if booking.id == 358:
                print('thissss')
            comms = self.env['commission.invoice'].search([('related_booking_id', '=', booking.id),('state', '!=', 'cancel'),('agent', '=', partner.id)])
            # if comms:
            #     commissions = comms
            vals = ['booking_date','unit','unit_type','project','customer', 'total_spa', 'total_collection',
                    'total_realized','collections_perc','comm_invc',
                    'commission_type', 'discount_from_comm', 'total_comm','comm_paid','bls_com','booking_status']
            res = dict((fn, 0.0) for fn in vals)
            res['customer'] = booking.partner_id.name or ''
            res['unit'] = booking.property_id.name or ''
            res['unit_type'] = booking.property_id.unit_type_id.name or ''
            res['project'] = booking.asset_project_id.name or ''
            res['booking_date'] = booking.booking_date.strftime('%d-%m-%Y') or ''
            commission_type = False
            if booking.agent_id.id == partner.id:
                commission_type = booking.agent_commission_type_id.name
            if booking.agent.id == partner.id:
                commission_type = booking.commission_type_id.name
            if booking.agent2.id == partner.id:
                commission_type = booking.commission_type_id2.name
            if booking.agent3.id == partner.id:
                commission_type = booking.commission_type_id3.name
            res['commission_type'] = commission_type or ''
            res['discount_from_comm'] = booking.agent_discount_perc or ''
            res['booking_status'] = self.get_state_values(booking.state) or ''
            if booking:
                res['total_spa'] = round(booking.total_spa_value,2)
                res['total_realized'] = round(booking.matured_pdcs,2)
                res['total_collection'] = round(booking.total_receipts,2)
                res['collections_perc'] = round(booking.receipts_perc,2)
            if comms:
                for cm in comms:
                    res['total_comm'] += round(cm.total_commission_amount,2)
                    res['comm_invc'] = round(comms[0].invoiced_amount,2)
                    res['comm_paid'] += round(cm.total_commission_paid,2)
                    res['bls_com'] += round(cm.balance_commission,2)
            sales_and_commission_res.append(res)


        return {
            'doc_ids': data.get('ids', docids),
            'doc_model': 'broker.statement.report',
            'docs': cb,
            'result': sales_and_commission_res,
            'commissions': commissions,
            'total_invoiced': total_comm_invoiced,
            'total_paid': total_comm_paid,
            'total_balance': total_comm_bls,
            'fifteen_perc': fifteen_perc,
            'fifteen_oqood_admin': fifteen_oqood_admin,
            'fifteen_received': fifteen_received,
            'fifteen_diff': fifteen_diff,
            'oqood_charged': oqood_charged,
            'eligibility': eligibility,
            'oqood_paid': oqood_paid,
            'admin_charged': admin_charged,
            'admin_paid': admin_paid,
            'partner': partner,
            'payments': payments_ids,
            'data': dict(
                data
            ),
        }

class CommissionInvoice(models.Model):
    _inherit = "commission.invoice"

    invoice_reference = fields.Char('Invoice Reference', compute='compute_related_inv_pay', store=True)

    # @api.depends('invc_id','invc_id.amount_total', 'invc_id.residual', 'invc_id.reference')
    # def compute_related_inv_pay(self):
    #     for rec in self:
    #         if rec.invc_id:
    #             payments = rec.env['account.payment'].search([('invoice_ids', 'in', rec.invc_id.ids)])
    #             rec.invoiced_amount = rec.invc_id.amount_total
    #             rec.invoice_reference = rec.invc_id.reference
    #             rec.related_invoices_ids = [(6,0, rec.invc_id.ids)]
    #             rec.related_payments_ids = [(6,0, payments.ids)]

    @api.depends('invc_id','invc_id.amount_total', 'invc_id.amount_residual')
    def compute_related_inv_pay(self):
        for rec in self:
            if rec.invc_id:
                payments = rec.env['account.payment'].search([('reconciled_invoice_ids', 'in', rec.invc_id.ids)])
                rec.invoiced_amount = rec.invc_id.amount_total
                rec.total_commission_paid = rec.invc_id.amount_total - rec.invc_id.amount_residual
                rec.invoice_reference = rec.invc_id.ref
                rec.related_invoices_ids = [(6,0, rec.invc_id.ids)]
                rec.related_payments_ids = [(6,0, payments.ids)]

    @api.model
    def old_inv_pay(self):
        comm = self.env['commission.invoice'].search([])
        for rec in comm:
            if rec.invc_id:
                payments = rec.env['account.payment'].search([('reconciled_invoice_ids', 'in', rec.invc_id.ids)])
                rec.invoiced_amount = rec.invc_id.amount_total
                rec.total_commission_paid = rec.invc_id.amount_total - rec.invc_id.amount_residual
                rec.invoice_reference = rec.invc_id.ref
                rec.related_invoices_ids = [(6, 0, rec.invc_id.ids)]
                rec.related_payments_ids = [(6, 0, payments.ids)]
            rec.balance_commission = rec.total_commission_amount - rec.total_commission_paid
