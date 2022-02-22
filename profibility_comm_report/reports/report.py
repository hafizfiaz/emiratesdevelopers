# -*- coding: utf-8 -*-

from odoo import api, models
import pandas as pd
from datetime import datetime, date


class ProfitabilityCommReport(models.AbstractModel):
    _name = 'report.profibility_comm_report.profitability_comm_report'

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
                for line in spa.commission_ids:
                    if line.state not in ['cancel','rejected']:
                        data[proj.name]['commissions'] += line.amount_total
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


