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


class ProfitLossWizard(models.TransientModel):
    _name = "profit.loss.wizard"

    # project_id = fields.Many2one('account.asset.asset', string="Project", domain="[('project', '=', True)]")
    # start_date = fields.Date(string='Start Date', required=True)
    # end_date = fields.Date(string='End Date', required=True)

    def _get_report_name(self):
        return _('Profit Loss Report')

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
            'data': {'model': 'profit.loss.wizard',
                     'options': json.dumps(data, default=date_utils.json_default),
                     'output_format': 'xlsx',
                     'report_name': 'PDC Movement Report',
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
        env_obj = vals.env['report.pdc_movement.profit_loss_report']
        result, project_list = env_obj.get_result()
        sheet = workbook.add_worksheet()
        format1 = workbook.add_format({'font_size': 12,'border': 2, 'align': 'center', 'bg_color': '#801700', 'bold': True, 'text_wrap': True})
        format2 = workbook.add_format({'font_size': 12,'border': 2, 'align': 'center', 'bg_color': '#C9C9C9', 'bold': True, 'text_wrap': True})
        format10 = workbook.add_format({'font_size': 12,'align': 'center', 'bold': True, 'text_wrap': True})
        format1.set_font_color('#ffff')
        format2.set_font_color('#801700')
        format10.set_font_color('#801700')
        formatnumber = workbook.add_format({'font_size': 12, 'num_format': '#,###', 'bold': True, 'bg_color': '#C9C9C9', 'text_wrap': True})
        format9 = workbook.add_format({'font_size': 12, 'bold': True, 'bg_color': '#36B642', 'text_wrap': True})
        format7 = workbook.add_format({'font_size': 12, 'num_format': '#,###', 'text_wrap': True})
        format11 = workbook.add_format({'font_size': 12, 'num_format': '#,###', 'text_wrap': True})
        format12 = workbook.add_format({'font_size': 12, 'num_format': '#,###', 'text_wrap': True})

        format11.set_bottom(2)
        format12.set_bottom(2)
        format12.set_top(2)

        formatdate = workbook.add_format({'font_size': 12, 'text_wrap': True})
        format3 = workbook.add_format({'font_size': 12, 'bg_color': '#C9C9C9', 'text_wrap': True})
        format4 = workbook.add_format({'font_size': 10, 'text_wrap': True})
        format5 = workbook.add_format({'font_size': 10, 'num_format': '#,###', 'text_wrap': True})
        format1.set_align('center')
        # format1.set_font_color('#000000')
        # format2.set_align('left')
        formatnumber.set_align('right')
        format9.set_align('center')
        format3.set_align('left')
        format4.set_align('center')
        format5.set_align('right')
        formatdate.set_align('right')

        # sheet.set_column('A:B', 18)
        sheet.set_column('A:A', 50)
        sheet.set_column('B:Y', 25)
        # sheet.set_row(1, 15)
        sheet.set_row(2, 30)
        sheet.set_row(6, 40)

        sheet.merge_range(1, 5, 0, 1, "Profit and Loss Statement- Since Inception", format1)

        # sheet.write(4, 3, 'Report Date', format4)
        # sheet.write(4, 4, datetime.datetime.now().strftime("%Y/%m/%d"), format4)
        # sheet.write(5, 3, 'Download By', format4)
        # sheet.write(5, 4, self.env.user.name, format4)
        # sheet.write(6, 0, 'Projects', format1)
        project_col = 1
        sheet.write(4, project_col-1, 'Revenue', format10)
        sheet.write(5, project_col-1, 'Direct Cost', format10)
        sheet.write(6, project_col-1, 'Gross Profit', format10)
        sheet.write(8, project_col-1, 'Gross Profit (%)', format10)
        # sheet.write(8, project_row-1, 'Realized Receipts Net of Oqood', format2)
        # sheet.write(9, project_row-1, 'Balance Due As of Now', format2)
        # sheet.write(10, project_row-1, 'Receivable Till Handover', format2)
        # sheet.write(11, project_row-1, 'Post Handover Receivables', format2)
        # sheet.write(12, project_row-1, 'Handover Date', format2)
        # value_row = 7
        # total_sale = 0.0
        # total_real = 0.0
        # total_bal = 0.0
        # total_receive = 0.0
        # total_post = 0.0
        for list in project_list:
            gross_profit = result[list]['Revenue'] - result[list]['Project Costing']
            revenue = result[list]['Revenue']
            project_cost = result[list]['Project Costing']
            sheet.write(2, project_col, list, format2)
            sheet.write(3, project_col, "(AED)", format2)
            sheet.write(4, project_col, revenue, format7)
            sheet.write(5, project_col, project_cost, format11)
            sheet.write(6, project_col, gross_profit, format11)
            if revenue == 0:
                revenue = 1
            sheet.write(8, project_col, (gross_profit/revenue)*100, format12)
        #     sheet.write(8, project_row, result[list]['Realized Receipts Net of Oqood'], format7)
        #     sheet.write(9, project_row, result[list]['Balance Due As of Now'], format7)
        #     sheet.write(10, project_row, result[list]['Receivable Till Handover'], format7)
        #     sheet.write(11, project_row, result[list]['Post Handover Receivables'], format7)
        #     if result[list]['Handover Date']:
        #         sheet.write(12, project_row, result[list]['Handover Date'].strftime("%Y/%m/%d"), formatdate)
        #     total_sale += result[list]['Sales Value']
        #     total_real += result[list]['Realized Receipts Net of Oqood']
        #     total_bal += result[list]['Balance Due As of Now']
        #     total_receive += result[list]['Receivable Till Handover']
        #     total_post += result[list]['Post Handover Receivables']
            project_col += 1
        #
        # sheet.write(6, project_row, "Total", format1)
        # sheet.write(7, project_row, total_sale, formatnumber)
        # sheet.write(8, project_row, total_real, formatnumber)
        # sheet.write(9, project_row, total_bal, formatnumber)
        # sheet.write(10, project_row, total_receive, formatnumber)
        # sheet.write(11, project_row,total_post, formatnumber)
        workbook.close()
        output.seek(0)
        generated_file = output.read()
        output.close()

        return generated_file
