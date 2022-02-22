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


class BuildinfMISReport(models.TransientModel):
    _name = "building.mis.report.wizard"

    project_id = fields.Many2one('account.asset.asset', string="Project", domain="[('project', '=', True)]")
    # start_date = fields.Date(string='Start Date', required=True)
    # end_date = fields.Date(string='End Date', required=True)

    def _get_report_name(self):
        return _('Building MIS Receivables Report')

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
            'data': {'model': 'building.mis.report.wizard',
                     'options': json.dumps(data, default=date_utils.json_default),
                     'output_format': 'xlsx',
                     'report_name': 'Building MIS Receivables Report',
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
        env_obj = vals.env['report.sd_xls_reports.building_mis']
        result = env_obj.get_result()
        sheet = workbook.add_worksheet()
        # format1 = workbook.add_format({'font_size': 16, 'align': 'center', 'bg_color': '#CFCCCE', 'bold': True, 'text_wrap': True})
        format_main = workbook.add_format({'font_size': 13, 'align': 'center','valign': 'vcenter','bg_color': '#FFF200', 'bold': True, 'text_wrap': True})
        format_main2 = workbook.add_format({'font_size': 10, 'align': 'center','valign': 'vcenter','bg_color': '#b8e08c', 'bold': True, 'text_wrap': True})
        format_main22 = workbook.add_format({'font_size': 10, 'align': 'center','valign': 'vcenter','bg_color': '#FFF200', 'bold': True, 'text_wrap': True})
        format1 = workbook.add_format({'font_size': 9, 'align': 'right', 'text_wrap': True,'num_format': '#,###'})
        format1t = workbook.add_format({'font_size': 9, 'align': 'right', 'text_wrap': True,'num_format': '#,###'})
        format1b = workbook.add_format({'font_size': 9, 'align': 'right', 'text_wrap': True,'num_format': '#,###'})
        formatdate = workbook.add_format({'font_size': 9,  'align': 'center', 'text_wrap': True})
        format1bb = workbook.add_format({'font_size': 9, 'align': 'right', 'text_wrap': True,'bold': True,'num_format': '#,###'})
        format1bs = workbook.add_format({'font_size': 9, 'align': 'right', 'text_wrap': True})
        format1bsn = workbook.add_format({'font_size': 9, 'align': 'right', 'text_wrap': True,'num_format': '#,###'})
        format11 = workbook.add_format({'font_size': 10, 'align': 'center', 'text_wrap': True,'bold': True})
        format2 = workbook.add_format({'font_size': 9, 'align': 'left', 'bold': False, 'text_wrap': True})

        format2b = workbook.add_format({'font_size': 9, 'align': 'left', 'bold': True, 'text_wrap': True})
        second_mainl = workbook.add_format({'font_size': 11, 'align': 'left', 'bg_color': '#92D050', 'bold': True, 'text_wrap': True})
        second_mainl2 = workbook.add_format({'font_size': 11, 'align': 'left', 'bg_color': '#FFF200', 'bold': True, 'text_wrap': True})
        second_main = workbook.add_format({'font_size': 10, 'align': 'center', 'bg_color': '#92D050', 'bold': True, 'text_wrap': True})
        grey_black = workbook.add_format({'font_size': 10, 'align': 'left', 'bg_color': '#ADA8A7', 'bold': False, 'text_wrap': True})
        sky_black = workbook.add_format({'font_size': 10, 'align': 'left', 'bg_color': '#D8EAF9', 'bold': False, 'text_wrap': True})
        # second_main.set_font_color('#92D050')
        # second_mainl.set_font_color('#92D050')
        # format_main.set_font_color('#6D0035')
        # format_main2.set_font_color('#6D0035')
        format_main.set_border()
        format_main2.set_border()
        format_main22.set_border()
        format11.set_border()
        format1t.set_top()
        format1b.set_bottom()
        formatdate.set_bottom()
        format1bb.set_top()
        format1bb.set_bottom(6)
        format1bs.set_top()
        format1bs.set_bottom()
        format1bsn.set_top()
        format1bsn.set_bottom()
        # format1.set_align('right')
        sheet.hide_gridlines(2)
        # sheet.set_column('A:', 25)
        sheet.set_column('A:A', 35)
        sheet.set_column('B:Y', 14)
        sheet.set_row(1, 25)
        sheet.set_row(3, 25)
        sheet.set_row(14, 25)
        # sheet.set_row(2, 47)
        projects = self.env['account.asset.asset'].search([('project', '=', True)])
        plen = len(projects)
        sheet.merge_range(1, 0, 1,  plen+1, "Samana Building MIS", format_main)
        sheet.merge_range(2, 0, 2, plen+1, "Receivables Summary", second_main)
        a = 1
        sheet.write(3, 0, '', second_mainl)
        for p1 in projects:
            sheet.write(3, a, p1.name, format_main2)
            a+=1
        sheet.write(3, a, 'Total', format_main2)

        # sheet.write(4, 0, 'Description', second_mainl)

    # ============================Report Receivable Values====================================

        sheet.write(4, 0, 'Sales Value', format2)
        a = 1
        line_total = 0
        for p in projects:
            sheet.write(4, a, result[p.name]['sales_value'], format1b)
            line_total += result[p.name]['sales_value']
            a+=1
        sheet.write(4, a, line_total, format1b)

        sheet.write(5, 0, 'Realised Collection - Net of Oqood and admin ', format2)
        a = 1
        line_total = 0
        for p in projects:
            sheet.write(5, a, result[p.name]['realized_net_of_o_a'], format1b)
            line_total += result[p.name]['realized_net_of_o_a']
            a+=1
        sheet.write(5, a, line_total, format1b)

        sheet.write(6, 0, 'Total Future Receivables', format2b)
        a = 1
        line_total = 0
        for p in projects:
            sheet.write(6, a, result[p.name]['total_future_receivable'], format1bb)
            line_total += result[p.name]['total_future_receivable']
            a+=1
        sheet.write(6, a, line_total, format1bb)

        sheet.write(7, 0, 'Over Due Payment', format2)
        a = 1
        line_total = 0
        for p in projects:
            sheet.write(7, a, result[p.name]['overdue_payment'], format1b)
            line_total += result[p.name]['overdue_payment']
            a+=1
        sheet.write(7, a, line_total, format1b)

        sheet.write(8, 0, 'Receivable till Handover', format2)
        a = 1
        line_total = 0
        for p in projects:
            sheet.write(8, a, result[p.name]['receivable_till_handover'], format1b)
            line_total += result[p.name]['receivable_till_handover']
            a+=1
        sheet.write(8, a, line_total, format1b)

        sheet.write(9, 0, 'Accumulated Receivables', format2)
        a = 1
        line_total = 0
        for p in projects:
            sheet.write(9, a, result[p.name]['accumulated_receivables'], format1b)
            line_total += result[p.name]['accumulated_receivables']
            a+=1
        sheet.write(9, a, line_total, format1b)

        sheet.write(10, 0, 'Post handover', format2)
        a = 1
        line_total = 0
        for p in projects:
            sheet.write(10, a, result[p.name]['post_handover'], format1b)
            line_total += result[p.name]['post_handover']
            a+=1
        sheet.write(10, a, line_total, format1b)

        sheet.write(11, 0, 'Handover Date (auto as dater changes)', format2)
        a = 1
        for p in projects:
            if result[p.name]['handover_date']:
                sheet.write(11, a, result[p.name]['handover_date'].strftime("%d/%m/%Y"), formatdate)
            else:
                sheet.write(11, a, 'N/A', formatdate)

            a+=1

    #===========================Payable Summary========================================

        sheet.merge_range(13, 0, 13, plen+1, "Payables Summary", second_main)
        a = 1
        sheet.write(14, 0, '', second_mainl2)
        for p1 in projects:
            sheet.write(14, a, p1.name, format_main22)
            a+=1
        sheet.write(14, a, 'Total', format_main22)

        sheet.write(15, 0, 'Contract Value Exc VAT ', format2)
        a = 1
        line_total = 0
        for p in projects:
            sheet.write(15, a, result[p.name]['contract_value_exc_vat'], format1b)
            line_total += result[p.name]['contract_value_exc_vat']
            a+=1
        sheet.write(15, a, line_total, format1b)

        sheet.write(16, 0, 'Savings', format2)
        a = 1
        line_total = 0
        for p in projects:
            sheet.write(16, a, result[p.name]['savings'], format1b)
            line_total += result[p.name]['savings']
            a+=1
        sheet.write(16, a, line_total, format1b)

        sheet.write(17, 0, 'Net Cost Exc VAT', format2)
        a = 1
        line_total = 0
        for p in projects:
            sheet.write(17, a, result[p.name]['net_cost_exc_vat'], format1b)
            line_total += result[p.name]['net_cost_exc_vat']
            a+=1
        sheet.write(17, a, line_total, format1b)

        sheet.write(18, 0, 'Retention', format2)
        a = 1
        line_total = 0
        for p in projects:
            sheet.write(18, a, result[p.name]['retention'], format1b)
            line_total += result[p.name]['retention']
            a+=1
        sheet.write(18, a, line_total, format1b)

        sheet.write(19, 0, 'Net Payable Inc VAT', format2)
        a = 1
        line_total = 0
        for p in projects:
            sheet.write(19, a, result[p.name]['net_payable_inc_vat'], format1b)
            line_total += result[p.name]['net_payable_inc_vat']
            a+=1
        sheet.write(19, a, line_total, format1b)

        sheet.write(20, 0, 'Paid Value', format2)
        a = 1
        line_total = 0
        for p in projects:
            sheet.write(20, a, result[p.name]['paid_value'], format1b)
            line_total += result[p.name]['paid_value']
            a+=1
        sheet.write(20, a, line_total, format1b)

        sheet.write(21, 0, 'Remaining Payable', format2b)
        a = 1
        line_total = 0
        for p in projects:
            sheet.write(21, a, result[p.name]['remaining_payable'], format1bb)
            line_total += result[p.name]['remaining_payable']
            a+=1
        sheet.write(21, a, line_total, format1bb)

        sheet.write(22, 0, 'Banks Balance: (Escrow+Sub Con.)', format2)
        a = 1
        line_total = 0
        for p in projects:
            sheet.write(22, a, result[p.name]['bank_bls'], format1b)
            line_total += result[p.name]['bank_bls']
            a+=1
        sheet.write(22, a, line_total, format1b)

        sheet.write(23, 0, 'Escrow Account', format2)
        a = 1
        line_total = 0
        for p in projects:
            sheet.write(23, a, result[p.name]['escrow_account'], format1b)
            line_total += result[p.name]['escrow_account']
            a+=1
        sheet.write(23, a, line_total, format1b)

        sheet.write(24, 0, 'Sub-Construction', format2)
        a = 1
        line_total = 0
        for p in projects:
            sheet.write(24, a, result[p.name]['sub_construction'], format1b)
            line_total += result[p.name]['sub_construction']
            a+=1
        sheet.write(24, a, line_total, format1b)

        sheet.write(25, 0, 'Cash Surplus/Deficit', format2b)
        a = 1
        line_total = 0
        for p in projects:
            sheet.write(25, a, result[p.name]['cash_surplus_deficit'], format1bb)
            line_total += result[p.name]['cash_surplus_deficit']
            a+=1
        sheet.write(25, a, line_total, format1bb)

        sheet.write(26, 0, 'Retention Account', format2)
        a = 1
        line_total = 0
        for p in projects:
            sheet.write(26, a, result[p.name]['retention_acc'], format1b)
            line_total += result[p.name]['retention_acc']
            a+=1
        sheet.write(26, a, line_total, format1b)



        workbook.close()
        output.seek(0)
        generated_file = output.read()
        output.close()

        return generated_file
