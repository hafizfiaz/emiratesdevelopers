# -*- coding: utf-8 -*-

from odoo import api, models
import pandas as pd
from datetime import datetime, date


class ProfitLossReport(models.AbstractModel):
    _name = 'report.pdc_movement.profit_loss_report'

    def get_result(self):
        data = {}
        projects = self.env['account.asset.asset'].search([('project','=',True)])
        project_list = []
        for project in projects:
            project_list.append(project.name)
            data[project.name] = {}

            sales = self.env['sale.order'].search([('internal_type', '=', 'spa'), ('asset_project_id','=', project.id),('state','not in',['cancel','refund_cancellation'])])
            revenue = 0.0
            for sale in sales:
                revenue += sale.amount_total
            data[project.name]['Revenue'] = revenue

            project_costing = self.env['project.costing'].search([('project', '=', project.id)])
            project_cost = 0.0
            for rec in project_costing:
                project_cost += rec.total_project_cost
            data[project.name]['Project Costing'] = project_cost
            # data[project.name]['Realized Receipts Net of Oqood'] = realized_receipts
            # data[project.name]['Balance Due As of Now'] = amount_till_date
            #
            # schedules = self.env['sale.rent.schedule'].search([('property_id.parent_id','=', project.id),('state','in',['confirm']),('start_date','<=',project.handover_date)])
            # till_handover = 0.0
            # for schedule in schedules:
            #     till_handover += schedule.amount - schedule.receipt_total
            # data[project.name]['Receivable Till Handover'] = till_handover
            #
            # schedules = self.env['sale.rent.schedule'].search([('property_id.parent_id','=', project.id),('state','in',['confirm']),('start_date','>',project.handover_date)])
            # till_handover = 0.0
            # for schedule in schedules:
            #     till_handover += schedule.amount - schedule.receipt_total
            # data[project.name]['Post Handover Receivables'] = till_handover
            # data[project.name]['Handover Date'] = project.handover_date
        return data, project_list


