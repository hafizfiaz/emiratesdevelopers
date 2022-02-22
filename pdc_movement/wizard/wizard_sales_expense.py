# -*- coding: utf-8 -*-
from odoo import _, api, fields, models
import json
import datetime
import io
from odoo.tools import date_utils
try:
    from odoo.tools.misc import xlsxwriter
except ImportError:
    import xlsxwriter


class SalesExpenseWizard(models.TransientModel):
    _name = "sales.expense.wizard"

    # project_id = fields.Many2one('account.asset.asset', string="Project", domain="[('project', '=', True)]")
    # start_date = fields.Date(string='Start Date', required=True)
    # end_date = fields.Date(string='End Date', required=True)

    def _get_report_name(self):
        return _('Sales Vs Operational Expenses Report')

    def get_report_filename(self, options):
        """The name that will be used for the file when downloading pdf,xlsx,..."""
        return self._get_report_name().lower().replace(' ', '_')

    def check_report(self):
        context = self._context
        self.ensure_one()
        data = {}
        data['form'] = self.read()[0]
        data['form']['xls'] = context.get('xls_export')
        return {
            'type': 'ir_actions_account_report_download',
            'data': {'model': 'sales.expense.wizard',
                     'options': json.dumps(data, default=date_utils.json_default),
                     'output_format': 'xlsx',
                     'report_name': 'Sales Vs Operational Expenses Report',
                     }
        }
        # else:
        #     data = {}
        #     data['form'] = self.read(['start_date','end_date'])[0]
        #     return self._print_report(data)

    # def _print_report(self, data):
    #     data['form'].update(self.read(['type','start_date','end_date','property_exc_ids','project_exc_ids','property_ids','nationality_ids','nationality_exc_ids','tag_ids','tag_exc_ids','receivable_ids','receivable_exc_ids','project_ids','partner_ids','period_length','sort_by','sale_type'])[0])
    #     return self.env.ref('sale_rent_schedule_reports.action_report_srs_periods').report_action(self, data=data)


    def get_xlsx(self, options, response=None):
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        data = {}
        vals = self.search([('id', '=', options['form']['id'])])
        data['form'] = vals.read([])[0]
        data['model'] = 'ir.ui.menu'
        data['ids'] = []
        env_obj = vals.env['report.pdc_movement.sales_expense_report']
        result, project_list, year_list, year_list_new = env_obj.get_result()
        sheet = workbook.add_worksheet()
        format1 = workbook.add_format({'font_size': 18, 'align': 'center', 'bg_color': '#d0cece', 'bold': True, 'text_wrap': True})
        format1.set_font_color('#660033')
        format2 = workbook.add_format({'font_size': 10, 'align': 'center', 'bg_color': '#d0cece', 'bold': True, 'text_wrap': True})
        format2.set_font_color('#660033')
        format3 = workbook.add_format({'font_size': 14, 'align': 'left', 'bg_color': '#660033', 'bold': True, 'text_wrap': True})
        format3.set_font_color('#FFFF')
        format4 = workbook.add_format({'font_size': 10, 'align': 'center', 'bg_color': '#deebf7', 'bold': True, 'text_wrap': True})
        format4.set_font_color('#000000')
        format5 = workbook.add_format({'font_size': 12, 'align': 'left', 'bg_color': '#d0cece', 'text_wrap': True})
        format5.set_font_color('#000000')
        format6 = workbook.add_format({'font_size': 12, 'align': 'left', 'bold': True, 'text_wrap': True})
        format6.set_font_color('#000000')
        format7 = workbook.add_format({'font_size': 10,'num_format': '#,###', 'align': 'right', 'text_wrap': True})
        format7.set_font_color('#000000')
        format_total_blue = workbook.add_format({'font_size': 10,'num_format': '#,###', 'align': 'right','bold':True, 'text_wrap': True})
        format_total_blue.set_font_color('#000000')
        format8 = workbook.add_format({'font_size': 10,'num_format': '#,###','bold': True, 'align': 'right', 'text_wrap': True})
        format8.set_font_color('#000000')
        grey_black = workbook.add_format(
            {'font_size': 10, 'align': 'left', 'bg_color': '#ADA8A7', 'bold': False, 'text_wrap': True})
        grey_mehroon = workbook.add_format(
            {'font_size': 10, 'align': 'left', 'bg_color': '#cfccce', 'bold': True, 'text_wrap': True})
        grey_blue = workbook.add_format(
            {'font_size': 10, 'align': 'left', 'bg_color': '#b7dee8', 'bold': True, 'text_wrap': True})
        grey_mehroon.set_font_color('#6d0035')
        grey_blue.set_font_color('#6d0035')
        format9 = workbook.add_format({'font_size': 10, 'align': 'right', 'text_wrap': True, 'num_format': '#,###'})

        format_main2 = workbook.add_format({'font_size': 10, 'align': 'center','bg_color': '#CFCCCE', 'bold': True, 'text_wrap': True})

        format_main2.set_font_color('#6D0035')
        format_main2.set_border()
        second_mainl = workbook.add_format({'font_size': 14, 'align': 'left', 'bg_color': '#6D0035', 'bold': True, 'text_wrap': True})
        second_mainl.set_font_color('#FFFFFF')

        format1bsn = workbook.add_format({'font_size': 10, 'align': 'right', 'text_wrap': True,'num_format': '#,###'})
        format1bsn.set_top()
        format1bsn.set_bottom()
        format2.set_border(2)
        format4.set_border(2)
        format8.set_top(2)
        format8.set_bottom(2)
        format_total_blue.set_top(2)
        format_total_blue.set_bottom(2)

        sheet.set_column('B:B', 50)
        sheet.set_column('D:I', 12)
        sheet.set_row(1, 20)
        sheet.set_row(18, 27)

        sheet.merge_range(1, 1, 1, 4, "Sales Vs Operational Expenses", format1)
        sheet.merge_range('D4:I4', "July 01 to June 30", format2)
        sheet.merge_range('D6:I6', "AED", format4)
        row = 4
        col = 3
        for data in year_list:
            sheet.write(row, col, data, format2)
            col +=1

        sheet.write(row, col, 'Total', format2)
        row += 1
        col = 1
        sheet.write(row, col, 'Sales', format3)
        row += 2
        year_total_dict = {}
        for data in year_list:
            year_total_dict[data] = 0
        grand_total = 0
        for project in project_list:
            col = 1
            sheet.write(row, col, project, format5)
            col = 3
            total_amount = 0
            for data in year_list:
                year_total_dict[data] += result[project][data]
                if result[project][data] == 0:
                    amount = '-'
                else:
                    amount = result[project][data]
                    total_amount += result[project][data]
                sheet.write(row, col, amount, format7)
                col += 1
            sheet.write(row, col, total_amount, format7)
            grand_total += total_amount
            row += 2
        col = 1
        sheet.write(row, col, "Total", format6)
        col = 3
        for data in year_list:
            sheet.write(row, col, year_total_dict[data], format8)
            col += 1
        sheet.write(row, col, grand_total, format8)
        col = 1

        # ============================COST OF Product Main===================================
        row+=3
        sheet.write(row, 1, 'Cost of Product (Upon 100% Completion)', second_mainl)
        a = 3
        for p1 in project_list:
            sheet.write(row, a, p1, format_main2)
            a += 1
        sheet.write(row, a, 'Total', format_main2)
        row+=2
        # ===================Land cost======================

        sheet.write(row, 1, 'Land Cost', grey_black)
        a = 3
        line_total = 0
        for p in project_list:
            sheet.write(row, a, result[p]['land_cost'], format9)
            line_total += result[p]['land_cost']
            a += 1
        sheet.write(row, a, line_total, format9)

        # ===================Cost of Construction======================
        row+=2
        sheet.write(row, 1, 'Cost of Construction', grey_black)
        a = 3
        line_total = 0
        for p in project_list:
            sheet.write(row, a, result[p]['cost_of_construction'], format9)
            line_total += result[p]['cost_of_construction']
            a += 1
        sheet.write(row, a, line_total, format9)

        # ===================Consultancy Other costs======================
        row+=2
        sheet.write(row, 1, 'Consultancy+Other Costs', grey_black)
        a = 3
        line_total = 0
        for p in project_list:
            sheet.write(row, a, result[p]['consult_other_cost'], format9)
            line_total += result[p]['consult_other_cost']
            a += 1
        sheet.write(row, a, line_total, format9)

        # ===================COst totals======================
        row+=2
        # sheet.write(33, 0, 'Consultancy+Other Costs', grey_black)
        a = 3
        line_total = 0
        for p in project_list:
            sheet.write(row, a, result[p]['cop_div_cos'], format8)
            line_total += result[p]['cop_div_cos']
            a += 1
        sheet.write(row, a, line_total, format8)
        row += 2
        sheet.write(row, 1, 'Commission Expenses', grey_black)
        col = 3
        total_commission = 0
        for project in project_list:
            sheet.write(row, col, result[project]['commission'], format7)
            total_commission += result[project]['commission']
            col += 1
        sheet.write(row, col, total_commission, format7)
        row += 2
        sheet.write(row, 1, 'FGR Expenses', grey_black)
        col = 3
        total_fgr = 0
        for project in project_list:
            sheet.write(row, col, result[project]['fgr'], format7)
            total_fgr += result[project]['fgr']
            col += 1
        sheet.write(row, col, total_fgr, format7)
        row += 4
        col = 3
        sheet.merge_range('D34:I34', "July 01 to June 30", format2)
        for data in year_list:
            sheet.write(row, col, data, format2)
            col +=1
        sheet.write(row, col, 'Total', format2)
        col = 1
        sheet.write(row-1, col, 'Cost of Product (Incurred Till Date)', format3)
        row +=2
        for project in project_list:
            sheet.write(row, 1, project, grey_mehroon)
            sheet.write(row+1, 1, 'Land Cost', grey_blue)
            sheet.write(row+2, 1, 'Cost of Construction', grey_blue)
            sheet.write(row+3, 1, 'Consultancy & Others', grey_blue)
            sheet.write(row+4, 1, 'Total', grey_blue)
            sheet.write(row+6, 1, 'Commissions', grey_blue)
            sheet.write(row+7, 1, 'FGR Payments', grey_blue)
            col =3
            total_land_cost = 0
            total_construction = 0
            total_consultancy = 0
            total_commission = 0
            total_fgr = 0
            total = 0
            for year in year_list:
                sheet.write(row+1, col, result[project][str(year)+'project']['land_cost'], format7)
                sheet.write(row+2, col, result[project][str(year)+'project']['construction'], format7)
                sheet.write(row+3, col, result[project][str(year)+'project']['consultancy'], format7)
                sheet.write(row+4, col, result[project][str(year)+'project']['consultancy']+result[project][str(year)+'project']['land_cost'], format_total_blue)
                sheet.write(row+6, col, result[project][str(year)+'project']['commission'], format7)
                sheet.write(row+7, col, result[project][str(year)+'project']['fgr'], format7)
                total_land_cost += result[project][str(year)+'project']['land_cost']
                total_construction += result[project][str(year)+'project']['construction']
                total_consultancy += result[project][str(year)+'project']['consultancy']
                total_commission += result[project][str(year)+'project']['commission']
                total_fgr += result[project][str(year)+'project']['fgr']
                col += 1

            sheet.write(row + 1, col, total_land_cost, format7)
            sheet.write(row+2, col, total_construction, format7)
            sheet.write(row+3, col, total_consultancy, format7)
            sheet.write(row+4, col, total_land_cost+total_consultancy, format_total_blue)
            sheet.write(row+6, col, total_commission, format7)
            sheet.write(row+7, col, total_fgr, format7)
            row += 10
        # sheet.write(row+1, 1, 'Other', grey_black)
        # sheet.write(row+2, 1, 'Total', format6)
        col =3
        # total_salaries = 0
        # total_other = 0
        # for year in year_list_new:
        #     result[year]['salaries']
        #     sheet.write(row, col, result[year]['salaries'], format7)
        #     if year == 2019:
        #         other_year = 0
        #     else:
        #         other_year = result[year]['other']
        #     sheet.write(row+1, col, other_year, format7)
        #     sheet.write(row+2, col, result[year]['salaries']+other_year, format8)
        #     total_salaries += result[year]['salaries']
        #     total_other += other_year
        #     col +=1
        # sheet.write(row, col, total_salaries, format7)
        # sheet.write(row+1, col, total_other, format7)
        # sheet.write(row+2, col, total_other+total_salaries, format8)







        row += 1
        col = 3
        sheet.merge_range('D77:H77', "July 01 to June 30", format2)
        for data in year_list_new:
            sheet.write(row, col, data, format2)
            col +=1
        sheet.write(row, col, 'Total', format2)
        col = 1
        sheet.write(row-1, col, 'Operational Expense', format3)
        row +=2
        sheet.write(row, 1, 'Salaries', grey_black)
        sheet.write(row+1, 1, 'Other', grey_black)
        sheet.write(row+2, 1, 'Total', format6)
        col =3
        total_salaries = 0
        total_other = 0
        for year in year_list_new:
            result[year]['salaries']
            sheet.write(row, col, result[year]['salaries'], format7)
            if year == 2019:
                other_year = 0
            else:
                other_year = result[year]['other']
            sheet.write(row+1, col, other_year, format7)
            sheet.write(row+2, col, result[year]['salaries']+other_year, format8)
            total_salaries += result[year]['salaries']
            total_other += other_year
            col +=1
        sheet.write(row, col, total_salaries, format7)
        sheet.write(row+1, col, total_other, format7)
        sheet.write(row+2, col, total_other+total_salaries, format8)
        workbook.close()
        output.seek(0)
        generated_file = output.read()
        output.close()

        return generated_file
