# -*- coding: utf-8 -*-

from odoo import api, models
import pandas as pd
from datetime import datetime, date


class SalesExpenseReport(models.AbstractModel):
    _name = 'report.pdc_movement.sales_expense_report'

    def get_result(self):
        data = {}
        projects = self.env['account.asset.asset'].search([('project','=',True)])
        project_list = []
        current_year = date.today().year
        start_year = 2017
        year_dict = {}
        year_list = []
        while current_year > start_year:
            year_dict[start_year+1] = []
            year_list.append(start_year+1)
            start_date = date(start_year, 7, 1)
            end_date = date(start_year+1, 6, 30)
            year_dict[start_year+1].append(start_date)
            year_dict[start_year+1].append(end_date)
            start_year += 1


        start_year = 2018
        year_dict_new = {}
        year_list_new = []
        while current_year > start_year:
            year_dict_new[start_year+1] = []
            year_list_new.append(start_year+1)
            start_date = date(start_year, 7, 1)
            end_date = date(start_year+1, 6, 30)
            year_dict_new[start_year+1].append(start_date)
            year_dict_new[start_year+1].append(end_date)
            start_year += 1
        for year in year_list_new:
            data[year] = {'salaries': 0,'other':0}
            date_start = year_dict[year][0]
            date_end = year_dict[year][1]
            move_lines = self.env['account.move.line'].search([('date','>=',date_start),('date','<=',date_end),('move_id.state', 'in', ['posted']),('account_id.code','=','4403A102')])
            total_move = 0
            for move in move_lines:
                total_move += move.balance
            data[year]['salaries'] = total_move
            move_others = self.env['account.move.line'].search([('date','>=',date_start),('date','<=',date_end),('move_id.state', 'in', ['posted'])])
            total_other = 0
            for move in move_others:
                if move.account_id.code[:4] == '4403' and move.account_id.code not in ['4403A102','4403K102','4403K104','4403K105']:
                    total_other += move.balance
            data[year]['other'] = total_other
        for project in projects:
            data[project.name] = {
                'land_cost': 0,
                'cost_of_construction': 0,
                'consult_other_cost': 0,
                'commission': 0,
                'fgr': 0,
            }

            project_list.append(project.name)
            data[project.name] = {}
            commissions = self.env['commission.invoice'].search(
                [('asset_project_id', '=', project.id), ('state', 'not in', ['cancel', 'rejected'])])
            total_commission = 0
            for rec in commissions:
                total_commission += rec.amount_total
            data[project.name]['commission'] = total_commission
            fgr_payments = self.env['fgr.payment.request'].search(
                [('asset_project_id', '=', project.id), ('state', 'in', ['in_process', 'approved'])])
            total_fgr = 0
            for rec in fgr_payments:
                total_fgr += rec.fgr_total_payment
            data[project.name]['fgr'] = total_fgr
            for year in year_list:
                date_start = year_dict[year][0]
                date_end = year_dict[year][1]
                schedules = self.env['sale.order'].search([('booking_date','>=',date_start),('booking_date','<=',date_end),('property_id.parent_id','=',project.id),('state','not in',['cancel','refund_cancellation']),('internal_type','=','spa')])
                amount = 0
                for rec in schedules:
                    amount += rec.amount_total
                data[project.name][year] = amount
            costing = self.env['project.costing'].search([('project', '=', project.id)], limit=1)
            if costing:
                data[project.name]['land_cost'] = costing.land_cost
                data[project.name]['cost_of_construction'] = costing.total_contract_value
                data[project.name]['consult_other_cost'] = costing.consultancy_cost + costing.other_cost
                data[project.name]['cop_div_cos'] = data[project.name]['land_cost'] + data[project.name][
                    'cost_of_construction'] + data[project.name]['consult_other_cost']
            else:
                data[project.name]['land_cost'] = 0
                data[project.name]['cost_of_construction'] = 0
                data[project.name]['consult_other_cost'] = 0
                data[project.name]['cop_div_cos'] = data[project.name]['land_cost'] + data[project.name][
                    'cost_of_construction'] + data[project.name]['consult_other_cost']
            for year in year_list:
                data[project.name][str(year)+'project'] = {'land_cost': 0,'construction':0, 'consultancy':0,'commission':0,'fgr': 0}
                date_start = year_dict[year][0]
                date_end = year_dict[year][1]
                if project.name == 'Samana Greens':
                    tags = self.env['account.account.tag'].search([('name','=', 'Land Cost- Samana Greens')])
                elif project.name == 'Samana Hills':
                    tags = self.env['account.account.tag'].search([('name','=', 'Land Cost- Hills')])
                elif project.name == 'Samana Golf Avenue':
                    tags = self.env['account.account.tag'].search([('name','=', 'Land Cost- Golf')])
                elif project.name == 'Samana Waves':
                    tags = self.env['account.account.tag'].search([('name','=', 'Land Cost- Waves')])
                elif project.name == 'Samana Park Views':
                    tags = self.env['account.account.tag'].search([('name','=', 'Land Cost- Park View')])
                accounts = []
                if tags:
                    accounts = self.env['account.account'].search([('tag_ids','in', tags.ids)])

                cost_moves = self.env['account.move.line'].search(
                    [('date', '>=', date_start), ('date', '<=', date_end), ('move_id.state', 'in', ['posted']), ('account_id','in',accounts.ids)])
                total_cost_moves = 0
                for move in cost_moves:
                    total_cost_moves += move.balance
                data[project.name][str(year)+'project']['land_cost'] = total_cost_moves



                if project.name == 'Samana Greens':
                    tags = self.env['account.account.tag'].search([('name','=', 'Project Cost- Greens')])
                elif project.name == 'Samana Hills':
                    tags = self.env['account.account.tag'].search([('name','=', 'Project Cost- Hills')])
                elif project.name == 'Samana Golf Avenue':
                    tags = self.env['account.account.tag'].search([('name','=', 'Project Cost- Golf')])
                elif project.name == 'Samana Waves':
                    tags = self.env['account.account.tag'].search([('name','=', 'Project Cost- Waves')])
                elif project.name == 'Samana Park Views':
                    tags = self.env['account.account.tag'].search([('name','=', 'Project Cost- Park Views')])
                accounts = []
                if tags:
                    accounts = self.env['account.account'].search([('tag_ids', 'in', tags.ids)])

                cost_moves = self.env['account.move.line'].search(
                    [('date', '>=', date_start), ('date', '<=', date_end), ('move_id.state', 'in', ['posted']),
                     ('account_id', 'in', accounts.ids)])
                total_cost_moves = 0
                for move in cost_moves:
                    total_cost_moves += move.balance
                data[project.name][str(year)+'project']['construction'] = total_cost_moves



                if project.name == 'Samana Greens':
                    tags = self.env['account.account.tag'].search([('name','in', ['Consultancy Cost- Greens','Other Project Cost- Greens'])])
                elif project.name == 'Samana Hills':
                    tags = self.env['account.account.tag'].search([('name','=', 'Consultancy Cost- Hills')])
                elif project.name == 'Samana Golf Avenue':
                    tags = self.env['account.account.tag'].search([('name','=', 'Consultancy Cost- Golf')])
                elif project.name == 'Samana Waves':
                    tags = self.env['account.account.tag'].search([('name','=', 'Consultancy Cost- Waves')])
                elif project.name == 'Samana Park Views':
                    tags = self.env['account.account.tag'].search([('name','in', ['Consultancy Cost- Park Views','Other Project Cost- Park View'])])
                accounts = []
                if tags:
                    accounts = self.env['account.account'].search([('tag_ids', 'in', tags.ids)])

                cost_moves = self.env['account.move.line'].search(
                    [('date', '>=', date_start), ('date', '<=', date_end), ('move_id.state', 'in', ['posted']),
                     ('account_id', 'in', accounts.ids)])
                total_cost_moves = 0
                for move in cost_moves:
                    total_cost_moves += move.balance
                data[project.name][str(year)+'project']['consultancy'] = total_cost_moves
                commissions = self.env['commission.invoice'].search(
                    [('date', '>=', date_start), ('date', '<=', date_end),
                     ('asset_project_id', '=', project.id), ('state', 'in', ['paid', 'invoiced'])])
                total_cost_moves = 0
                for move in commissions:
                    total_cost_moves += move.amount_total
                data[project.name][str(year)+'project']['commission'] = total_cost_moves

                commissions = self.env['fgr.details'].search(
                    [('Due_date', '>=', date_start), ('Due_date', '<=', date_end),
                     ('asset_project_id', '=', project.id), ('state', 'in', ['confirm'])])
                total_cost_moves = 0
                for move in commissions:
                    total_cost_moves += move.amount
                data[project.name][str(year)+'project']['fgr'] = total_cost_moves

        return data, project_list, year_list, year_list_new


