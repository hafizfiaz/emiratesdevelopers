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


class CashFlowReportWizard(models.TransientModel):
    _name = "cashflow.report.wizard"

    project_id = fields.Many2one('account.asset.asset', string="Project", domain="[('project', '=', True)]")
    start_date = fields.Date(string='Start Date', required=True)
    end_date = fields.Date(string='End Date', required=True)

    def _get_report_name(self):
        return _('CashFlow Report')

    def get_report_filename(self, options):
        """The name that will be used for the file when downloading pdf,xlsx,..."""
        return self._get_report_name().lower().replace(' ', '_')

    def check_report(self):
        context = self._context
        self.ensure_one()
        data = {}
        data['form'] = self.read(['start_date','end_date','project_id'])[0]
        data['form']['xls'] = context.get('xls_export')
        return {
            'type': 'ir_actions_account_report_download',
            'data': {'model': 'cashflow.report.wizard',
                     'options': json.dumps(data, default=date_utils.json_default),
                     'output_format': 'xlsx',
                     'report_name': 'Cashflow Report',
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
        env_obj = vals.env['report.cashflow_report.cashflow_report']
        result = env_obj.get_result(vals.project_id, vals.start_date, vals.end_date)
        sheet = workbook.add_worksheet()
        format1 = workbook.add_format({'font_size': 16, 'align': 'center', 'bg_color': '#C9C9C9', 'bold': True, 'text_wrap': True})
        format1.set_font_color('#000000')
        format2 = workbook.add_format({'font_size': 12, 'bold': True, 'text_wrap': True})
        format9 = workbook.add_format({'font_size': 12, 'bold': True, 'bg_color': '#36B642', 'text_wrap': True})
        format7 = workbook.add_format({'font_size': 12, 'bold': True, 'bg_color': '#C9C9C9','num_format': '#,###', 'text_wrap': True})
        format3 = workbook.add_format({'font_size': 12, 'bg_color': '#C9C9C9', 'text_wrap': True})
        format4 = workbook.add_format({'font_size': 10, 'text_wrap': True})
        format5 = workbook.add_format({'font_size': 10, 'num_format': '#,###', 'text_wrap': True})
        format1.set_align('center')
        format2.set_align('left')
        format9.set_align('center')
        format3.set_align('left')
        format4.set_align('center')
        format5.set_align('right')

        # sheet.set_column('A:B', 18)
        sheet.set_column('A:Y', 20)
        sheet.set_row(1, 15)
        sheet.set_row(2, 47)

        sheet.merge_range(0, 0, 1, 20, "Samana Golf Avenue", format1)
        sheet.merge_range(4, 0, 2, 20, "Project Cashflow Till Handover", format1)

        sheet.write(6, 0, 'Collections', format2)
        sheet.write(7, 0, 'Regular Collections', format2)
        sheet.write(8, 0, 'OverDue Balance', format2)
        sheet.write(9, 0, 'Total', format2)
        c = 1
        for line in result['collections']:
            sheet.write(6, c, line, format3)
            c += 1
        c = 1
        for line in result['regular_collections']:

            sheet.write(7, c, line, format5)
            c += 1
        c = 1
        for line in result['overdue_collections']:
            sheet.write(8, c, line, format5)
            c += 1
        c=1
        a=0
        for line in result['regular_collections']:
            sheet.write(9, c, result['regular_collections'][a]+result['overdue_collections'][a], format7)
            a+=1
            c += 1

        # sheet.merge_range('E3:F3', "Top Defaulters", format2)
        # sheet.merge_range('G3:H3', vals.top_defaulter or ' ', format3)
        # projects = ''
        # for project in vals.project_ids:
        #     projects += project.name + ", "

        sheet.merge_range('I3:J3', "Projects", format2)
        # sheet.merge_range('K3:L3', projects or ' ', format3)
        properties = ''

        workbook.close()
        output.seek(0)
        generated_file = output.read()
        output.close()

        return generated_file
