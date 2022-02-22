# -*- coding: utf-8 -*-

from odoo import api, models
import pandas as pd
from datetime import datetime, date


class CashflowReport(models.AbstractModel):
    _name = 'report.cashflow_report.cashflow_report'

    def get_result(self, project, start_date, end_date):
        if project:
            projects = self.env['account.asset.asset'].search([('project', '=', True),('id','=',project.ids)])
        else:
            projects = self.env['account.asset.asset'].search([('project', '=', True)])

        data = {}
        data['collections'] = []
        data['regular_collections'] = []
        data['overdue_collections'] = []
        dates = pd.date_range(start_date, end_date, freq='M')
        count = len(dates)

        for rec in dates:
            if rec == dates[0]:
                schedules = self.env['sale.rent.schedule'].search([('start_date','>=',start_date),('start_date','<=',rec),('property_id.parent_id','in',projects.ids)])
                schedules_overdue = self.env['sale.rent.schedule'].search([('start_date','<',start_date),('property_id.parent_id','in',projects.ids)])

                total_pen = 0
                total_overdue = 0
                for line in schedules:
                    total_pen += line.amount - line.receipt_total
                for line in schedules_overdue:
                    total_overdue += line.pen_amt

                data['collections'].append(rec.strftime("%B")+" "+str(rec.year))
                data['regular_collections'].append(total_pen)
                data['overdue_collections'].append(total_overdue)
            elif rec == dates[count-1]:
                schedules = self.env['sale.rent.schedule'].search(
                    [('start_date', '>=', end_date.replace(day=1)), ('start_date', '<=', end_date),('property_id.parent_id','in',projects.ids)])
                schedules_overdue = self.env['sale.rent.schedule'].search(
                    [('start_date', '<', end_date.replace(day=1)), ('property_id.parent_id', 'in', projects.ids)])
                total_pen = 0
                total_overdue = 0
                for line in schedules:
                    total_pen += line.amount - line.receipt_total
                for line in schedules_overdue:
                    total_overdue += line.pen_amt
                data['collections'].append(rec.strftime("%B") + " " + str(rec.year))
                data['regular_collections'].append(total_pen)
                data['overdue_collections'].append(total_overdue)
            else:
                schedules = self.env['sale.rent.schedule'].search(
                    [('start_date', '>=', rec.replace(day=1)), ('start_date', '<=', rec),('property_id.parent_id','in',projects.ids)])

                schedules_overdue = self.env['sale.rent.schedule'].search(
                    [('start_date', '<', rec.replace(day=1)), ('property_id.parent_id', 'in', projects.ids)])
                total_pen = 0
                total_overdue = 0
                for line in schedules:
                    total_pen += line.amount - line.receipt_total
                for line in schedules_overdue:
                    total_overdue += line.pen_amt
                data['collections'].append(rec.strftime("%B") + " " + str(rec.year))
                data['regular_collections'].append(total_pen)
                data['overdue_collections'].append(total_overdue)
        return data


