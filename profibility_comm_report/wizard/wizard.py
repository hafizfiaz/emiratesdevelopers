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


class ProfitabilityReport(models.TransientModel):
    _name = "profitability.comm.report.wizard"

    project_id = fields.Many2one('account.asset.asset', string="Project", domain="[('project', '=', True)]")
    # start_date = fields.Date(string='Start Date', required=True)
    # end_date = fields.Date(string='End Date', required=True)

    def _get_report_name(self):
        return _('Profitability Commission Report')

    def get_report_filename(self, options):
        """The name that will be used for the file when downloading pdf,xlsx,..."""
        return self._get_report_name().lower().replace(' ', '_')

    def check_report(self):
        context = self._context
        self.ensure_one()
        data = {}
        data['form'] = self.read(['project_id'])[0]
        data['form']['xls'] = context.get('xls_export')
        return {
            'type': 'ir_actions_account_report_download',
            'data': {'model': 'profitability.comm.report.wizard',
                     'options': json.dumps(data, default=date_utils.json_default),
                     'output_format': 'xlsx',
                     'report_name': 'Profitability Commission Report',
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
        env_obj = vals.env['report.profibility_comm_report.profitability_comm_report']
        result = env_obj.get_result()
        sheet = workbook.add_worksheet()
        # format1 = workbook.add_format({'font_size': 16, 'align': 'center', 'bg_color': '#CFCCCE', 'bold': True, 'text_wrap': True})
        format_main = workbook.add_format({'font_size': 14, 'align': 'left','bg_color': '#CFCCCE', 'bold': True, 'text_wrap': True})
        format_main2 = workbook.add_format({'font_size': 9, 'align': 'center','bg_color': '#CFCCCE', 'bold': True, 'text_wrap': True})
        format1 = workbook.add_format({'font_size': 9, 'align': 'right', 'text_wrap': True,'num_format': '#,###'})
        format1t = workbook.add_format({'font_size': 9, 'align': 'right', 'text_wrap': True,'num_format': '#,###'})
        format1b = workbook.add_format({'font_size': 9, 'align': 'right', 'text_wrap': True,'num_format': '#,###'})
        format1bb = workbook.add_format({'font_size': 9, 'align': 'right', 'text_wrap': True,'num_format': '#,###'})
        format1bt = workbook.add_format({'font_size': 9, 'align': 'right', 'text_wrap': True,'num_format': '#,###'})
        format1bs = workbook.add_format({'font_size': 9, 'align': 'right', 'text_wrap': True})
        format1bsn = workbook.add_format({'font_size': 9, 'align': 'right', 'text_wrap': True,'num_format': '#,###'})
        format11 = workbook.add_format({'font_size': 10, 'align': 'center', 'text_wrap': True,'bold': True})
        format2 = workbook.add_format({'font_size': 9, 'align': 'left', 'bold': False, 'text_wrap': True})
        format2b = workbook.add_format({'font_size': 9, 'align': 'left', 'bold': True, 'text_wrap': True})
        second_mainl = workbook.add_format({'font_size': 10, 'align': 'left', 'bg_color': '#6D0035', 'bold': True, 'text_wrap': True})
        second_main = workbook.add_format({'font_size': 10, 'align': 'center', 'bg_color': '#6D0035', 'bold': True, 'text_wrap': True})
        grey_black = workbook.add_format({'font_size': 10, 'align': 'left', 'bg_color': '#ADA8A7', 'bold': False, 'text_wrap': True})
        sky_black = workbook.add_format({'font_size': 10, 'align': 'left', 'bg_color': '#D8EAF9', 'bold': False, 'text_wrap': True})
        second_main.set_font_color('#FFFFFF')
        second_mainl.set_font_color('#FFFFFF')
        format_main.set_font_color('#6D0035')
        format_main2.set_font_color('#6D0035')
        format_main2.set_border()
        format11.set_border()
        format1t.set_top()
        format1b.set_bottom()
        format1bb.set_top()
        format1bb.set_bottom(6)
        format1bt.set_top()
        format1bt.set_bottom()
        format1bs.set_top()
        format1bs.set_bottom()
        format1bsn.set_top()
        format1bsn.set_bottom()
        # format1.set_align('right')
        sheet.hide_gridlines(2)
        sheet.set_column('A:A', 30)
        sheet.set_column('B:B', 3)
        sheet.set_column('C:Y', 16)
        sheet.set_row(0, 25)
        # sheet.set_row(2, 47)
        projects = self.env['account.asset.asset'].search([('project', '=', True)])
        plen = len(projects)
        # sheet.merge_range(0, 0, 0, 2, "Project Profitability Report", format_main)
        sheet.merge_range(2, 2, 2, plen+1, "Project Profitability / SFt", second_main)
        a = 2
        for p1 in projects:
            sheet.write(3, a, p1.name, format_main2)
            a+=1
        # sheet.write(3, a, 'Total', format_main2)

        sheet.write(3, 0, 'Description', second_mainl)
        # sheet.merge_range(4, 2, 4, plen+2, "AED", format11)

    # ============================Unsold====================================

        sheet.write(4, 0, 'Sales Price/SFt', format2)
        a = 2
        line_total = 0
        for p in projects:
            sheet.write(4, a, result[p.name]['sale_area_psft'], format1b)
            line_total += result[p.name]['sale_area_psft']
            a+=1
        # sheet.write(6, a, line_total, format1t)

        sheet.write(5, 0, 'Commissions (External+Internal) SFt', format2)
        a = 2
        line_total = 0
        for p in projects:
            sheet.write(5, a, result[p.name]['commissions_sft'], format1b)
            line_total += result[p.name]['commissions_sft']
            a+=1
        # sheet.write(7, a, line_total, format1)

        sheet.write(6, 0, 'Sales Price Net of Commission', format2)
        a = 2
        line_total = 0
        for p in projects:
            sheet.write(6, a, result[p.name]['sale_net_of_commissions'], format1b)
            line_total += result[p.name]['sale_net_of_commissions']
            a+=1
        # sheet.write(8, a, line_total, format1b)

        sheet.write(7, 0, 'Cost of Product/Sft (Sold)', format2)
        a = 2
        line_total = 0
        for p in projects:
            sheet.write(7, a, result[p.name]['cop_sold'], format1b)
            line_total += result[p.name]['cop_sold']
            a+=1
        # sheet.write(10, a, line_total, format1t)

        sheet.write(8, 0, 'Cost of Product/Sft (Unsold)', format2)
        a = 2
        line_total = 0
        for p in projects:
            sheet.write(8, a, result[p.name]['cop_unsold'], format1b)
            line_total += result[p.name]['cop_unsold']
            a+=1
        # sheet.write(10, a, line_total, format1t)

        sheet.write(9, 0, 'Cost of Product/Sft (Sold + Unsold)', format2)
        a = 2
        line_total = 0
        for p in projects:
            sheet.write(9, a, result[p.name]['cop_sold_unsold'], format1b)
            line_total += result[p.name]['cop_sold_unsold']
            a+=1
        # sheet.write(10, a, line_total, format1t)

        sheet.write(10, 0, 'Gross Profit/Sft', format2)
        a = 2
        line_total = 0
        for p in projects:
            sheet.write(10, a, result[p.name]['gross_profit'], format1bb)
            line_total += result[p.name]['gross_profit']
            a+=1
        # sheet.write(11, a, line_total, format1)

        sheet.write(11, 0, 'Gross Profit/SFt %', format2)
        a = 2
        line_total = 0
        for p in projects:
            sheet.write(11, a, result[p.name]['gross_profit_perc'], format1bb)
            line_total += result[p.name]['gross_profit_perc']
            a+=1
        # sheet.write(12, a, line_total, format1b)

        sheet.write(16, 0, 'Commission (External+Internal)', grey_black)
        a = 2
        line_total = 0
        for p in projects:
            sheet.write(16, a, result[p.name]['commissions'], format1bt)
            line_total += result[p.name]['commissions']
            a+=1
        # sheet.write(12, a, line_total, format1b)



        workbook.close()
        output.seek(0)
        generated_file = output.read()
        output.close()

        return generated_file
