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
    _name = "profitability.report.wizard"

    project_id = fields.Many2one('account.asset.asset', string="Project", domain="[('project', '=', True)]")
    # start_date = fields.Date(string='Start Date', required=True)
    # end_date = fields.Date(string='End Date', required=True)

    def _get_report_name(self):
        return _('Project Profitability Report')

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
            'data': {'model': 'profitability.report.wizard',
                     'options': json.dumps(data, default=date_utils.json_default),
                     'output_format': 'xlsx',
                     'report_name': 'Project Profitability Report',
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
        env_obj = vals.env['report.project_profibility_report.profitability_report']
        result = env_obj.get_result()
        resullts = env_obj.get_results()
        sheet = workbook.add_worksheet()
        # format1 = workbook.add_format({'font_size': 16, 'align': 'center', 'bg_color': '#CFCCCE', 'bold': True, 'text_wrap': True})
        format_main = workbook.add_format({'font_size': 14, 'align': 'left','bg_color': '#CFCCCE', 'bold': True, 'text_wrap': True})
        format_main2 = workbook.add_format({'font_size': 9, 'align': 'center','bg_color': '#CFCCCE', 'bold': True, 'text_wrap': True})
        format1 = workbook.add_format({'font_size': 9, 'align': 'right', 'text_wrap': True,'num_format': '#,###'})
        format1bt = workbook.add_format({'font_size': 9, 'align': 'right', 'text_wrap': True,'num_format': '#,###'})
        format1t = workbook.add_format({'font_size': 9, 'align': 'right', 'text_wrap': True,'num_format': '#,###'})
        format1b = workbook.add_format({'font_size': 9, 'align': 'right', 'text_wrap': True,'num_format': '#,###'})
        format1bb = workbook.add_format({'font_size': 9, 'align': 'right', 'text_wrap': True,'num_format': '#,###'})
        format1bbb = workbook.add_format({'font_size': 9, 'align': 'right','bold': True, 'text_wrap': True,'num_format': '#,###'})
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
        format1bt.set_top()
        format1bt.set_bottom()
        format1b.set_bottom()
        format1bb.set_top()
        format1bb.set_bottom(6)
        format1bbb.set_top()
        format1bbb.set_bottom(6)
        format1bs.set_top()
        format1bs.set_bottom()
        format1bsn.set_top()
        format1bsn.set_bottom()
        # format1.set_align('right')
        sheet.hide_gridlines(2)
        sheet.set_column('A:A', 35)
        sheet.set_column('B:B', 3)
        sheet.set_column('C:Y', 16)
        sheet.set_row(0, 25)
        # sheet.set_row(2, 47)
        projects = self.env['account.asset.asset'].search([('project', '=', True)])
        plen = len(projects)
        sheet.merge_range(0, 0, 0, 2, "Project Profitability Report", format_main)
        sheet.merge_range(2, 2, 2, plen+2, "Project", second_main)
        a = 2
        for p1 in projects:
            sheet.write(3, a, p1.name, format_main2)
            a+=1
        sheet.write(3, a, 'Total', format_main2)

        sheet.write(4, 0, 'Description', second_mainl)
        sheet.merge_range(4, 2, 4, plen+2, "AED", format11)

    # ============================sold====================================

        sheet.write(6, 0, 'Sales(Sold Inventory)', grey_black)
        a = 2
        line_total = 0
        for p in projects:
            sheet.write(6, a, result[p.name]['sold_inv'], format1t)
            line_total += result[p.name]['sold_inv']
            a+=1
        sheet.write(6, a, line_total, format1t)

        sheet.write(7, 0, 'Price/SFt', sky_black)
        a = 2
        line_total = 0
        for p in projects:
            sheet.write(7, a, result[p.name]['sale_psft'], format1)
            line_total += result[p.name]['sale_psft']
            a+=1
        sheet.write(7, a, line_total, format1)

        sheet.write(8, 0, 'Sold Area (SFt)', format2)
        a = 2
        line_total = 0
        for p in projects:
            sheet.write(8, a, result[p.name]['sale_area_psft'], format1b)
            line_total += result[p.name]['sale_area_psft']
            a+=1
        sheet.write(8, a, line_total, format1b)

    #============================Unsold====================================

        sheet.write(10, 0, 'Value of UnSold Inventory)', grey_black)
        a = 2
        line_total = 0
        for p in projects:
            sheet.write(10, a, result[p.name]['unsold_inv'], format1t)
            line_total += result[p.name]['unsold_inv']
            a+=1
        sheet.write(10, a, line_total, format1t)

        sheet.write(11, 0, 'Price/SFt', sky_black)
        a = 2
        line_total = 0
        for p in projects:
            sheet.write(11, a, result[p.name]['unsold_psft'], format1)
            line_total += result[p.name]['unsold_psft']
            a+=1
        sheet.write(11, a, line_total, format1)

        sheet.write(12, 0, 'UnSold Area (SFt)', format2)
        a = 2
        line_total = 0
        for p in projects:
            sheet.write(12, a, result[p.name]['unsold_area_psft'], format1b)
            line_total += result[p.name]['unsold_area_psft']
            a+=1
        sheet.write(12, a, line_total, format1b)

    #============================SOld + Unsold====================================

        sheet.write(14, 0, 'Total Value (Sold+UnSold Inventory)', grey_black)
        a = 2
        line_total = 0
        for p in projects:
            sheet.write(14, a, result[p.name]['sold_unsold_inv'], format1t)
            line_total += result[p.name]['sold_unsold_inv']
            a+=1
        sheet.write(14, a, line_total, format1t)

        sheet.write(15, 0, 'Price (Sold+UnSold)/SFt', sky_black)
        a = 2
        line_total = 0
        for p in projects:
            sheet.write(15, a, result[p.name]['sold_unsold_psft'], format1)
            line_total += result[p.name]['sold_unsold_psft']
            a+=1
        sheet.write(15, a, line_total, format1)

        sheet.write(16, 0, 'Total Area (Sold+UnSold)', format2)
        a = 2
        line_total = 0
        for p in projects:
            sheet.write(16, a, result[p.name]['sold_unsold_area_psft'], format1b)
            line_total += result[p.name]['sold_unsold_area_psft']
            a+=1
        sheet.write(16, a, line_total, format1b)

    #============================Cost of product / cost of sales===================================

        sheet.write(18, 0, 'Cost of Product / Cost of Sales', grey_black)
        a = 2
        line_total = 0
        for p in projects:
            sheet.write(18, a, result[p.name]['cop_div_cos'], format1t)
            line_total += result[p.name]['cop_div_cos']
            a+=1
        sheet.write(18, a, line_total, format1t)

        sheet.write(19, 0, 'Cost of Product/SFt', sky_black)
        a = 2
        line_total = 0
        for p in projects:
            sheet.write(19, a, result[p.name]['cop_div_cos'] / (result[p.name]['sold_unsold_area_psft'] or 1), format1b)
            line_total += result[p.name]['cop_div_cos'] / (result[p.name]['sold_unsold_area_psft'] or 1)
            a+=1
        sheet.write(19, a, line_total, format1b)

    #============================Gross Profit===================================

        sheet.write(21, 0, 'Gross Profit', format2b)
        a = 2
        line_total = 0
        for p in projects:
            sheet.write(21, a, result[p.name]['sold_inv'] - result[p.name]['cop_div_cos'], format1bb)
            line_total += result[p.name]['sold_inv'] - result[p.name]['cop_div_cos']
            a+=1
        sheet.write(21, a, line_total, format1bb)

    #============================Gross Profit %===================================

        sheet.write(23, 0, 'Gross Profit %', grey_black)
        a = 2
        for p in projects:
            gross = result[p.name]['sold_inv'] - result[p.name]['cop_div_cos']
            gross_perc = round(( gross/ (result[p.name]['sold_inv'] or 1)) * 100)
            sheet.write(23, a, str(gross_perc)+'%', format1bs)
            a+=1

    #============================Gross Profit/SFt===================================

        sheet.write(25, 0, 'Gross Profit/SFt', grey_black)
        a = 2
        for p in projects:
            gross = result[p.name]['sold_inv'] - result[p.name]['cop_div_cos']
            gross_profit_sft = round((gross/(result[p.name]['sale_area_psft'] or 1)))
            sheet.write(25, a, gross_profit_sft, format1bsn)
            a+=1

    #============================Commissions===================================

        sheet.write(27, 0, 'Commission', grey_black)
        sheet.write(28, 0, 'Commission/SFt', sky_black)
        a = 2
        for p in projects:
            sheet.write(28, a, result[p.name]['commissions_sft'], format1t)
            a+=1

        sheet.write(29, 0, 'Commission %', sky_black)
        a = 2
        for p in projects:
            # str(round())+' %'
            sheet.write(29, a, str(round(result[p.name]['comm_perc']))+' %', format1b)
            a+=1

        sheet.write(31, 0, 'Gross Profit Net of Commission', grey_black)
        a = 2
        for p in projects:
            sheet.write(31, a, result[p.name]['gross_profit_noc'], format1b)
            a+=1

        sheet.write(33, 0, 'Gross Profit/Sft Net of Commission %', grey_black)
        a = 2
        for p in projects:
            sheet.write(33, a, str(round(result[p.name]['gross_profit_sft_noc_perc']))+' %', format1bbb)
            a+=1

        # ============================Commissions===================================

        sheet.write(35, 0, 'FGR', grey_black)
        sheet.write(36, 0, 'FGR/SFt', sky_black)
        a = 2
        for p in projects:
            sheet.write(36, a, result[p.name]['fgr_sft'], format1t)
            a += 1

        sheet.write(37, 0, 'FGR %', sky_black)
        a = 2
        for p in projects:
            # str(round())+' %'
            sheet.write(37, a, str(round(result[p.name]['fgr_perc'])) + ' %', format1b)
            a += 1

        sheet.write(39, 0, 'Gross Profit Net of FGR', grey_black)
        a = 2
        for p in projects:
            # str(round())+' %'
            sheet.write(39, a, result[p.name]['gross_profit_no_fgr'], format1bb)
            a += 1

        sheet.write(41, 0, 'Gross Profit/Sft Net of FGR & Commission', sky_black)
        a = 2
        for p in projects:
            sheet.write(41, a, result[p.name]['gross_profit_no_fgr_com'], format1t)
            a += 1

        sheet.write(42, 0, 'Gross Profit/Sft Net of FGR & Commission %', sky_black)
        a = 2
        for p in projects:
            # str(round())+' %'
            sheet.write(42, a, str(round(result[p.name]['gross_profit_no_fgr_com_perc'])) + ' %', format1b)
            a += 1

        #============================COST OF Product Main===================================
        sheet.write(45, 0, 'Cost of Product (Upon 100% Completion)', second_mainl)
        a = 2
        for p1 in projects:
            sheet.write(45, a, p1.name, format_main2)
            a += 1
        sheet.write(45, a, 'Total', format_main2)


        #===================Land cost======================

        sheet.write(47, 0, 'Land Cost', grey_black)
        a = 2
        line_total = 0
        for p in projects:
            sheet.write(47, a, result[p.name]['land_cost'], format1)
            line_total += result[p.name]['land_cost']
            a+=1
        sheet.write(47, a, line_total, format1)

        #===================Cost of Construction======================

        sheet.write(49, 0, 'Cost of Construction', grey_black)
        a = 2
        line_total = 0
        for p in projects:
            sheet.write(49, a, result[p.name]['cost_of_construction'], format1)
            line_total += result[p.name]['cost_of_construction']
            a+=1
        sheet.write(49, a, line_total, format1)

        #===================Consultancy Other costs======================

        sheet.write(51, 0, 'Consultancy+Other Costs', grey_black)
        a = 2
        line_total = 0
        for p in projects:
            sheet.write(51, a, result[p.name]['consult_other_cost'], format1)
            line_total += result[p.name]['consult_other_cost']
            a+=1
        sheet.write(51, a, line_total, format1)


        #===================COst totals======================

        # sheet.write(33, 0, 'Consultancy+Other Costs', grey_black)
        a = 2
        line_total = 0
        for p in projects:
            sheet.write(53, a, result[p.name]['cop_div_cos'], format1bsn)
            line_total += result[p.name]['cop_div_cos']
            a+=1
        sheet.write(53, a, line_total, format1bsn)

        #============================COST OF Product Till Date===================================
        sheet.write(56, 0, 'Cost of Product (Incurred Till Date)', second_mainl)
        a = 2
        for p1 in projects:
            sheet.write(56, a, p1.name, format_main2)
            a += 1
        sheet.write(56, a, 'Total', format_main2)


        #===================Land cost======================

        sheet.write(58, 0, 'Land Cost', grey_black)
        a = 2
        line_total = 0
        for p in projects:
            sheet.write(58, a, result[p.name]['land_cost_apl'], format1)
            line_total += result[p.name]['land_cost_apl']
            a+=1
        sheet.write(58, a, line_total, format1)

        #===================Cost of Construction======================

        sheet.write(60, 0, 'Cost of Construction', grey_black)
        a = 2
        line_total = 0
        for p in projects:
            sheet.write(60, a, result[p.name]['cost_of_construction_apl'], format1)
            line_total += result[p.name]['cost_of_construction_apl']
            a+=1
        sheet.write(60, a, line_total, format1)

        #===================Consultancy Other costs======================

        sheet.write(62, 0, 'Consultancy+Other Costs', grey_black)
        a = 2
        line_total = 0
        for p in projects:
            sheet.write(62, a, result[p.name]['consult_other_cost_apl'], format1)
            line_total += result[p.name]['consult_other_cost_apl']
            a+=1
        sheet.write(62, a, line_total, format1)


        #===================COst totals======================

        # sheet.write(33, 0, 'Consultancy+Other Costs', grey_black)
        a = 2
        line_total = 0
        for p in projects:
            sheet.write(64, a, result[p.name]['cop_div_cos_apl'], format1bsn)
            line_total += result[p.name]['cop_div_cos_apl']
            a+=1
        sheet.write(64, a, line_total, format1bsn)

        # sheet.merge_range(0, 0, 0, 2, "Project Profitability Report", format_main)
        sheet.merge_range(69, 2, 69, plen + 1, "Project Profitability / SFt", second_main)
        a = 2
        for p1 in projects:
            sheet.write(70, a, p1.name, format_main2)
            a += 1
        # sheet.write(3, a, 'Total', format_main2)

        sheet.write(70, 0, 'Description', second_mainl)
        # sheet.merge_range(4, 2, 4, plen+2, "AED", format11)

        # ============================Unsold====================================

        sheet.write(71, 0, 'Sales Price/SFt', format2)
        a = 2
        line_total = 0
        for p in projects:
            sheet.write(71, a, resullts[p.name]['sale_area_psft'], format1b)
            line_total += resullts[p.name]['sale_area_psft']
            a += 1
        # sheet.write(6, a, line_total, format1t)

        sheet.write(72, 0, 'Commissions (External+Internal) SFt', format2)
        a = 2
        line_total = 0
        for p in projects:
            sheet.write(72, a, resullts[p.name]['commissions_sft'], format1b)
            line_total += resullts[p.name]['commissions_sft']
            a += 1
        # sheet.write(7, a, line_total, format1)

        sheet.write(73, 0, 'FGR SFt', format2)
        a = 2
        line_total = 0
        for p in projects:
            sheet.write(73, a, result[p.name]['fgr_sft'], format1b)
            # line_total += result[p.name]['fgr_sft']
            a += 1
        # sheet.write(7, a, line_total, format1)

        sheet.write(74, 0, 'Sales Price Net of Commission & FGR', format2)
        a = 2
        line_total = 0
        for p in projects:
            sheet.write(74, a, resullts[p.name]['sale_area_psft'] - resullts[p.name]['commissions_sft'] - result[p.name]['fgr_sft'], format1b)
            # line_total += resullts[p.name]['sale_net_of_commissions']
            a += 1
        # sheet.write(8, a, line_total, format1b)
        #
        # sheet.write(45, 0, 'Cost of Product/Sft (Sold)', format2)
        # a = 2
        # line_total = 0
        # for p in projects:
        #     sheet.write(45, a, resullts[p.name]['cop_sold'], format1b)
        #     line_total += resullts[p.name]['cop_sold']
        #     a += 1
        # # sheet.write(10, a, line_total, format1t)
        #
        # sheet.write(46, 0, 'Cost of Product/Sft (Unsold)', format2)
        # a = 2
        # line_total = 0
        # for p in projects:
        #     sheet.write(46, a, resullts[p.name]['cop_unsold'], format1b)
        #     line_total += resullts[p.name]['cop_unsold']
        #     a += 1
        # # sheet.write(10, a, line_total, format1t)

        sheet.write(75, 0, 'Cost of Product/Sft (Sold + Unsold)', format2)
        a = 2
        line_total = 0
        for p in projects:
            sheet.write(75, a, resullts[p.name]['cop_sold_unsold'], format1b)
            line_total += resullts[p.name]['cop_sold_unsold']
            a += 1
        # sheet.write(10, a, line_total, format1t)

        sheet.write(76, 0, 'Gross Profit/Sft', format2)
        a = 2
        line_total = 0
        for p in projects:
            sheet.write(76, a, resullts[p.name]['gross_profit'], format1b)
            line_total += resullts[p.name]['gross_profit']
            a += 1
        # sheet.write(11, a, line_total, format1)

        sheet.write(77, 0, 'Gross Profit/SFt %', format2)
        a = 2
        line_total = 0
        for p in projects:
            sheet.write(77, a, str(round(resullts[p.name]['gross_profit_perc']))+' %', format1b)
            line_total += resullts[p.name]['gross_profit_perc']
            a += 1
        # sheet.write(12, a, line_total, format1b)

        sheet.write(78, 0, 'Gross Profit/SFt Net of Commission and FGR %', format2)
        a = 2
        line_total = 0
        for p in projects:
            # gross_profit_no_com_fgr = resullts[p.name]['gross_profit_perc']
            sheet.write(78, a, str(round(result[p.name]['gross_profit_no_fgr_com_perc']))+' %', format1bb)
            # line_total += result[p.name]['gross_profit_no_fgr_com_perc']
            a += 1
        # sheet.write(12, a, line_total, format1b)

        # sheet.write(54, 0, 'Commission (External+Internal)', grey_black)
        # a = 2
        # line_total = 0
        # for p in projects:
        #     sheet.write(54, a, resullts[p.name]['commissions'], format1bt)
        #     line_total += resullts[p.name]['commissions']
        #     a += 1
        # sheet.write(12, a, line_total, format1b)

        workbook.close()
        output.seek(0)
        generated_file = output.read()
        output.close()

        return generated_file

