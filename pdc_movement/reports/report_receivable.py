# -*- coding: utf-8 -*-

from odoo import api, models
import pandas as pd
from datetime import datetime, date


class ReceivableSummaryReport(models.AbstractModel):
    _name = 'report.pdc_movement.receivable_summary_report'

    def get_result(self):
        data = {}
        projects = self.env['account.asset.asset'].search([('project','=',True)])
        project_list = []
        for project in projects:
            project_list.append(project.name)
            data[project.name] = {}

            sales = self.env['sale.order'].search([('internal_type', '=', 'spa'), ('asset_project_id','=', project.id),('state','not in',['cancel','refund_cancellation'])])
            sale_value = 0.0
            realized_receipts = 0.0
            for sale in sales:
                sale_value += sale.amount_total
                for receipt in sale.receipt_ids:
                    if receipt.state in ['posted','paid_unposted'] and receipt.payment_type == 'inbound':
                        realized_receipts += receipt.nets_amount
            data[project.name]['Sales Value'] = sale_value
            data[project.name]['Realized Receipts Net of Oqood'] = realized_receipts

            schedules = self.env['sale.rent.schedule'].search([('property_id.parent_id','=', project.id),('state','in',['confirm']),('start_date','<=',project.handover_date)])
            schedules_due = self.env['sale.rent.schedule'].search([('property_id.parent_id','=', project.id),('state','in',['confirm']),('start_date','<=',datetime.today().date())])
            till_handover = 0.0
            for schedule in schedules:
                till_handover += schedule.amount - schedule.receipt_total
            data[project.name]['Receivable Till Handover'] = till_handover
            amount_till_date = 0.0
            for schedule in schedules_due:
                amount_till_date += schedule.amount
            data[project.name]['Balance Due As of Now'] = amount_till_date
            schedules = self.env['sale.rent.schedule'].search([('property_id.parent_id','=', project.id),('state','in',['confirm']),('start_date','>',project.handover_date)])
            till_handover = 0.0
            for schedule in schedules:
                till_handover += schedule.amount - schedule.receipt_total
            data[project.name]['Post Handover Receivables'] = till_handover
            data[project.name]['Handover Date'] = project.handover_date
        return data, project_list


