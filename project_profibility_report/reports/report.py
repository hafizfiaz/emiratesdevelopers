# -*- coding: utf-8 -*-

from odoo import api, models
import pandas as pd
from datetime import datetime, date


class ProfitabilityReport(models.AbstractModel):
    _name = 'report.project_profibility_report.profitability_report'

    def get_result(self):
        # if project:
        #     projects = self.env['account.asset.asset'].search([('project', '=', True),('id','=',project.ids)])
        # else:
        data = {}
        projects = self.env['account.asset.asset'].search([('project', '=', True)])

        for proj in projects:
            data[proj.name] = {
                'sold_inv': 0,
                'sale_psft': 0,
                'sale_area_psft': 0,

                'unsold_inv': 0,
                'unsold_psft': 0,
                'unsold_area_psft': 0,

                'sold_unsold_inv': 0,
                'sold_unsold_psft': 0,
                'sold_unsold_area_psft': 0,

                'cop_div_cos': 0,
                'cop_div_cos_apl': 0,
                'cop_div_sft': 0,

                'gross_profit': 0,

                'gross_profit_sft': 0,
                'gross_profit_noc': 0,

                'commissions': 0,
                'commissions_sft': 0,
                'comm_perc': 0,

                'fgr_sft': 0,
                'fgr_perc': 0,
                'gross_profit_no_fgr': 0,

                'gross_profit_no_fgr_com': 0,
                'gross_profit_no_fgr_com_perc': 0,

                'land_cost': 0,
                'cost_of_construction': 0,
                'consult_other_cost': 0,
                'land_cost_apl': 0,
                'cost_of_construction_apl': 0,
                'consult_other_cost_apl': 0
            }
            for spa in self.env['sale.order'].search([('asset_project_id', '=', proj.id), ('internal_type', '=', 'spa')
                                                         , ('state', 'not in', ['refund_cancellation', 'cancel'])]):
                data[proj.name]['sold_inv'] += spa.amount_total
                data[proj.name]['sale_area_psft'] += spa.property_id.gfa_feet
            if data[proj.name]['sold_inv'] and data[proj.name]['sale_area_psft']:
                data[proj.name]['sale_psft'] = data[proj.name]['sold_inv'] / data[proj.name]['sale_area_psft']

            for prop in self.env['account.asset.asset'].search([('parent_id', '=', proj.id), ('state', '=', 'draft')]):
                data[proj.name]['unsold_inv'] += prop.value
                data[proj.name]['unsold_area_psft'] += prop.gfa_feet
            if data[proj.name]['unsold_inv'] and data[proj.name]['unsold_area_psft']:
                data[proj.name]['unsold_psft'] = data[proj.name]['unsold_inv'] / data[proj.name]['unsold_area_psft']

            data[proj.name]['sold_unsold_inv'] = data[proj.name]['sold_inv'] + data[proj.name]['unsold_inv']
            data[proj.name]['sold_unsold_psft'] = data[proj.name]['sale_psft'] + data[proj.name]['unsold_psft']
            data[proj.name]['sold_unsold_area_psft'] = data[proj.name]['sale_area_psft'] + data[proj.name]['unsold_area_psft']

            commissions = self.env['commission.invoice'].search(
                [('asset_project_id', '=', proj.id), ('state', 'not in', ['cancel', 'rejected'])])
            total_commission = 0
            for rec in commissions:
                total_commission += rec.amount_total
            data[proj.name]['commissions'] = total_commission
            data[proj.name]['commissions_sft'] = data[proj.name]['commissions'] / (data[proj.name]['sale_area_psft'] or 1)
            # data[proj.name]['sale_net_of_commissions'] = data[proj.name]['sale_psft'] - data[proj.name]['commissions_sft']
            data[proj.name]['comm_perc'] = (data[proj.name]['commissions_sft'] / (data[proj.name]['sale_psft']  or 1)) * 100

            costing = self.env['project.costing'].search([('project','=',proj.id)], limit=1)
            if costing:
                data[proj.name]['land_cost'] = costing.land_cost
                data[proj.name]['cost_of_construction'] = costing.total_contract_value
                data[proj.name]['consult_other_cost'] = costing.consultancy_cost + costing.other_cost
                data[proj.name]['cop_div_cos'] = data[proj.name]['land_cost'] + data[proj.name]['cost_of_construction'] + data[proj.name]['consult_other_cost']
                data[proj.name]['land_cost_apl'] = costing.land_cost_ap_ledger
                data[proj.name]['cost_of_construction_apl'] = costing.contract_value_ap_ledger
                data[proj.name]['consult_other_cost_apl'] = costing.consultancy_cost_ap_ledger + costing.other_cost_ap_ledger
                data[proj.name]['cop_div_cos_apl'] = data[proj.name]['land_cost_apl'] + data[proj.name]['cost_of_construction_apl'] + data[proj.name]['consult_other_cost_apl']
            else:
                data[proj.name]['land_cost'] = 0
                data[proj.name]['cost_of_construction'] = 0
                data[proj.name]['consult_other_cost'] = 0
                data[proj.name]['cop_div_cos'] = data[proj.name]['land_cost'] + data[proj.name]['cost_of_construction'] + data[proj.name]['consult_other_cost']
                data[proj.name]['land_cost_apl'] = 0
                data[proj.name]['cost_of_construction_apl'] = 0
                data[proj.name]['consult_other_cost_apl'] = 0
                data[proj.name]['cop_div_cos_apl'] = data[proj.name]['land_cost_apl'] + data[proj.name]['cost_of_construction_apl'] + data[proj.name]['consult_other_cost_apl']

            gross = data[proj.name]['sold_inv'] - data[proj.name]['cop_div_cos']
            data[proj.name]['gross_profit'] = gross
            gross_profit_perc = round((gross / (data[proj.name]['sold_inv'] or 1)) * 100)
            data[proj.name]['gross_profit_sft'] = round((gross / (data[proj.name]['sale_area_psft'] or 1)))
            data[proj.name]['gross_profit_noc'] = data[proj.name]['gross_profit_sft'] - data[proj.name]['commissions_sft']
            data[proj.name]['gross_profit_sft_noc_perc'] = (data[proj.name]['gross_profit_sft'] / (data[proj.name]['sale_psft']  or 1)) * 100

            fgr_payments = self.env['fgr.payment.request'].search(
                [('asset_project_id', '=', proj.id), ('state', 'in', ['in_process', 'approved'])])
            total_fgr = 0
            for rec in fgr_payments:
                total_fgr += rec.fgr_total_payment
            data[proj.name]['fgr_sft'] = total_fgr / (data[proj.name]['sale_area_psft'] or 1)
            data[proj.name]['fgr_perc'] = (data[proj.name]['fgr_sft'] / (data[proj.name]['sale_psft'] or 1)) * 100
            data[proj.name]['gross_profit_no_fgr'] = data[proj.name]['gross_profit_sft'] - data[proj.name]['fgr_sft']

            data[proj.name]['gross_profit_no_fgr_com'] = data[proj.name]['gross_profit_sft'] - data[proj.name]['commissions_sft'] - data[proj.name]['fgr_sft']
            data[proj.name]['gross_profit_no_fgr_com_perc'] = (data[proj.name]['gross_profit_no_fgr_com'] / (data[proj.name]['sale_psft'] or 1)) * 100

        return data

    def get_results(self):
        # if project:
        #     projects = self.env['account.asset.asset'].search([('project', '=', True),('id','=',project.ids)])
        # else:
        data = {}
        projects = self.env['account.asset.asset'].search([('project', '=', True)])

        for proj in projects:
            data[proj.name] = {
                'sold_inv': 0,
                'sale_psft': 0,
                'sale_area_psft': 0,

                'unsold_inv': 0,
                'unsold_psft': 0,
                'unsold_area_psft': 0,

                'sold_unsold_inv': 0,
                'sold_unsold_psft': 0,
                'sold_unsold_area_psft': 0,

                'sale_net_of_commissions': 0,
                'commissions_sft': 0,
                'commissions': 0,

                'cop_div_cos': 0,
                'cop_div_sft': 0,

                'gross_profit': 0,
                'gross_profit_perc': 0,


                'cop_sold': 0,
                'cop_unsold': 0,
                'cop_sold_unsold': 0,

                'land_cost': 0,
                'cost_of_construction': 0,
                'consult_other_cost': 0,

            }
            for spa in self.env['sale.order'].search([('asset_project_id','=',proj.id),('internal_type','=','spa')
                                                         ,('state','not in',['refund_cancellation','cancel'])]):
                data[proj.name]['sold_inv'] += spa.amount_total
                data[proj.name]['sale_psft'] += spa.property_id.gfa_feet
                # for line in spa.commission_ids:
                #     if line.state not in ['cancel','rejected']:
                #         data[proj.name]['commissions'] += line.amount_total
            commissions = self.env['commission.invoice'].search(
                [('asset_project_id', '=', proj.id), ('state', 'not in', ['cancel', 'rejected'])])
            total_commission = 0
            for rec in commissions:
                total_commission += rec.amount_total
            data[proj.name]['commissions'] = total_commission
            if data[proj.name]['sold_inv'] and data[proj.name]['sale_psft']:
                data[proj.name]['sale_area_psft'] = data[proj.name]['sold_inv'] / data[proj.name]['sale_psft']

            data[proj.name]['commissions_sft'] = data[proj.name]['commissions'] / (data[proj.name]['sale_psft'] or 1)
            data[proj.name]['sale_net_of_commissions'] = data[proj.name]['sale_area_psft'] - data[proj.name]['commissions_sft']

            costing = self.env['project.costing'].search([('project','=',proj.id)], limit=1)
            if costing:
                data[proj.name]['land_cost'] = costing.land_cost
                data[proj.name]['cost_of_construction'] = costing.total_contract_value
                data[proj.name]['consult_other_cost'] = costing.consultancy_cost + costing.other_cost
                data[proj.name]['cop_div_cos'] = data[proj.name]['land_cost'] + data[proj.name]['cost_of_construction'] + data[proj.name]['consult_other_cost']
            else:
                data[proj.name]['land_cost'] = 0
                data[proj.name]['cost_of_construction'] = 0
                data[proj.name]['consult_other_cost'] = 0
                data[proj.name]['cop_div_cos'] = data[proj.name]['land_cost'] + data[proj.name]['cost_of_construction'] + data[proj.name]['consult_other_cost']

            for prop in self.env['account.asset.asset'].search([('parent_id', '=', proj.id), ('state', '=', 'draft')]):
                data[proj.name]['unsold_inv'] += prop.value
                data[proj.name]['unsold_psft'] += prop.gfa_feet
            if data[proj.name]['unsold_inv'] and data[proj.name]['unsold_psft']:
                data[proj.name]['unsold_area_psft'] = data[proj.name]['unsold_inv'] / data[proj.name]['unsold_psft']

            data[proj.name]['sold_unsold_inv'] = data[proj.name]['sold_inv'] + data[proj.name]['unsold_inv']
            data[proj.name]['sold_unsold_psft'] = data[proj.name]['sale_psft'] + data[proj.name]['unsold_psft']
            data[proj.name]['sold_unsold_area_psft'] = data[proj.name]['sale_area_psft'] + data[proj.name]['unsold_area_psft']



            data[proj.name]['cop_sold'] = data[proj.name]['cop_div_cos']/(data[proj.name]['sale_psft'] or 1)
            data[proj.name]['cop_unsold'] = data[proj.name]['cop_div_cos']/(data[proj.name]['unsold_psft'] or 1)
            data[proj.name]['cop_sold_unsold'] = data[proj.name]['cop_div_cos'] / (data[proj.name]['sold_unsold_psft'] or 1)

            data[proj.name]['gross_profit'] = data[proj.name]['sale_area_psft'] - data[proj.name]['cop_sold']
            data[proj.name]['gross_profit_perc'] = data[proj.name]['gross_profit']/ (data[proj.name]['sale_area_psft'] or 1) *100
        return data


