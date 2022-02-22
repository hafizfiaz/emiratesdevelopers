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


class PdcMovementReportWizard(models.TransientModel):
    _name = "pdc.bounced.movement.report.wizard"

    # project_id = fields.Many2one('account.asset.asset', string="Project", domain="[('project', '=', True)]")
    start_date = fields.Date(string='Start Date', required=True)
    end_date = fields.Date(string='End Date', required=True)

    def _get_report_name(self):
        return _('Bounced PDC Movement Report')

    def get_report_filename(self, options):
        """The name that will be used for the file when downloading pdf,xlsx,..."""
        return self._get_report_name().lower().replace(' ', '_')

    def check_report(self):
        context = self._context
        self.ensure_one()
        data = {}
        data['form'] = self.read(['start_date','end_date'])[0]
        data['form']['xls'] = context.get('xls_export')
        return {
            'type': 'ir_actions_account_report_download',
            'data': {'model': 'pdc.bounced.movement.report.wizard',
                     'options': json.dumps(data, default=date_utils.json_default),
                     'output_format': 'xlsx',
                     'report_name': 'Bounced PDC Movement Report',
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
        env_obj = vals.env['report.pdc_movement.pdc_bounced_movement_report']
        result = env_obj.get_result(vals.start_date, vals.end_date)
        sheet = workbook.add_worksheet()
        format1 = workbook.add_format({'font_size': 16, 'align': 'center', 'bg_color': '#C9C9C9', 'bold': True, 'text_wrap': True})
        format1.set_font_color('#000000')
        format2 = workbook.add_format({'font_size': 12, 'bold': True, 'bg_color': '#C9C9C9', 'text_wrap': True})
        format9 = workbook.add_format({'font_size': 12, 'bold': True, 'bg_color': '#36B642', 'text_wrap': True})
        format7 = workbook.add_format({'font_size': 12, 'num_format': '#,###', 'text_wrap': True})
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
        sheet.set_column('A:A', 60)
        sheet.set_column('B:Y', 20)
        sheet.set_row(1, 15)
        sheet.set_row(2, 47)

        sheet.merge_range(3, 0, 1, 3, "Bounced PDCs Movement", format1)

        sheet.write(4, 1, 'Start Date', format4)
        sheet.write(4, 2, vals.start_date.strftime("%Y/%m/%d"), format4)
        sheet.write(5, 1, 'End Date', format4)
        sheet.write(5, 2, vals.end_date.strftime("%Y/%m/%d"), format4)
        sheet.write(4, 3, 'Report Date', format4)
        sheet.write(4, 4, datetime.datetime.now().strftime("%Y/%m/%d"), format4)
        sheet.write(5, 3, 'Download By', format4)
        sheet.write(5, 4, self.env.user.name, format4)

        sheet.write(6, 0, 'Description', format2)
        sheet.write(6, 1, 'Amount', format2)
        sheet.write(6, 2, 'Count', format2)
        total_count = 0
        total = 0
        row = 7

        sheet.write(row, 0, "Bounced Cheques in hand at the start of the period", format3)
        sheet.write(row, 1, result['cheques bounced'][1], format7)
        sheet.write(row, 2, result['cheques bounced'][0], format7)
        total_count += result['cheques bounced'][1]
        total += result['cheques bounced'][0]
        row += 1
        sheet.write(row, 0, "Additional Cheques bounced during the period-Regular", format3)
        sheet.write(row, 1, result['cheques regular'][1], format7)
        sheet.write(row, 2, result['cheques regular'][0], format7)
        total_count += result['cheques regular'][1]
        total += result['cheques regular'][0]
        row += 1
        sheet.write(row, 0, "Additional Cheques bounced during the period-EOI", format3)
        sheet.write(row, 1, result['cheques eoi'][1], format7)
        sheet.write(row, 2, result['cheques eoi'][0], format7)
        total_count += result['cheques eoi'][1]
        total += result['cheques eoi'][0]
        row += 1
        sheet.write(row, 0, "Cheques cleared during the period", format3)
        sheet.write(row, 1, result['cheques cleared'][1], format7)
        sheet.write(row, 2, result['cheques cleared'][0], format7)
        total_count -= result['cheques cleared'][1]
        total -= result['cheques cleared'][0]
        row += 1
        sheet.write(row, 0, "Closing Balance of Collected Cheques", format3)
        sheet.write(row, 1, total_count, format7)
        sheet.write(row, 2, total, format7)
        row += 1

        sheet2 = workbook.add_worksheet(str('Bounced Cheques'))

        sheet2.write(1, 1, "Create Date", format3)
        sheet2.write(1, 2, "Payment Date", format3)
        sheet2.write(1, 3, "Number", format3)
        sheet2.write(1, 4, "Journal", format3)
        sheet2.write(1, 5, "Last Updated On", format3)
        sheet2.write(1, 6, "Check Number", format3)
        sheet2.write(1, 7, "Maturity Date", format3)
        sheet2.write(1, 8, "Customer", format3)
        sheet2.write(1, 9, "Project", format3)
        sheet2.write(1, 10, "Property", format3)
        sheet2.write(1, 11, "Collection Type", format3)
        sheet2.write(1, 12, "Amount", format3)
        sheet2.write(1, 13, "Bank Where The Check is Deposited", format3)
        sheet2.write(1, 14, "Payment Ref", format3)
        sheet2.set_column('A:Y', 15)
        row1 = 2
        for rec in result['bounced cheques view']:
            sheet2.write(row1, 1, rec['create_date'].strftime("%Y/%m/%d"), format7)
            sheet2.write(row1, 2, rec['date'].strftime("%Y/%m/%d"), format7)
            sheet2.write(row1, 3, rec['name'], format7)
            sheet2.write(row1, 4, rec['journal_name'], format7)
            sheet2.write(row1, 5, rec['write_date'].strftime("%Y/%m/%d"), format7)
            sheet2.write(row1, 6, rec['check_number'], format7)
            sheet2.write(row1, 7, rec['maturity_date'].strftime("%Y/%m/%d") if rec['maturity_date'] else rec['maturity_date'], format7)
            sheet2.write(row1, 8, rec['partner_name'], format7)
            sheet2.write(row1, 9, rec['asset_project_name'], format7)
            sheet2.write(row1, 10, rec['property_name'], format7)
            sheet2.write(row1, 11, rec['collection_type_name'], format7)
            sheet2.write(row1, 12, rec['amount'], format7)
            sheet2.write(row1, 13, rec['bank_deposit'], format7)
            sheet2.write(row1, 14, rec['reference'], format7)
            row1 += 1



        sheet2 = workbook.add_worksheet(str('Additional Cheques period Regular'))

        sheet2.write(1, 1, "Create Date", format3)
        sheet2.write(1, 2, "Payment Date", format3)
        sheet2.write(1, 3, "Number", format3)
        sheet2.write(1, 4, "Journal", format3)
        sheet2.write(1, 5, "Last Updated On", format3)
        sheet2.write(1, 6, "Check Number", format3)
        sheet2.write(1, 7, "Maturity Date", format3)
        sheet2.write(1, 8, "Customer", format3)
        sheet2.write(1, 9, "Project", format3)
        sheet2.write(1, 10, "Property", format3)
        sheet2.write(1, 11, "Collection Type", format3)
        sheet2.write(1, 12, "Amount", format3)
        sheet2.write(1, 13, "Bank Where The Check is Deposited", format3)
        sheet2.write(1, 14, "Payment Ref", format3)
        sheet2.set_column('A:Y', 15)
        row1 = 2
        for rec in result['cheques regular view']:
            sheet2.write(row1, 1, rec['create_date'].strftime("%Y/%m/%d"), format7)
            sheet2.write(row1, 2, rec['date'].strftime("%Y/%m/%d"), format7)
            sheet2.write(row1, 3, rec['name'], format7)
            sheet2.write(row1, 4, rec['journal_name'], format7)
            sheet2.write(row1, 5, rec['write_date'].strftime("%Y/%m/%d"), format7)
            sheet2.write(row1, 6, rec['check_number'], format7)
            sheet2.write(row1, 7, rec['maturity_date'].strftime("%Y/%m/%d") if rec['maturity_date'] else rec['maturity_date'], format7)
            sheet2.write(row1, 8, rec['partner_name'], format7)
            sheet2.write(row1, 9, rec['asset_project_name'], format7)
            sheet2.write(row1, 10, rec['property_name'], format7)
            sheet2.write(row1, 11, rec['collection_type_name'], format7)
            sheet2.write(row1, 12, rec['amount'], format7)
            sheet2.write(row1, 13, rec['bank_deposit'], format7)
            sheet2.write(row1, 14, rec['reference'], format7)
            row1 += 1


        sheet2 = workbook.add_worksheet(str('eoi Cheques'))

        sheet2.write(1, 1, "Create Date", format3)
        sheet2.write(1, 2, "Payment Date", format3)
        sheet2.write(1, 3, "Number", format3)
        sheet2.write(1, 4, "Journal", format3)
        sheet2.write(1, 5, "Last Updated On", format3)
        sheet2.write(1, 6, "Check Number", format3)
        sheet2.write(1, 7, "Maturity Date", format3)
        sheet2.write(1, 8, "Customer", format3)
        sheet2.write(1, 9, "Project", format3)
        sheet2.write(1, 10, "Property", format3)
        sheet2.write(1, 11, "Collection Type", format3)
        sheet2.write(1, 12, "Amount", format3)
        sheet2.write(1, 13, "Bank Where The Check is Deposited", format3)
        sheet2.write(1, 14, "Payment Ref", format3)
        sheet2.set_column('A:Y', 15)
        row1 = 2
        for rec in result['cheques eoi view']:
            sheet2.write(row1, 1, rec['create_date'].strftime("%Y/%m/%d"), format7)
            sheet2.write(row1, 2, rec['date'].strftime("%Y/%m/%d"), format7)
            sheet2.write(row1, 3, rec['name'], format7)
            sheet2.write(row1, 4, rec['journal_name'], format7)
            sheet2.write(row1, 5, rec['write_date'].strftime("%Y/%m/%d"), format7)
            sheet2.write(row1, 6, rec['check_number'], format7)
            sheet2.write(row1, 7, rec['maturity_date'].strftime("%Y/%m/%d") if rec['maturity_date'] else rec['maturity_date'], format7)
            sheet2.write(row1, 8, rec['partner_name'], format7)
            sheet2.write(row1, 9, rec['asset_project_name'], format7)
            sheet2.write(row1, 10, rec['property_name'], format7)
            sheet2.write(row1, 11, rec['collection_type_name'], format7)
            sheet2.write(row1, 12, rec['amount'], format7)
            sheet2.write(row1, 13, rec['bank_deposit'], format7)
            sheet2.write(row1, 14, rec['reference'], format7)
            row1 += 1




        sheet2 = workbook.add_worksheet(str('cleared Cheques'))

        sheet2.write(1, 1, "Create Date", format3)
        sheet2.write(1, 2, "Payment Date", format3)
        sheet2.write(1, 3, "Number", format3)
        sheet2.write(1, 4, "Journal", format3)
        sheet2.write(1, 5, "Last Updated On", format3)
        sheet2.write(1, 6, "Check Number", format3)
        sheet2.write(1, 7, "Maturity Date", format3)
        sheet2.write(1, 8, "Customer", format3)
        sheet2.write(1, 9, "Project", format3)
        sheet2.write(1, 10, "Property", format3)
        sheet2.write(1, 11, "Collection Type", format3)
        sheet2.write(1, 12, "Amount", format3)
        sheet2.write(1, 13, "Bank Where The Check is Deposited", format3)
        sheet2.write(1, 14, "Payment Ref", format3)
        sheet2.set_column('A:Y', 15)
        row1 = 2
        for rec in result['cheques cleared view']:
            sheet2.write(row1, 1, rec['create_date'].strftime("%Y/%m/%d"), format7)
            sheet2.write(row1, 2, rec['date'].strftime("%Y/%m/%d"), format7)
            sheet2.write(row1, 3, rec['name'], format7)
            sheet2.write(row1, 4, rec['journal_name'], format7)
            sheet2.write(row1, 5, rec['write_date'].strftime("%Y/%m/%d"), format7)
            sheet2.write(row1, 6, rec['check_number'], format7)
            sheet2.write(row1, 7, rec['maturity_date'].strftime("%Y/%m/%d") if rec['maturity_date'] else rec['maturity_date'], format7)
            sheet2.write(row1, 8, rec['partner_name'], format7)
            sheet2.write(row1, 9, rec['asset_project_name'], format7)
            sheet2.write(row1, 10, rec['property_name'], format7)
            sheet2.write(row1, 11, rec['collection_type_name'], format7)
            sheet2.write(row1, 12, rec['amount'], format7)
            sheet2.write(row1, 13, rec['bank_deposit'], format7)
            sheet2.write(row1, 14, rec['reference'], format7)
            row1 += 1


        workbook.close()
        output.seek(0)
        generated_file = output.read()
        output.close()

        return generated_file
