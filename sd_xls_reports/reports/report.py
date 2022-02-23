# -*- coding: utf-8 -*-

from odoo import api, models
import pandas as pd
from datetime import datetime, timedelta, date


class BuildingMIS(models.AbstractModel):
    _name = 'report.sd_xls_reports.building_mis'

    def get_result(self):
        # if project:
        #     projects = self.env['account.asset.asset'].search([('project', '=', True),('id','=',project.ids)])
        # else:
        data = {}
        projects = self.env['account.asset.asset'].search([('project', '=', True)])
        june_30 = date(2019, 6, 30)
        current_date = datetime.now().date()
        for proj in projects:
            data[proj.name] = {
                'sales_value': 0,
                'realized_net_of_o_a': 0,
                'total_future_receivable': 0,
                'overdue_payment': 0,
                'receivable_till_handover': 0,
                'accumulated_receivables': 0,
                'post_handover': 0,
                'handover_date': 0,

                'contract_value_exc_vat': 0,
                'savings': 0,
                'net_cost_exc_vat': 0,
                'retention_amount_perc': 0,
                'retention': 0,
                'vat_perc': 00,
                'net_payable_inc_vat': 0,
                'paid_value': 0,
                'remaining_payable': 0,
                'bank_bls': 0,
                'escrow_account': 0,
                'sub_construction': 0,
                'cash_surplus_deficit': 0,
                'retention_acc': 0,
            }
            data[proj.name]['handover_date'] = proj.handover_date
            realized_receipts = 0.0
            amount_till_date = 0.0
            for spa in self.env['sale.order'].search([('asset_project_id', '=', proj.id), ('internal_type', '=', 'spa')
                                                         , ('state', 'not in', ['refund_cancellation', 'cancel'])]):
                data[proj.name]['sales_value'] += spa.amount_total
                data[proj.name]['realized_net_of_o_a'] += spa.paid_installments
                amount_till_date += spa.amount_till_date
                # for receipt in spa.receipt_ids:
                #     if receipt.state in ['posted','paid_unposted'] and receipt.payment_type == 'inbound':
                #         realized_receipts += receipt.nets_amount
            if proj.handover_date and proj.handover_date > current_date:
                data[proj.name]['overdue_payment'] = amount_till_date - data[proj.name]['realized_net_of_o_a']

            # print(proj.name)
            # print("amount_till_date")
            # print(amount_till_date)
            # print("data[proj.name]['realized_net_of_o_a']")
            # print(data[proj.name]['realized_net_of_o_a'])
            # print("data[proj.name]['overdue_payment']")
            # print(data[proj.name]['overdue_payment'])

            installment_till_handover = 0
            installment_after_handover = 0
            for srs in self.env['sale.rent.schedule'].search(
                    [('asset_property_id', '=', proj.id), ('state', '=', 'confirm')]):
                if srs.start_date <= proj.handover_date:
                    installment_till_handover += srs.amount
                if srs.start_date > proj.handover_date:
                    installment_after_handover += srs.amount
            # print("installment_till_handover")
            # print(installment_till_handover)
            if proj.handover_date and proj.handover_date > current_date:
                data[proj.name]['receivable_till_handover'] = installment_till_handover - data[proj.name]['realized_net_of_o_a'] - data[proj.name]['overdue_payment']
            if proj.handover_date and proj.handover_date > current_date:
                data[proj.name]['accumulated_receivables'] = data[proj.name]['overdue_payment'] + data[proj.name]['receivable_till_handover']
            if proj.handover_date and proj.handover_date > current_date:
                data[proj.name]['post_handover'] = installment_after_handover
            else:
                data[proj.name]['post_handover'] = data[proj.name]['sales_value'] - data[proj.name]['realized_net_of_o_a']
            data[proj.name]['total_future_receivable'] = data[proj.name]['post_handover'] + data[proj.name][
                'accumulated_receivables']

            costing = self.env['project.costing'].search([('project', '=', proj.id)], limit=1)
            if costing:
                data[proj.name]['contract_value_exc_vat'] = costing.total_contract_value
                data[proj.name]['savings'] = costing.savings
                data[proj.name]['net_cost_exc_vat'] = costing.net_cost_exc_vat
                data[proj.name]['retention_amount_perc'] = costing.retention_amount_perc
                data[proj.name]['retention'] = costing.net_cost_exc_vat * (costing.retention_amount_perc/100)
                data[proj.name]['vat_perc'] = costing.vat_perc
                data[proj.name]['net_payable_inc_vat'] = (costing.net_cost_exc_vat - data[proj.name]['retention']) \
                                                         + (costing.net_cost_exc_vat - data[proj.name]['retention'])\
                                                         * ((costing.vat_perc/100) or 1)
                data[proj.name]['paid_value'] = costing.total_payments
                data[proj.name]['remaining_payable'] = data[proj.name]['net_payable_inc_vat'] - costing.total_payments
            escrow_tag = ''
            sub_con_tag = ''
            retention_tag = ''
            if proj.name == 'Samana Golf Avenue':
                escrow_tag = 'Escrow- Golf'
                sub_con_tag = 'Sub Construction- Golf'
                retention_tag = 'Retention- Golf'
            if proj.name == 'Samana Greens':
                escrow_tag = 'Escrow- Greens'
                sub_con_tag = 'Sub Construction- Greens'
                retention_tag = 'Retention- Greens'
            if proj.name == 'Samana Hills':
                escrow_tag = 'Escrow- Hills'
                sub_con_tag = 'Sub Construction- Hills'
                retention_tag = 'Retention- Hills'
            if proj.name == 'Samana Waves':
                escrow_tag = 'Escrow- Waves'
                sub_con_tag = 'Sub Construction- Waves'
                retention_tag = 'Retention- Waves'
            if proj.name == 'Samana Park Views':
                escrow_tag = 'Escrow- Park Views'
                sub_con_tag = 'Sub Construction-Park Views'
                retention_tag = 'Retention- Park Views'
            esc_tags = self.env['account.account.tag'].search([('name', '=', escrow_tag)], limit=1)
            sub_con_tags = self.env['account.account.tag'].search([('name', '=', sub_con_tag)], limit=1)
            retention_tags = self.env['account.account.tag'].search([('name', '=', retention_tag)], limit=1)
            escrow_sum = 0
            retention_sum = 0
            sub_con_sum = 0
            aml = self.env['account.move.line'].search([('parent_state', '=', 'posted'), ('date', '>', june_30)])
            if esc_tags:
                escrow_sum = sum(aml.filtered(lambda m: esc_tags.id in m.account_id.tag_ids.ids).mapped("balance"))
            if retention_tags:
                retention_sum = sum(aml.filtered(lambda m: retention_tags.id in m.account_id.tag_ids.ids).mapped("balance"))
            if sub_con_tags:
                sub_con_sum = sum(aml.filtered(lambda m: sub_con_tags.id in m.account_id.tag_ids.ids).mapped("balance"))

            data[proj.name]['bank_bls'] = escrow_sum + sub_con_sum
            data[proj.name]['escrow_account'] = escrow_sum
            data[proj.name]['sub_construction'] = sub_con_sum
            data[proj.name]['retention_acc'] = retention_sum
            data[proj.name]['cash_surplus_deficit'] = data[proj.name]['bank_bls'] - data[proj.name]['remaining_payable']

        return data
