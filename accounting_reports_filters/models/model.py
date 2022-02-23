# from openerp.osv import fields, orm, osv
from odoo import api, models, fields, _
from odoo.tools.misc import format_date
import json
import datetime

import io
from odoo.tools.misc import xlsxwriter


class ReportAccountAgedPayable(models.Model):
    _inherit = 'account.aged.payable'

    pdc = False
    payment_date_check = False


class ReportAccountAgedReceivable(models.Model):
    _inherit = 'account.aged.receivable'

    pdc = False
    payment_date_check = False

    archieve = fields.Boolean()


class AccountCashFlowReport(models.AbstractModel):
    _inherit = 'account.cash.flow.report'

    pdc = False
    payment_date_check = False


class assets_report(models.AbstractModel):
    _inherit = 'account.assets.report'

    pdc = False
    payment_date_check = False


class analytic_report(models.AbstractModel):
    _inherit = 'account.analytic.report'

    pdc = False
    payment_date_check = False


class generic_tax_report(models.AbstractModel):
    _inherit = 'account.generic.tax.report'

    pdc = False
    payment_date_check = False


class report_account_consolidated_journal(models.AbstractModel):
    _inherit = 'account.consolidated.journal'

    pdc = False
    payment_date_check = False


class AccountChartOfAccountReport(models.AbstractModel):
    _inherit = 'account.coa.report'

    pdc = False
    payment_date_check = False


class ReportAccountFinancialReport(models.Model):
    _inherit = 'account.financial.html.report'

    filter_pdc = False
    filter_payment_date_check = False

    @property
    def filter_pdc(self):
        if self.pdc:
            return True
        return super().filter_pdc

    @property
    def filter_payment_date_check(self):
        if self.payment_date_check:
            return True
        return super().filter_payment_date_check

    pdc = fields.Boolean('Allow PDC', default=False, help='display the PDC filter')
    payment_date_check = fields.Boolean('Payment Date', default=False, help='display the Payment Date filter')


class AccountMove(models.Model):
    _inherit = 'account.move'

    related_spa_id = fields.Many2one('sale.order', string='Related SPA/Booking')

    @api.model
    def get_installment_oqood_admin(self):
        invs = self.env['account.move'].search([])
        a = 1
        # for rec in invs:
        #     if rec.invoice_line_ids:
        #         so = rec.env['sale.order'].search([('property_id', '=', rec.property_id.id),('state', '!=', 'cancel')])
        #         if so:
        #             rec.related_spa_id = so[0].id
        #         print(a)
        #         a+=1

        query = """
            update account_move
            set related_spa_id = sale_order.id
            from sale_order
            WHERE account_move.property_id = sale_order.property_id and sale_order.state != 'cancel'
        """
        self.env.cr.execute(query)
        self.env.cr.commit()

        # rec.oqood_admin_string = 'Oqood Fee'
        # srs = rec.env['sale.rent.schedule'].search([('invc_id','=', rec.id)])
        # if srs:
        #     rec.related_spa_id = srs[0].sale_id.id

    @api.model
    def old_payments_add_spa_jv(self):
        ap = self.env['account.payment'].search([])
        a = 1
        for rec in ap:
            if rec.payment_type == 'inbound':
                if rec.journal_entry_id:
                    for move_line in rec.journal_entry_id:
                        move_line.related_spa_id = rec.spa_id.id
                        print(a)
                        a += 1
            if rec.payment_type == 'outbound':
                if rec.journal_entry_id:
                    for move_line in rec.journal_entry_id:
                        move_line.related_spa_id = rec.spa_payment_id.id
                        print(a)
                        a += 1

        # query = """
        #     update account_move
        #     set related_spa_id = account_payment.id
        #     from account_payment
        #     WHERE account_move.property_id = account_payment.property_id and sale_order.state != 'cancel'
        # """
        # self.env.cr.execute(query)
        # self.env.cr.commit()

        query = """
            update account_move_line
            set related_spa_id = account_move.related_spa_id
            from account_move
            WHERE account_move.id = account_move_line.move_id
        """
        self.env.cr.execute(query)

        query = """
            update account_move_line
            set spa_status = sale_order.state
            from sale_order
            WHERE sale_order.id = account_move_line.related_spa_id
        """
        self.env.cr.execute(query)
        self.env.cr.commit()

        query = """
            update account_move_line
            set receivable_status_id = sale_order.receivable_status_id
            from sale_order
            WHERE sale_order.id = account_move_line.related_spa_id
        """
        self.env.cr.execute(query)
        self.env.cr.commit()

        query = """
            update account_move_line
        set sale_type = sale_order.sale_type
        from sale_order
        WHERE sale_order.id = account_move_line.related_spa_id
        """
        self.env.cr.execute(query)
        self.env.cr.commit()


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    def update_archieve(self):
        count = 1
        records = self.env['account.move.line'].search([('date','<=',datetime.datetime.strptime('2019-06-30', '%Y-%m-%d'))])
        for rec in records:
            rec.archieve = True
            print(count)
            count += 1
    def update_date(self):
        moves = self.env['account.move.line'].search([('date', '=', False)])
        a = 1
        for rec in moves:
            rec.date = rec.move_id.date

    # @api.onchange('payment_id','move_id','related_spa_id')
    # def onchange_payment(self):
    #     for rec in self:
    #         rec.nationality_id = rec.partner_id.nationality_id.id
    #         rec.type_id = rec.property_id.type_id.id
    #         rec.related_spa_id = rec.payment_id.spa_id.id
    #         rec.asset_project_id = rec.move_id.asset_project_id.id
    #         rec.property_id = rec.move_id.property_id.id
    #         rec.receivable_status_id = rec.related_spa_id.receivable_status_id.id
    #         rec.spa_status = rec.related_spa_id.spa_status
    #         rec.sale_type = rec.related_spa_id.sale_type

    def update_records(self):
        moves = self.env['account.move.line'].search([('property_id', '!=', False)])
        a = 1
        for rec in moves:
            rec.nationality_id = rec.partner_id.nationality_id.id
            rec.type_id = rec.property_id.type_id.id
            rec.related_spa_id = rec.move_id.related_spa_id.id
            rec.write({'nationality_id': rec.partner_id.nationality_id.id})
            rec.write({'type_id': rec.property_id.type_id.id})
            rec.write({'type_id': rec.move_id.related_spa_id.id})
            rec.update({'nationality_id': rec.partner_id.nationality_id.id})
            rec.update({'type_id': rec.property_id.type_id.id})
            rec.update({'type_id': rec.move_id.related_spa_id.id})
            print(a)
            print(rec.nationality_id.name)
            print(rec.type_id.name)
            print(len(moves))
            a += 1

    @api.depends('partner_id', 'partner_id.nationality_id')
    def _compute_nationality(self):
        for rec in self:
            rec.nationality_id = rec.partner_id.nationality_id.id

    @api.depends('property_id', 'property_id.type_id')
    def compute_property(self):
        for rec in self:
            rec.type_id = rec.property_id.type_id.id

    nationality_id = fields.Many2one('res.country', readonly=True, store=True, compute='_compute_nationality',
                                     string="Nationality")
    journal_id = fields.Many2one('account.journal', readonly=True, store=True, related='move_id.journal_id',
                                 string="Journal")
    remarks = fields.Text(readonly=True, store=True, related='payment_id.remarks', string="Remarks")
    check_number = fields.Char(readonly=True, store=True, related='payment_id.check_number', string="Check Number")
    maturity_date = fields.Datetime('Maturity Date', readonly=True, store=True, related='payment_id.maturity_date')

    related_spa_id = fields.Many2one('sale.order', string='Related SPA/Booking', store=True)
    spa_status = fields.Selection([
        ('draft', 'Draft'),
        ('under_discount_approval', 'Under Approval'),
        ('tentative_booking', 'Tentative Booking'),
        ('review', 'Under Review'),
        ('under_cancellation', 'Booking Under Cancellation'),
        ('confirm_spa', 'Confirmed for SPA'),
        # ('approved', 'Approved'),
        ('booking_rejected', 'Rejected'),
        ('booking_cancel', 'Cancel'),

        ('spa_draft', 'Unconfirmed SPA'),
        # ('under_legal_review_print', 'Under Legal Review for Print'),
        # ('under_acc_verification_print', 'Under Accounts Verification for Print'),
        # ('under_confirmation_print', 'Under Confirmation for Print'),
        # ('unconfirmed_ok_for_print', 'Unconfirmed SPA OK for Print'),
        ('under_legal_review', 'Under Legal Review'),
        ('under_accounts_verification', 'Under Accounts Verification'),
        ('under_approval', 'Under Approval'),
        # ('under_spa_termination', 'Under SPA Termination'),
        # ('under_termination', 'Under Termination'),
        ('sale', 'Approved SPA'),
        ('sent', 'Quotation Sent'),
        ('refund_cancellation', 'Refund Cancellation'),
        ('rejected', 'Rejected'),
        ('under_sd_admin_review', 'Under SD Admin Review'),
        ('paid', 'Approved SPA - Paid'),
        ('done', 'Locked'),
        ('cancel', 'Cancelled'),
    ], string='SPA Status', readonly=True)
    receivable_status_id = fields.Many2one('receivable.status', 'Receivable Status',
                                           store=True)


    receivable_name = fields.Char(related='receivable_status_id.name', string='Receivable Status',
                                           store=True)
    project_name = fields.Char(related='asset_project_id.name', string='Receivable Status',
                                           store=True)
    property_name = fields.Char(related='property_id.name', string='Receivable Status',
                                           store=True)
    national_name = fields.Char(string='Nationality')
    archieve = fields.Boolean(string='Archieve')

    def update_nationality(self):
        records =  self.env['account.move.line'].search([('nationality_id','!=', False)])
        a = 1
        for rec in records:
            rec.national_name = rec.nationality_id.name
            print(a)
            a += 1

    @api.onchange('nationality_id')
    def onchange_nationality(self):
        for rec in self:
            rec.national_name = rec.nationality_id.name

    sale_type = fields.Selection([
        ('samana_sale', 'Samana Sale'),
        ('investor_sale', 'Investor Sale'),
    ], string='Sale Type', required=True, default='samana_sale')
    type_id = fields.Many2one(
        comodel_name='property.type',
        string='Property Type', compute='compute_property', store=True)

    parent_state = fields.Selection(related='move_id.state', string="Status", store=True, readonly=True)


class AccountingReport(models.AbstractModel):
    _inherit = 'account.accounting.report'

    archieve = fields.Boolean()


    def _get_move_line_fields(self, aml_alias="account_move_line"):
        return ', '.join('%s.%s' % (aml_alias, field) for field in (
            'id',
            'move_id',
            'name',
            'account_id',
            'journal_id',
            'company_id',
            'currency_id',
            'analytic_account_id',
            'display_type',
            'date',
            'debit',
            'credit',
            'balance',
            'archieve',
        ))

class AccountReport(models.AbstractModel):
    _inherit = 'account.report'

    filter_amount_due_greater = False
    filter_amount_due_less = False
    filter_project_wise = False
    filter_property_wise = False
    filter_receivable_wise = False
    filter_installment = False
    filter_pdc = None
    filter_payment_date_check = None


    @api.model
    def _get_options_domain(self, options):
        domain = [
            ('display_type', 'not in', ('line_section', 'line_note')),
        ]
        if options.get('multi_company', False):
            domain += [('company_id', 'in', self.env.companies.ids)]
        else:
            domain += [('company_id', '=', self.env.company.id)]
        domain += self._get_options_journals_domain(options)
        domain += self._get_options_date_domain(options)
        domain += self._get_options_analytic_domain(options)
        domain += self._get_options_partner_domain(options)
        domain += self._get_options_all_entries_domain(options)
        if not self._name == 'account.aged.receivable':
            domain.append(('archieve', '=', False))

        if options.get('installment'):
            invoices = self.env['account.move.line'].search(domain+ ['&',('move_id.invoice_type', '=', 'installment'),('move_id.related_installment_status', '=', 'confirm')])
            domain += ['|',('move_id.invoice_type', '=', 'installment'),('payment_id.reconciled_invoice_ids','in', invoices.ids)]
        # if self._name == 'account.aged.receivable':
        #     domain.append(('payment_id.state', '=', 'posted'))
        # options['unreconciled'] = True
        return domain

    @api.model
    def _get_options_date_domain(self, options):
        def create_date_domain(options_date):
            date_field = options_date.get('date_field', 'date')
            if options.get('payment_date_check'):
                date_field = 'payment_id.date'
            domain = [(date_field, '<=', options_date['date_to'])]
            if options_date['mode'] == 'range':
                strict_range = options_date.get('strict_range')
                if not strict_range:
                    domain += [
                        '|',
                        (date_field, '>=', options_date['date_from']),
                        ('account_id.user_type_id.include_initial_balance', '=', True)
                    ]
                else:
                    domain += [(date_field, '>=', options_date['date_from'])]
            return domain

        if not options.get('date'):
            return []
        return create_date_domain(options['date'])

    def print_xlsx_init(self, options):
        options['no_init'] = True
        return {
            'type': 'ir_actions_account_report_download',
            'data': {'model': self.env.context.get('model'),
                     'options': json.dumps(options),
                     'output_format': 'xlsx',
                     'financial_id': self.env.context.get('id'),
                     }
        }

    def _get_reports_buttons(self):
        if self.env.context.copy().get('model') == 'account.general.ledger':
            return [
                {'name': _('Print Preview'), 'sequence': 1, 'action': 'print_pdf', 'file_export_type': _('PDF')},
                {'name': _('Print Preview Initial'), 'sequence': 1, 'action': 'print_pdf_init',
                 'file_export_type': _('PDF')},
                {'name': _('Export (XLSX)'), 'sequence': 2, 'action': 'print_xlsx', 'file_export_type': _('XLSX')},
                {'name': _('Save'), 'sequence': 10, 'action': 'open_report_export_wizard'},
            ]
        elif self.env.context.copy().get('model') == 'account.partner.ledger':
            return [
                {'name': _('Print Preview'), 'sequence': 1, 'action': 'print_pdf', 'file_export_type': _('PDF')},
                {'name': _('Print Preview Initial'), 'sequence': 1, 'action': 'print_pdf_init',
                 'file_export_type': _('PDF')},
                {'name': _('Export (XLSX)'), 'sequence': 2, 'action': 'print_xlsx', 'file_export_type': _('XLSX')},
                {'name': _('Save'), 'sequence': 10, 'action': 'open_report_export_wizard'},
            ]
        else:
            return [
                {'name': _('Print Preview'), 'sequence': 1, 'action': 'print_pdf', 'file_export_type': _('PDF')},
                {'name': _('Export (XLSX)'), 'sequence': 2, 'action': 'print_xlsx', 'file_export_type': _('XLSX')},
                {'name': _('Save'), 'sequence': 10, 'action': 'open_report_export_wizard'},
            ]

    def print_pdf_init(self, options):
        options['no_init'] = True
        return {
            'type': 'ir_actions_account_report_download',
            'data': {'model': self.env.context.get('model'),
                     'options': json.dumps(options),
                     'output_format': 'pdf',
                     'financial_id': self.env.context.get('id'),
                     }
        }

    def get_xlsx(self, options, response=None):
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {
            'in_memory': True,
            'strings_to_formulas': False,
        })
        sheet = workbook.add_worksheet(self._get_report_name()[:31])

        date_default_col1_style = workbook.add_format(
            {'font_name': 'Arial', 'font_size': 12, 'font_color': '#666666', 'indent': 2, 'num_format': 'yyyy-mm-dd'})
        date_default_style = workbook.add_format(
            {'font_name': 'Arial', 'font_size': 12, 'font_color': '#666666', 'num_format': 'yyyy-mm-dd'})
        default_col1_style = workbook.add_format(
            {'font_name': 'Arial', 'font_size': 12, 'font_color': '#666666', 'indent': 2})
        default_style = workbook.add_format({'font_name': 'Arial', 'font_size': 12, 'font_color': '#666666'})
        title_style = workbook.add_format({'font_name': 'Arial', 'bold': True, 'bottom': 2})
        level_0_style = workbook.add_format(
            {'font_name': 'Arial', 'bold': True, 'font_size': 13, 'bottom': 6, 'font_color': '#666666'})
        level_1_style = workbook.add_format(
            {'font_name': 'Arial', 'bold': True, 'font_size': 13, 'bottom': 1, 'font_color': '#666666'})
        level_2_col1_style = workbook.add_format(
            {'font_name': 'Arial', 'bold': True, 'font_size': 12, 'font_color': '#666666', 'indent': 1})
        level_2_col1_total_style = workbook.add_format(
            {'font_name': 'Arial', 'bold': True, 'font_size': 12, 'font_color': '#666666'})
        level_2_style = workbook.add_format(
            {'font_name': 'Arial', 'bold': True, 'font_size': 12, 'font_color': '#666666'})
        level_3_col1_style = workbook.add_format(
            {'font_name': 'Arial', 'font_size': 12, 'font_color': '#666666', 'indent': 2})
        level_3_col1_total_style = workbook.add_format(
            {'font_name': 'Arial', 'bold': True, 'font_size': 12, 'font_color': '#666666', 'indent': 1})
        level_3_style = workbook.add_format({'font_name': 'Arial', 'font_size': 12, 'font_color': '#666666'})

        # Set the first column width to 50
        sheet.set_column(0, 0, 50)

        y_offset = 0
        headers, lines = self.with_context(no_format=True, print_mode=True, prefetch_fields=False)._get_table(options)

        # Add headers.
        for header in headers:
            x_offset = 0
            for column in header:
                column_name_formated = column.get('name', '').replace('<br/>', ' ').replace('&nbsp;', ' ')
                colspan = column.get('colspan', 1)
                if colspan == 1:
                    sheet.write(y_offset, x_offset, column_name_formated, title_style)
                else:
                    sheet.merge_range(y_offset, x_offset, y_offset, x_offset + colspan - 1, column_name_formated,
                                      title_style)
                x_offset += colspan
            y_offset += 1

        if options.get('hierarchy'):
            lines = self._create_hierarchy(lines, options)
        if options.get('selected_column'):
            lines = self._sort_lines(lines, options)

        # Add lines.
        for y in range(0, len(lines)):
            level = lines[y].get('level')
            if options.get('no_init'):
                if lines[y].get('id'):
                    if isinstance(lines[y].get('id'), str):
                        if lines[y].get('id')[:7] == 'initial':
                            continue
            if lines[y].get('caret_options'):
                style = level_3_style
                col1_style = level_3_col1_style
            elif level == 0:
                y_offset += 1
                style = level_0_style
                col1_style = style
            elif level == 1:
                style = level_1_style
                col1_style = style
            elif level == 2:
                style = level_2_style
                col1_style = 'total' in lines[y].get('class', '').split(
                    ' ') and level_2_col1_total_style or level_2_col1_style
            elif level == 3:
                style = level_3_style
                col1_style = 'total' in lines[y].get('class', '').split(
                    ' ') and level_3_col1_total_style or level_3_col1_style
            else:
                style = default_style
                col1_style = default_col1_style

            # write the first column, with a specific style to manage the indentation
            cell_type, cell_value = self._get_cell_type_value(lines[y])
            if cell_type == 'date':
                sheet.write_datetime(y + y_offset, 0, cell_value, date_default_col1_style)
            else:
                sheet.write(y + y_offset, 0, cell_value, col1_style)

            # write all the remaining cells
            for x in range(1, len(lines[y]['columns']) + 1):
                cell_type, cell_value = self._get_cell_type_value(lines[y]['columns'][x - 1])
                if cell_type == 'date':
                    sheet.write_datetime(y + y_offset, x + lines[y].get('colspan', 1) - 1, cell_value,
                                         date_default_style)
                else:
                    sheet.write(y + y_offset, x + lines[y].get('colspan', 1) - 1, cell_value, style)

        workbook.close()
        output.seek(0)
        generated_file = output.read()
        output.close()

        return generated_file

    @api.model
    def _init_filter_pdc(self, options, previous_options=None):
        if self.pdc:
            options['pdc'] = True
        else:
            options['pdc'] = False

    @api.model
    def _init_filter_payment_date_check(self, options, previous_options=None):
        if self.payment_date_check:
            options['payment_date_check'] = True
        else:
            options['payment_date_check'] = False

    @api.model
    def _init_filter_partner(self, options, previous_options=None):
        if not self.filter_partner:
            return

        options['partner'] = True
        options['partner_ids'] = previous_options and previous_options.get('partner_ids') or []
        options['asset_project_id'] = previous_options and previous_options.get('asset_project_id') or []
        options['property_id'] = previous_options and previous_options.get('property_id') or []
        options['nationality_id'] = previous_options and previous_options.get('nationality_id') or []
        options['ex_nationality_id'] = previous_options and previous_options.get('ex_nationality_id') or []
        options['related_spa_id'] = previous_options and previous_options.get('related_spa_id') or []
        options['receivable_status_id'] = previous_options and previous_options.get('receivable_status_id') or []
        options['ex_receivable_status_id'] = previous_options and previous_options.get('ex_receivable_status_id') or []
        options['type_id'] = previous_options and previous_options.get('type_id') or []
        options['partner_categories'] = previous_options and previous_options.get('partner_categories') or []
        selected_partner_ids = [int(partner) for partner in options['partner_ids']]
        selected_asset_project_id = [int(partner) for partner in options['asset_project_id']]
        selected_property_id = [int(partner) for partner in options['property_id']]
        selected_nationality_id = [int(partner) for partner in options['nationality_id']]
        selected_ex_nationality_id = [int(partner) for partner in options['ex_nationality_id']]
        selected_related_spa_id = [int(partner) for partner in options['related_spa_id']]
        selected_receivable_status_id = [int(partner) for partner in options['receivable_status_id']]
        selected_ex_receivable_status_id = [int(partner) for partner in options['ex_receivable_status_id']]
        selected_type_id = [int(partner) for partner in options['type_id']]
        selected_partners = selected_partner_ids and self.env['res.partner'].browse(selected_partner_ids) or self.env[
            'res.partner']
        selected_asset_project = selected_asset_project_id and self.env['account.asset.asset'].browse(
            selected_asset_project_id) or self.env['account.asset.asset']
        selected_property = selected_property_id and self.env['account.asset.asset'].browse(
            selected_property_id) or self.env['account.asset.asset']
        selected_nationality = selected_nationality_id and self.env['res.country'].browse(
            selected_nationality_id) or self.env['res.country']
        selected_ex_nationality = selected_ex_nationality_id and self.env['res.country'].browse(
            selected_ex_nationality_id) or self.env['res.country']
        selected_related_spa = selected_related_spa_id and self.env['sale.order'].browse(
            selected_related_spa_id) or self.env['sale.order']
        selected_receivable_status = selected_receivable_status_id and self.env['receivable.status'].browse(
            selected_receivable_status_id) or self.env['receivable.status']
        selected_ex_receivable_status = selected_ex_receivable_status_id and self.env['receivable.status'].browse(
            selected_ex_receivable_status_id) or self.env['receivable.status']
        selected_type = selected_type_id and self.env['property.type'].browse(
            selected_type_id) or self.env['property.type']
        options['selected_partner_ids'] = selected_partners.mapped('name')
        selected_partner_category_ids = [int(category) for category in options['partner_categories']]
        selected_partner_categories = selected_partner_category_ids and self.env['res.partner.category'].browse(
            selected_partner_category_ids) or self.env['res.partner.category']
        options['selected_partner_categories'] = selected_partner_categories.mapped('name')
        options['selected_asset_project_id'] = selected_asset_project.mapped('name')
        options['selected_property_id'] = selected_property.mapped('name')
        options['selected_nationality_id'] = selected_nationality.mapped('name')
        options['selected_ex_nationality_id'] = selected_ex_nationality.mapped('name')
        options['selected_related_spa_id'] = selected_related_spa.mapped('name')
        options['selected_receivable_status_id'] = selected_receivable_status.mapped('name')
        options['selected_ex_receivable_status_id'] = selected_ex_receivable_status.mapped('name')
        options['selected_type_id'] = selected_type.mapped('name')

    def _get_options_partner_domain(self, options):
        domain = []
        if options.get('partner_ids'):
            partner_ids = [int(partner) for partner in options['partner_ids']]
            domain.append(('partner_id', 'in', partner_ids))
        if options.get('partner_categories'):
            partner_category_ids = [int(category) for category in options['partner_categories']]
            domain.append(('partner_id.category_id', 'in', partner_category_ids))
        if options.get('asset_project_id'):
            asset_project_id = [int(category) for category in options['asset_project_id']]
            domain.append(('asset_project_id', 'in', asset_project_id))
        if options.get('property_id'):
            property_id = [int(category) for category in options['property_id']]
            domain.append(('property_id', 'in', property_id))
        if options.get('nationality_id'):
            nationality_id = [int(category) for category in options['nationality_id']]
            domain.append(('nationality_id', 'in', nationality_id))
        if options.get('ex_nationality_id'):
            ex_nationality_id = [int(category) for category in options['ex_nationality_id']]
            domain.append(('nationality_id', 'not in', ex_nationality_id))
        if options.get('related_spa_id'):
            related_spa_id = [int(category) for category in options['related_spa_id']]
            domain.append(('related_spa_id', 'in', related_spa_id))
        if options.get('receivable_status_id'):
            receivable_status_id = [int(category) for category in options['receivable_status_id']]
            domain.append(('receivable_status_id', 'in', receivable_status_id))
        if options.get('ex_receivable_status_id'):
            ex_receivable_status_id = [int(category) for category in options['ex_receivable_status_id']]
            domain.append(('receivable_status_id', 'not in', ex_receivable_status_id))
        if options.get('type_id'):
            type_id = [int(category) for category in options['type_id']]
            domain.append(('type_id', 'in', type_id))
        return domain

    @api.model
    def _get_options_all_entries_domain(self, options):
        if not options.get('all_entries'):
            domain = [('move_id.state', '=', 'posted')]
        else:
            domain = [('move_id.state', '!=', 'cancel')]
        if options.get('pdc'):
            domain = []
        if options.get('amount_due_greater'):
            domain += [('balance', '>', 0)]
        if options.get('amount_due_less'):
            domain += [('balance', '<', 0)]
        return domain

    def _set_context(self, options):
        """This method will set information inside the context based on the options dict as some options need to be in context for the query_get method defined in account_move_line"""
        ctx = self.env.context.copy()
        if options.get('date') and options['date'].get('date_from'):
            ctx['date_from'] = options['date']['date_from']
        if options.get('date'):
            ctx['date_to'] = options['date'].get('date_to') or options['date'].get('date')
        if options.get('all_entries') is not None:
            ctx['state'] = options.get('all_entries') and 'all' or 'posted'
        if options.get('journals'):
            ctx['journal_ids'] = [j.get('id') for j in options.get('journals') if j.get('selected')]
        if options.get('analytic_accounts'):
            ctx['analytic_account_ids'] = self.env['account.analytic.account'].browse(
                [int(acc) for acc in options['analytic_accounts']])
        if options.get('analytic_tags'):
            ctx['analytic_tag_ids'] = self.env['account.analytic.tag'].browse(
                [int(t) for t in options['analytic_tags']])
            ctx['partner_ids'] = self.env['account.analytic.tag'].browse([int(t) for t in options['analytic_tags']])
        if options.get('partner_ids'):
            ctx['partner_ids'] = self.env['res.partner'].browse([int(partner) for partner in options['partner_ids']])
        if options.get('asset_project_id'):
            ctx['asset_project_id'] = self.env['account.asset.asset'].browse(
                [int(project) for project in options['asset_project_id']])
        if options.get('property_id'):
            ctx['property_id'] = self.env['account.asset.asset'].browse(
                [int(project) for project in options['property_id']])
        if options.get('nationality_id'):
            ctx['nationality_id'] = self.env['res.country'].browse(
                [int(project) for project in options['nationality_id']])
        if options.get('ex_nationality_id'):
            ctx['ex_nationality_id'] = self.env['res.country'].browse(
                [int(project) for project in options['ex_nationality_id']])
        if options.get('related_spa_id'):
            ctx['related_spa_id'] = self.env['sale.order'].browse(
                [int(project) for project in options['related_spa_id']])
        if options.get('receivable_status_id'):
            ctx['receivable_status_id'] = self.env['receivable.status'].browse(
                [int(project) for project in options['receivable_status_id']])
        if options.get('ex_receivable_status_id'):
            ctx['ex_receivable_status_id'] = self.env['receivable.status'].browse(
                [int(project) for project in options['ex_receivable_status_id']])
        if options.get('type_id'):
            ctx['type_id'] = self.env['property.type'].browse([int(project) for project in options['type_id']])
        if options.get('partner_categories'):
            ctx['partner_categories'] = self.env['res.partner.category'].browse(
                [int(category) for category in options['partner_categories']])
        if not ctx.get('allowed_company_ids') or not options.get('multi_company'):
            """Contrary to the generic multi_company strategy,
            If we have not specified multiple companies, we only use
            the user company for account reports.

            To do so, we set the allowed_company_ids to only the main current company
            so that self.env.company == self.env.companies
            """
            ctx['allowed_company_ids'] = self.env.company.ids
        return ctx

    @api.model
    def _get_options_analytic_domain(self, options):
        domain = []
        if options.get('analytic_accounts'):
            analytic_account_ids = [int(acc) for acc in options['analytic_accounts']]
            domain.append(('analytic_account_id', 'in', analytic_account_ids))
        if options.get('analytic_tags'):
            analytic_tag_ids = [int(tag) for tag in options['analytic_tags']]
            domain.append(('analytic_tag_ids', 'in', analytic_tag_ids))
        if options.get('partner_ids'):
            partner_ids = [int(tag) for tag in options['partner_ids']]
            domain.append(('partner_id', 'in', partner_ids))
        if options.get('asset_project_id'):
            asset_project_id = [int(tag) for tag in options['asset_project_id']]
            domain.append(('asset_project_id', 'in', asset_project_id))
        if options.get('property_id'):
            property_id = [int(tag) for tag in options['property_id']]
            domain.append(('property_id', 'in', property_id))
        if options.get('account_id'):
            account_id = [int(tag) for tag in options['account_id']]
            domain.append(('account_id', 'in', account_id))
        return domain

    def open_action(self, options, domain):
        assert isinstance(domain, (list, tuple))
        domain += [('date', '>=', options.get('date').get('date_from')),
                   ('date', '<=', options.get('date').get('date_to'))]
        if not options.get('all_entries'):
            domain += [('move_id.state', '=', 'posted')]
        if not options.get('amount_due_greater'):
            domain += [('balance', '>', 0)]
        if not options.get('amount_due_less'):
            domain += [('balance', '<', 0)]
        ctx = self.env.context.copy()
        ctx.update({'search_default_account': 1, 'search_default_groupby_date': 1})

        return {
            'type': 'ir.actions.act_window',
            'name': _('Journal Items for Tax Audit'),
            'res_model': 'account.move.line',
            'views': [[self.env.ref('account.view_move_line_tax_audit_tree').id, 'list'], [False, 'form']],
            'domain': domain,
            'context': ctx,
        }

    @api.model
    def _get_options(self, previous_options=None):
        # Create default options.
        options = {
            'unfolded_lines': previous_options and previous_options.get('unfolded_lines') or [],
        }

        # Multi-company is there for security purpose and can't be disabled by a filter.
        if self.filter_multi_company:
            if self._context.get('allowed_company_ids'):
                # Retrieve the companies through the multi-companies widget.
                companies = self.env['res.company'].browse(self._context['allowed_company_ids'])
            else:
                # When called from testing files, 'allowed_company_ids' is missing.
                # Then, give access to all user's companies.
                companies = self.env.companies
            if len(companies) > 1:
                options['multi_company'] = [
                    {'id': c.id, 'name': c.name} for c in companies
                ]

        # Call _init_filter_date/_init_filter_comparison because the second one must be called after the first one.
        if self.filter_date:
            self._init_filter_date(options, previous_options=previous_options)
        if self.filter_comparison:
            self._init_filter_comparison(options, previous_options=previous_options)
        if self.filter_analytic:
            options['analytic'] = self.filter_analytic

        filter_list = [attr
                       for attr in dir(self)
                       if (attr.startswith('filter_') or attr.startswith('order_'))
                       and attr not in ('filter_date', 'filter_comparison', 'filter_multi_company')
                       and len(attr) > 7
                       and not callable(getattr(self, attr))]
        filter_list.append('filter_partner_ids')
        filter_list.append('filter_asset_project_id')
        filter_list.append('filter_property_id')
        filter_list.append('filter_account_id')
        for filter_key in filter_list:
            options_key = filter_key[7:]
            init_func = getattr(self, '_init_%s' % filter_key, None)
            if init_func:
                init_func(options, previous_options=previous_options)
            else:
                filter_opt = getattr(self, filter_key, None)
                if filter_opt is not None:
                    if previous_options and options_key in previous_options:
                        options[options_key] = previous_options[options_key]
                    else:
                        options[options_key] = filter_opt
        # if previous_options and previous_options.get('pdc'):
        #     options['pdc'] = previous_options.get('pdc')
        if previous_options and previous_options.get('partner_ids'):
            options['partner_ids'] = previous_options.get('partner_ids')
        if previous_options and previous_options.get('asset_project_id'):
            options['asset_project_id'] = previous_options.get('asset_project_id')
        if previous_options and previous_options.get('property_id'):
            options['property_id'] = previous_options.get('property_id')
        if previous_options and previous_options.get('account_id'):
            options['account_id'] = previous_options.get('account_id')
        return options

    # @api.model
    # def _get_options(self, previous_options=None):
    #     # Create default options.
    #     options = {
    #         'unfolded_lines': previous_options and previous_options.get('unfolded_lines') or [],
    #     }
    #
    #     # Multi-company is there for security purpose and can't be disabled by a filter.
    #     if self.filter_multi_company:
    #         if self._context.get('allowed_company_ids'):
    #             # Retrieve the companies through the multi-companies widget.
    #             companies = self.env['res.company'].browse(self._context['allowed_company_ids'])
    #         else:
    #             # When called from testing files, 'allowed_company_ids' is missing.
    #             # Then, give access to all user's companies.
    #             companies = self.env.companies
    #         if len(companies) > 1:
    #             options['multi_company'] = [
    #                 {'id': c.id, 'name': c.name} for c in companies
    #             ]
    #
    #     # Call _init_filter_date/_init_filter_comparison because the second one must be called after the first one.
    #     if self.filter_date:
    #         self._init_filter_date(options, previous_options=previous_options)
    #     if self.filter_comparison:
    #         self._init_filter_comparison(options, previous_options=previous_options)
    #
    #     filter_list = [attr for attr in dir(self)
    #                    if (attr.startswith('filter_') or attr.startswith('order_')) and attr not in ('filter_date', 'filter_comparison', 'filter_multi_company') and len(attr) > 7 and not callable(getattr(self, attr))]
    #     filter_list.append('filter_partner_ids')
    #     filter_list.append('filter_asset_project_id')
    #     filter_list.append('filter_property_id')
    #     filter_list.append('filter_account_id')
    #     for filter_key in filter_list:
    #         options_key = filter_key[7:]
    #         init_func = getattr(self, '_init_%s' % filter_key, None)
    #         if init_func:
    #             init_func(options, previous_options=previous_options)
    #         else:
    #             filter_opt = getattr(self, filter_key, None)
    #             if filter_opt is not None:
    #                 if previous_options and options_key in previous_options:
    #                     options[options_key] = previous_options[options_key]
    #                 else:
    #                     options[options_key] = filter_opt
    #     if previous_options and previous_options.get('partner_ids'):
    #         options['partner_ids'] = previous_options.get('partner_ids')
    #     if previous_options and previous_options.get('asset_project_id'):
    #         options['asset_project_id'] = previous_options.get('asset_project_id')
    #     if previous_options and previous_options.get('property_id'):
    #         options['property_id'] = previous_options.get('property_id')
    #     if previous_options and previous_options.get('account_id'):
    #         options['account_id'] = previous_options.get('account_id')
    #     return options

    def get_report_informations(self, options):
        '''
        return a dictionary of informations that will be needed by the js widget, manager_id, footnotes, html of report and searchview, ...
        '''
        options_new = options
        options = self._get_options(options)

        searchview_dict = {'options': options, 'context': self.env.context}
        # Check if report needs analytic
        if options.get('analytic_accounts') is not None:
            options['selected_analytic_account_names'] = [self.env['account.analytic.account'].browse(int(account)).name
                                                          for account in options['analytic_accounts']]
            if options.get('partner_ids'):
                options['partner_ids'] = [self.env['res.partner'].browse(int(partner)).id for partner in
                                          options['partner_ids']]

                options['selected_partner_ids'] = [self.env['res.partner'].browse(int(partner)).name for partner in
                                                   options['partner_ids'] or []]
            if options.get('asset_project_id'):
                options['asset_project_id'] = [self.env['account.asset.asset'].browse(int(partner)).id for partner in
                                               options['asset_project_id']]
            if options.get('property_id'):
                options['property_id'] = [self.env['account.asset.asset'].browse(int(partner)).id for partner in
                                          options['property_id']]
            if options.get('account_id'):
                options['account_id'] = [self.env['account.account'].browse(int(partner)).id for partner in
                                         options['account_id']]

        if options.get('analytic_tags') is not None:
            options['selected_analytic_tag_names'] = [self.env['account.analytic.tag'].browse(int(tag)).name for tag in
                                                      options['analytic_tags']]
        if options.get('partner'):
            options['selected_partner_ids'] = [self.env['res.partner'].browse(int(partner)).name for partner in
                                               options['partner_ids']]
            options['selected_asset_project_id'] = [self.env['account.asset.asset'].browse(int(partner)).name for
                                                    partner in options['asset_project_id']]
            options['selected_property_id'] = [self.env['account.asset.asset'].browse(int(partner)).name for partner in
                                               options['property_id']]
            options['selected_nationality_id'] = [self.env['res.country'].browse(int(partner)).name for partner in
                                                  options['nationality_id']]
            options['selected_ex_nationality_id'] = [self.env['res.country'].browse(int(partner)).name for partner in
                                                     options['ex_nationality_id']]
            options['selected_related_spa_id'] = [self.env['sale.order'].browse(int(partner)).name for partner in
                                                  options['related_spa_id']]
            options['selected_receivable_status_id'] = [self.env['receivable.status'].browse(int(partner)).name for
                                                        partner in options['receivable_status_id']]
            options['selected_ex_receivable_status_id'] = [self.env['receivable.status'].browse(int(partner)).name for
                                                           partner in options['ex_receivable_status_id']]
            options['selected_type_id'] = [self.env['property.type'].browse(int(partner)).name for partner in
                                           options['type_id']]
            options['selected_partner_categories'] = [self.env['res.partner.category'].browse(int(category)).name for
                                                      category in (options.get('partner_categories') or [])]

        # Check whether there are unposted entries for the selected period or not (if the report allows it)
        if options.get('date') and options.get('all_entries') is not None:
            date_to = options['date'].get('date_to') or options['date'].get('date') or fields.Date.today()
            period_domain = [('state', '=', 'draft'), ('date', '<=', date_to)]
            options['unposted_in_period'] = bool(self.env['account.move'].search_count(period_domain))

        if options.get('journals'):
            journals_selected = set(journal['id'] for journal in options['journals'] if journal.get('selected'))
            for journal_group in self.env['account.journal.group'].search([('company_id', '=', self.env.company.id)]):
                if journals_selected and journals_selected == set(self._get_filter_journals().ids) - set(
                        journal_group.excluded_journal_ids.ids):
                    options['name_journal_group'] = journal_group.name
                    break

        report_manager = self._get_report_manager(options)
        info = {'options': options,
                'context': self.env.context,
                'report_manager_id': report_manager.id,
                'footnotes': [{'id': f.id, 'line': f.line, 'text': f.text} for f in report_manager.footnotes_ids],
                'buttons': self._get_reports_buttons_in_sequence(),
                'main_html': self.get_html(options),
                'searchview_html': self.env['ir.ui.view']._render_template(
                    self._get_templates().get('search_template', 'account_report.search_template'),
                    values=searchview_dict),
                }
        return info


class ReportAccountAgedPartner(models.AbstractModel):
    _inherit = "account.aged.partner"

    asset_project_id = fields.Many2one('account.asset.asset', domain="[('project', '=', True)]")
    property_id = fields.Many2one('account.asset.asset')
    nationality_id = fields.Many2one('res.country')
    ex_nationality_id = fields.Many2one('res.country')
    related_spa_id = fields.Many2one('sale.order', string='Related SPA/Booking')
    receivable_status_id = fields.Many2one('receivable.status', string='Receivable Status')
    type_id = fields.Many2one('property.type')
    project_name = fields.Char(group_operator='max')
    property_name = fields.Char(group_operator='max')
    receivable_status_name = fields.Char(group_operator='max')
    nationality_name = fields.Char(group_operator='max')
    archieve = fields.Boolean()

    # nationality_name = fields.Char(group_operator='max')
    # type_name = fields.Char(group_operator='max')



    def _get_hierarchy_details(self, options):
        self
        if options['project_wise']:
            return [
                self._hierarchy_level('asset_project_id', foldable=True, namespan=2),
                self._hierarchy_level('id'),
            ]
        elif options['property_wise']:
            return [
                self._hierarchy_level('property_id', foldable=True, namespan=2),
                self._hierarchy_level('id'),
            ]
        elif options['receivable_wise']:
            return [
                self._hierarchy_level('receivable_status_id', foldable=True, namespan=2),
                self._hierarchy_level('id'),
            ]
        else:
            return [
                self._hierarchy_level('partner_id', foldable=True, namespan=2),
                self._hierarchy_level('id'),
            ]



    def _format_receivable_status_id_line(self, res, value_dict, options):
        res['name'] = value_dict['receivable_status_name'][:128] if value_dict['receivable_status_name'] else _('Unknown Receivable Status')
        res['trust'] = value_dict['partner_trust']

    def _format_asset_project_id_line(self, res, value_dict, options):
        res['name'] = value_dict['project_name'][:128] if value_dict['project_name'] else _('Unknown Projects')
        res['trust'] = value_dict['partner_trust']

    def _format_property_id_line(self, res, value_dict, options):
        res['name'] = value_dict['partner_name'][:128] if value_dict['partner_name'] else _('Unknown Properties')
        res['trust'] = value_dict['partner_trust']


    @api.model
    def _get_column_details(self, options):
        self
        return [
            self._header_column(),
            self._field_column('report_date'),
            self._field_column('journal_code', name=_("Journal")),
            self._field_column('project_name', name="Project"),
            self._field_column('property_name', name="Property"),
            self._field_column('receivable_status_name', name="Receivable Status"),
            self._field_column('nationality_name', name="Nationality"),
            self._field_column('account_name', name="Account"),
            self._field_column('expected_pay_date'),
            self._field_column('period0', name=_("As of: %s") % format_date(self.env, options['date']['date_to'])),
            self._field_column('period1', sortable=True),
            self._field_column('period2', sortable=True),
            self._field_column('period3', sortable=True),
            self._field_column('period4', sortable=True),
            self._field_column('period5', sortable=True),
            self._custom_column(  # Avoid doing twice the sub-select in the view
                name=_('Total'),
                classes=['number'],
                formatter=self.format_value,
                getter=(
                    lambda v: v['period0'] + v['period1'] + v['period2'] + v['period3'] + v['period4'] + v['period5']),
                sortable=True,
            ),
        ]

    @api.model
    def _get_sql(self):
        options = self.env.context['report_options']
        if self._name == 'account.aged.receivable':
            query = ("""
                    SELECT
                        {move_line_fields},
                        account_move_line.partner_id AS partner_id,
                        account_move_line.asset_project_id AS asset_project_id,
                        account_move_line.property_id AS property_id,
                        account_move_line.nationality_id AS nationality_id,
                        account_move_line.nationality_id AS ex_nationality_id,
                        account_move_line.related_spa_id AS related_spa_id,
                        account_move_line.receivable_status_id AS receivable_status_id,
                        account_move_line.receivable_name AS receivable_status_name,
                        account_move_line.national_name AS nationality_name,
                        account_move_line.project_name AS project_name,
                        account_move_line.property_name AS property_name,
                        account_move_line.receivable_status_id AS ex_receivable_status_id,
                        account_move_line.type_id AS type_id,
                        partner.name AS partner_name,
                        COALESCE(trust_property.value_text, 'normal') AS partner_trust,
                        COALESCE(account_move_line.currency_id, journal.currency_id) AS report_currency_id,
                        account_move_line.payment_id AS payment_id,
                        COALESCE(account_move_line.date_maturity, account_move_line.date) AS report_date,
                        account_move_line.expected_pay_date AS expected_pay_date,
                        move.move_type AS move_type,
                        move.name AS move_name,
                        journal.code AS journal_code,
                        account.name AS account_name,
                        account.code AS account_code,""" + ','.join([("""
                        CASE WHEN period_table.period_index = {i}
                        THEN %(sign)s * ROUND((
                            account_move_line.balance
                        ) * currency_table.rate, currency_table.precision)
                        ELSE 0 END AS period{i}""").format(i=i) for i in range(6)]) + """
                    FROM account_move_line
                    JOIN account_move move ON account_move_line.move_id = move.id
                    JOIN account_journal journal ON journal.id = account_move_line.journal_id
                    JOIN account_account account ON account.id = account_move_line.account_id
                    JOIN res_partner partner ON partner.id = account_move_line.partner_id
                    LEFT JOIN ir_property trust_property ON (
                        trust_property.res_id = 'res.partner,'|| account_move_line.partner_id
                        AND trust_property.name = 'trust'
                        AND trust_property.company_id = account_move_line.company_id
                    )
                    JOIN {currency_table} ON currency_table.company_id = account_move_line.company_id
                    LEFT JOIN LATERAL (
                        SELECT part.amount, part.debit_move_id
                        FROM account_partial_reconcile part
                        WHERE part.max_date <= %(date)s
                    ) part_debit ON part_debit.debit_move_id = account_move_line.id
                    LEFT JOIN LATERAL (
                        SELECT part.amount, part.credit_move_id
                        FROM account_partial_reconcile part
                        WHERE part.max_date <= %(date)s
                    ) part_credit ON part_credit.credit_move_id = account_move_line.id
                    JOIN {period_table} ON (
                        period_table.date_start IS NULL
                        OR COALESCE(account_move_line.date_maturity, account_move_line.date) <= DATE(period_table.date_start)
                    )
                    AND (
                        period_table.date_stop IS NULL
                        OR COALESCE(account_move_line.date_maturity, account_move_line.date) >= DATE(period_table.date_stop)
                    )
                    WHERE account.internal_type = %(account_type)s
                    GROUP BY account_move_line.id, partner.id, trust_property.id, journal.id, move.id, account.id,
                             period_table.period_index, currency_table.rate, currency_table.precision
                """).format(
                move_line_fields=self._get_move_line_fields('account_move_line'),
                currency_table=self.env['res.currency']._get_query_currency_table(options),
                period_table=self._get_query_period_table(options),
            )
            params = {
                'account_type': options['filter_account_type'],
                'sign': 1 if options['filter_account_type'] == 'receivable' else -1,
                'date': options['date']['date_to'],
            }
            return self.env.cr.mogrify(query, params).decode(self.env.cr.connection.encoding)
        else:

            query = ("""
                                SELECT
                                    {move_line_fields},
                                    account_move_line.partner_id AS partner_id,
                                    account_move_line.asset_project_id AS asset_project_id,
                                    account_move_line.property_id AS property_id,
                                    account_move_line.nationality_id AS nationality_id,
                                    account_move_line.nationality_id AS ex_nationality_id,
                                    account_move_line.related_spa_id AS related_spa_id,
                                    account_move_line.receivable_status_id AS receivable_status_id,
                                    account_move_line.receivable_name AS receivable_status_name,
                                    account_move_line.national_name AS nationality_name,
                                    account_move_line.project_name AS project_name,
                                    account_move_line.property_name AS property_name,
                                    account_move_line.receivable_status_id AS ex_receivable_status_id,
                                    account_move_line.type_id AS type_id,
                                    partner.name AS partner_name,
                                    COALESCE(trust_property.value_text, 'normal') AS partner_trust,
                                    COALESCE(account_move_line.currency_id, journal.currency_id) AS report_currency_id,
                                    account_move_line.payment_id AS payment_id,
                                    COALESCE(account_move_line.date_maturity, account_move_line.date) AS report_date,
                                    account_move_line.expected_pay_date AS expected_pay_date,
                                    move.move_type AS move_type,
                                    move.name AS move_name,
                                    journal.code AS journal_code,
                                    account.name AS account_name,
                                    account.code AS account_code,""" + ','.join([("""
                                    CASE WHEN period_table.period_index = {i}
                                    THEN %(sign)s * ROUND((
                                        account_move_line.balance - COALESCE(SUM(part_debit.amount), 0) + COALESCE(SUM(part_credit.amount), 0)
                                    ) * currency_table.rate, currency_table.precision)
                                    ELSE 0 END AS period{i}""").format(i=i) for i in range(6)]) + """
                                FROM account_move_line
                                JOIN account_move move ON account_move_line.move_id = move.id
                                JOIN account_journal journal ON journal.id = account_move_line.journal_id
                                JOIN account_account account ON account.id = account_move_line.account_id
                                JOIN res_partner partner ON partner.id = account_move_line.partner_id
                                LEFT JOIN ir_property trust_property ON (
                                    trust_property.res_id = 'res.partner,'|| account_move_line.partner_id
                                    AND trust_property.name = 'trust'
                                    AND trust_property.company_id = account_move_line.company_id
                                )
                                JOIN {currency_table} ON currency_table.company_id = account_move_line.company_id
                                LEFT JOIN LATERAL (
                                    SELECT part.amount, part.debit_move_id
                                    FROM account_partial_reconcile part
                                    WHERE part.max_date <= %(date)s
                                ) part_debit ON part_debit.debit_move_id = account_move_line.id
                                LEFT JOIN LATERAL (
                                    SELECT part.amount, part.credit_move_id
                                    FROM account_partial_reconcile part
                                    WHERE part.max_date <= %(date)s
                                ) part_credit ON part_credit.credit_move_id = account_move_line.id
                                JOIN {period_table} ON (
                                    period_table.date_start IS NULL
                                    OR COALESCE(account_move_line.date_maturity, account_move_line.date) <= DATE(period_table.date_start)
                                )
                                AND (
                                    period_table.date_stop IS NULL
                                    OR COALESCE(account_move_line.date_maturity, account_move_line.date) >= DATE(period_table.date_stop)
                                )
                                WHERE account.internal_type = %(account_type)s
                                GROUP BY account_move_line.id, partner.id, trust_property.id, journal.id, move.id, account.id,
                                         period_table.period_index, currency_table.rate, currency_table.precision
                            """).format(
                move_line_fields=self._get_move_line_fields('account_move_line'),
                currency_table=self.env['res.currency']._get_query_currency_table(options),
                period_table=self._get_query_period_table(options),
            )
            params = {
                'account_type': options['filter_account_type'],
                'sign': 1 if options['filter_account_type'] == 'receivable' else -1,
                'date': options['date']['date_to'],
            }
            return self.env.cr.mogrify(query, params).decode(self.env.cr.connection.encoding)


class AccountGeneralLedgerReport(models.AbstractModel):
    _inherit = 'account.general.ledger'

    filter_amount_due_greater = None
    filter_amount_due_less = None
    filter_installment = None
    filter_project_wise = None
    filter_property_wise = None
    filter_receivable_wise = None
    pdc = False
    payment_date_check = False

    @api.model
    def _get_general_ledger_lines(self, options, line_id=None):
        ''' Get lines for the whole report or for a specific line.
        :param options: The report options.
        :return:        A list of lines, each one represented by a dictionary.
        '''
        lines = []
        aml_lines = []
        options_list = self._get_options_periods_list(options)
        unfold_all = options.get('unfold_all') or (self._context.get('print_mode') and not options['unfolded_lines'])
        date_from = fields.Date.from_string(options['date']['date_from'])
        company_currency = self.env.company.currency_id

        expanded_account = line_id and self.env['account.account'].browse(int(line_id[8:]))
        accounts_results, taxes_results = self._do_query(options_list, expanded_account=expanded_account)

        total_debit = total_credit = total_balance = 0.0
        check = True
        newcumulated_balance = 0.0
        try:
            accounts_results = sorted(accounts_results, key=lambda i: i[1][0]['sum']['balance'], reverse=True)
        except:
            print('sum')
        for account, periods_results in accounts_results:
            # No comparison allowed in the General Ledger. Then, take only the first period.
            results = periods_results[0]

            is_unfolded = 'account_%s' % account.id in options['unfolded_lines']

            # account.account record line.
            account_sum = results.get('sum', {})
            account_un_earn = results.get('unaffected_earnings', {})

            # Check if there is sub-lines for the current period.
            max_date = account_sum.get('max_date')
            has_lines = max_date and max_date >= date_from or False

            amount_currency = account_sum.get('amount_currency', 0.0) + account_un_earn.get('amount_currency', 0.0)
            debit = account_sum.get('debit', 0.0) + account_un_earn.get('debit', 0.0)
            credit = account_sum.get('credit', 0.0) + account_un_earn.get('credit', 0.0)
            balance = account_sum.get('balance', 0.0) + account_un_earn.get('balance', 0.0)

            lines.append(
                self._get_account_title_line(options, account, amount_currency, debit, credit, balance, has_lines))

            total_debit += debit
            total_credit += credit
            total_balance += balance

            if has_lines and (unfold_all or is_unfolded):
                # Initial balance line.
                account_init_bal = results.get('initial_balance', {})
                cumulated_balance = newcumulated_balance
                if not options.get('no_init'):
                    cumulated_balance = account_init_bal.get('balance', 0.0) + account_un_earn.get('balance', 0.0)

                lines.append(self._get_initial_balance_line(
                    options, account,
                    account_init_bal.get('amount_currency', 0.0) + account_un_earn.get('amount_currency', 0.0),
                    account_init_bal.get('debit', 0.0) + account_un_earn.get('debit', 0.0),
                    account_init_bal.get('credit', 0.0) + account_un_earn.get('credit', 0.0),
                    cumulated_balance,
                ))

                # account.move.line record lines.
                amls = results.get('lines', [])

                load_more_remaining = len(amls)
                load_more_counter = self._context.get('print_mode') and load_more_remaining or self.MAX_LINES
                for aml in amls:
                    # Don't show more line than load_more_counter.
                    if options.get('no_init') and check:
                        check = False
                        cumulated_balance = 0.0
                    if load_more_counter == 0:
                        break

                    cumulated_balance += aml['balance']
                    newcumulated_balance = cumulated_balance
                    lines.append(self._get_aml_line(options, account, aml, company_currency.round(cumulated_balance)))

                    load_more_remaining -= 1
                    load_more_counter -= 1
                    aml_lines.append(aml['id'])

                if load_more_remaining > 0:
                    # Load more line.
                    lines.append(self._get_load_more_line(
                        options, account,
                        self.MAX_LINES,
                        load_more_remaining,
                        cumulated_balance,
                    ))

                if self.env.company.totals_below_sections:
                    # Account total line.
                    lines.append(self._get_account_total_line(
                        options, account,
                        account_sum.get('amount_currency', 0.0),
                        account_sum.get('debit', 0.0),
                        account_sum.get('credit', 0.0),
                        account_sum.get('balance', 0.0),
                    ))

        if not line_id:
            # Report total line.
            lines.append(self._get_total_line(
                options,
                total_debit,
                total_credit,
                company_currency.round(total_balance),
            ))

            # Tax Declaration lines.
            journal_options = self._get_options_journals(options)
            if len(journal_options) == 1 and journal_options[0]['type'] in ('sale', 'purchase'):
                lines += self._get_tax_declaration_lines(
                    options, journal_options[0]['type'], taxes_results
                )
        if self.env.context.get('aml_only'):
            return aml_lines
        return lines

    @api.model
    def _get_tax_declaration_lines(self, options, journal_type, taxes_results):
        lines = [{
            'id': 0,
            'name': _('Tax Declaration'),
            'columns': [{'name': ''}],
            'colspan': self.user_has_groups('base.group_multi_currency') and 7 or 6,
            'level': 1,
            'unfoldable': False,
            'unfolded': False,
        }, {
            'id': 0,
            'name': _('Name'),
            'columns': [{'name': v} for v in ['', _('Base Amount'), _('Tax Amount'), '']],
            'colspan': self.user_has_groups('base.group_multi_currency') and 4 or 3,
            'level': 2,
            'unfoldable': False,
            'unfolded': False,
        }]

        tax_report_date = options['date'].copy()
        tax_report_date['strict_range'] = True
        tax_report_options = self.env['account.generic.tax.report']._get_options()
        tax_report_options.update({
            'tax_grids': False,
            'date': tax_report_date,
            'journals': options['journals'],
            'all_entries': options['all_entries'],
            'amount_due_greater': options['amount_due_greater'],
            'project_wise': options['project_wise'],
            'property_wise': options['property_wise'],
            'receivable_wise': options['receivable_wise'],
            'amount_due_less': options['amount_due_less'],
            'installment': options['installment'],
        })
        journal = self.env['account.journal'].browse(self._get_options_journals(options)[0]['id'])
        tax_report_lines = self.env['account.generic.tax.report'].with_company(journal.company_id)._get_lines(
            tax_report_options)

        for tax_line in tax_report_lines:
            if tax_line['id'] not in ('sale', 'purchase'):  # We want to exclude title lines here
                tax_line['columns'].append({'name': ''})
                tax_line['colspan'] = self.user_has_groups('base.group_multi_currency') and 5 or 4
                lines.append(tax_line)

        return lines

    @api.model
    def _get_initial_balance_line(self, options, account, amount_currency, debit, credit, balance):
        columns = [
            {'name': self.format_value(debit), 'class': 'number'},
            {'name': self.format_value(credit), 'class': 'number'},
            {'name': self.format_value(balance), 'class': 'number'},
        ]

        has_foreign_currency = account.currency_id and account.currency_id != account.company_id.currency_id or False
        if self.user_has_groups('base.group_multi_currency'):
            columns.insert(0, {
                'name': has_foreign_currency and self.format_value(amount_currency, currency=account.currency_id,
                                                                   blank_if_zero=True) or '', 'class': 'number'})
        return {
            'id': 'initial_%d' % account.id,
            'class': 'o_account_reports_initial_balance',
            'name': _('Initial Balance'),
            'parent_id': 'account_%d' % account.id,
            'columns': columns,
            'colspan': 12,
        }

    @api.model
    def _get_account_title_line(self, options, account, amount_currency, debit, credit, balance, has_lines):
        has_foreign_currency = account.currency_id and account.currency_id != account.company_id.currency_id or False
        unfold_all = self._context.get('print_mode') and not options.get('unfolded_lines')

        name = '%s %s' % (account.code, account.name)

        max_length = self._context.get('print_mode') and 100 or 60
        if len(name) > max_length and not self._context.get('no_format'):
            name = name[:max_length] + '...'
        columns = [
            {'name': self.format_value(debit), 'class': 'number'},
            {'name': self.format_value(credit), 'class': 'number'},
            {'name': self.format_value(balance), 'class': 'number'},
        ]
        if self.user_has_groups('base.group_multi_currency'):
            columns.insert(0, {
                'name': has_foreign_currency and self.format_value(amount_currency, currency=account.currency_id,
                                                                   blank_if_zero=True) or '', 'class': 'number'})
        # inp = name
        # new_input = ""
        # for i, letter in enumerate(inp):
        #     if i % 20 == 0:
        #         new_input += '\n'
        #     new_input += letter
        #
        # # this is just because at the beginning too a `\n` character gets added
        # new_input = new_input[1:]
        # name = new_input
        # name = name.replace("\n","<br />\n")
        return {
            'id': 'account_%d' % account.id,
            'name': name[:30] + " ...",
            'title_hover': name[:30] + " ...",
            'columns': columns,
            'level': 2,
            'unfoldable': has_lines,
            'unfolded': has_lines and 'account_%d' % account.id in options.get('unfolded_lines') or unfold_all,
            'colspan': 12,
            'class': 'whitespace_print' if self.env.company.totals_below_sections else '',
        }

    @api.model
    def _get_account_total_line(self, options, account, amount_currency, debit, credit, balance):
        has_foreign_currency = account.currency_id and account.currency_id != account.company_id.currency_id or False

        columns = []
        if self.user_has_groups('base.group_multi_currency'):
            columns.append({'name': has_foreign_currency and self.format_value(amount_currency,
                                                                               currency=account.currency_id,
                                                                               blank_if_zero=True) or '',
                            'class': 'number'})

        columns += [
            {'name': self.format_value(debit), 'class': 'number'},
            {'name': self.format_value(credit), 'class': 'number'},
            {'name': self.format_value(balance), 'class': 'number'},
        ]
        # inp = account['display_name']
        # new_input = ""
        # for i, letter in enumerate(inp):
        #     if i % 20 == 0:
        #         new_input += '\n'
        #     new_input += letter
        #
        # # this is just because at the beginning too a `\n` character gets added
        # new_input = new_input[1:]
        # name=new_input
        # name = name.replace("\n","<br />\n")
        return {
            'id': 'total_%s' % account.id,
            'class': 'o_account_reports_domain_total',
            'parent_id': 'account_%s' % account.id,
            'name': _('Total %s ...', account['display_name'][:30]),
            'columns': columns,
            'colspan': 2,
        }

    @api.model
    def _get_total_line(self, options, debit, credit, balance):
        return {
            'id': 'general_ledger_total_%s' % self.env.company.id,
            'name': _('Total'),
            'class': 'total',
            'level': 1,
            'columns': [
                {'name': self.format_value(debit), 'class': 'number'},
                {'name': self.format_value(credit), 'class': 'number'},
                {'name': self.format_value(balance), 'class': 'number'},
            ],
            'colspan': self.user_has_groups('base.group_multi_currency') and 5 or 12,
        }

    @api.model
    def _get_columns_name(self, options):
        columns_names = [
            {'name': ''},
            {'name': _('Date'), 'class': 'date'},
            {'name': _('Communication')},
            {'name': _('Partner')},
            {'name': _('Project')},
            {'name': _('Property')},
            {'name': _('Voucher #')},
            {'name': _('Journal Name')},
            {'name': _('Remarks'), 'class': 'whitespace_print'},
            {'name': _('Check Number')},
            {'name': _('Maturity Date')},
            {'name': _('Voucher Status')},
            {'name': _('Debit'), 'class': 'number'},
            {'name': _('Credit'), 'class': 'number'},
            {'name': _('Balance'), 'class': 'number'}
        ]
        if self.user_has_groups('base.group_multi_currency'):
            columns_names.insert(4, {'name': _('Currency'), 'class': 'number'})
        return columns_names

    @api.model
    def _get_query_amls(self, options, expanded_account, offset=None, limit=None):
        ''' Construct a query retrieving the account.move.lines when expanding a report line with or without the load
        more.
        :param options:             The report options.
        :param expanded_account:    The account.account record corresponding to the expanded line.
        :param offset:              The offset of the query (used by the load more).
        :param limit:               The limit of the query (used by the load more).
        :return:                    (query, params)
        '''

        unfold_all = options.get('unfold_all') or (self._context.get('print_mode') and not options['unfolded_lines'])

        # Get sums for the account move lines.
        # period: [('date' <= options['date_to']), ('date', '>=', options['date_from'])]
        if expanded_account:
            domain = [('account_id', '=', expanded_account.id)]
        elif unfold_all:
            domain = []
        elif options['unfolded_lines']:
            domain = [('account_id', 'in', [int(line[8:]) for line in options['unfolded_lines']])]

        new_options = self._force_strict_range(options)
        tables, where_clause, where_params = self._query_get(new_options, domain=domain)
        ct_query = self.env['res.currency']._get_query_currency_table(options)
        query = '''
                SELECT
                    account_move_line.id,
                    account_move_line.date,
                    account_move_line.maturity_date,
                    account_move_line.name,
                    account_move_line.ref,
                    account_move_line.company_id,
                    account_move_line.account_id,
                    account_move_line.payment_id,
                    account_move_line.partner_id,
                    account_move_line.asset_project_id,
                    account_move_line.journal_id,
                    account_move_line.move_id,
                    account_move_line.payment_id,
                    account_move_line.remarks,
                    account_move_line.check_number,
                    account_move_line.property_id,
                    account_move_line.currency_id,
                    account_move_line.amount_currency,
                    ROUND(account_move_line.debit * currency_table.rate, currency_table.precision)   AS debit,
                    ROUND(account_move_line.credit * currency_table.rate, currency_table.precision)  AS credit,
                    ROUND(account_move_line.balance * currency_table.rate, currency_table.precision) AS balance,
                    account_move_line__move_id.name         AS move_name,
                    account_move_line.remarks         AS remarks_name,
                    account_move_line.check_number         AS check_number,
                    company.currency_id                     AS company_currency_id,
                    partner.name                            AS partner_name,
                    voucher.state                            AS move_state,
                    project.name                            AS project_name,
                    journalnew.name                            AS journal_name_new,
                    property.name                            AS property_name,
                    voucher.name                            AS voucher_name,
                    account_move_line__move_id.move_type         AS move_type,
                    account.code                            AS account_code,
                    account.name                            AS account_name,
                    journal.code                            AS journal_code,
                    journal.name                            AS journal_name,
                    full_rec.name                           AS full_rec_name
                FROM account_move_line
                LEFT JOIN account_move account_move_line__move_id ON account_move_line__move_id.id = account_move_line.move_id
                LEFT JOIN %s ON currency_table.company_id = account_move_line.company_id
                LEFT JOIN res_company company               ON company.id = account_move_line.company_id
                LEFT JOIN res_partner partner               ON partner.id = account_move_line.partner_id
                LEFT JOIN account_asset_asset project               ON project.id = account_move_line.asset_project_id
                LEFT JOIN account_journal journalnew               ON journalnew.id = account_move_line.journal_id
                LEFT JOIN account_move voucher               ON voucher.id = account_move_line.move_id
                LEFT JOIN account_asset_asset property               ON property.id = account_move_line.property_id
                LEFT JOIN account_account account           ON account.id = account_move_line.account_id
                LEFT JOIN account_journal journal           ON journal.id = account_move_line.journal_id
                LEFT JOIN account_full_reconcile full_rec   ON full_rec.id = account_move_line.full_reconcile_id
                WHERE %s
                ORDER BY account_move_line.date, account_move_line.id
            ''' % (ct_query, where_clause)

        if offset:
            query += ' OFFSET %s '
            where_params.append(offset)
        if limit:
            query += ' LIMIT %s '
            where_params.append(limit)

        return query, where_params

    @api.model
    def _get_aml_line(self, options, account, aml, cumulated_balance):
        if aml['payment_id']:
            caret_type = 'account.payment'
        else:
            caret_type = 'account.move'

        if aml['ref'] and aml['name']:
            title = '%s - %s' % (aml['name'], aml['ref'])
        elif aml['ref']:
            title = aml['ref']
        elif aml['name']:
            title = aml['name']
        else:
            title = ''

        if (aml['currency_id'] and aml['currency_id'] != account.company_id.currency_id.id) or account.currency_id:
            currency = self.env['res.currency'].browse(aml['currency_id'])
        else:
            currency = False

        columns = [
            {'name': format_date(self.env, aml['date']), 'class': 'date'},
            {'name': self._format_aml_name(aml['name'], aml['ref'], aml['move_name']), 'title': title,
             'class': 'whitespace_print o_account_report_line_ellipsis'},
            {'name': aml['partner_name'], 'title': aml['partner_name'], 'class': 'whitespace_print'},
            {'name': aml['project_name'], 'title': aml['project_name'], 'class': 'whitespace_print'},
            {'name': aml['property_name'], 'title': aml['property_name'], 'class': 'whitespace_print'},
            {'name': aml['voucher_name'], 'title': aml['voucher_name'], 'class': 'whitespace_print'},
            {'name': aml['journal_name_new'], 'title': aml['journal_name_new'], 'class': 'whitespace_print'},
            {'name': aml['remarks_name'], 'title': aml['remarks_name'], 'class': 'whitespace_print'},
            {'name': aml['check_number'], 'title': aml['check_number'], 'class': 'whitespace_print'},
            {'name': format_date(self.env, aml['maturity_date']), 'class': 'date'},
            {'name': aml['move_state'], 'title': aml['move_state'], 'class': 'whitespace_print'},
            {'name': self.format_value(aml['debit'], blank_if_zero=True), 'class': 'number'},
            {'name': self.format_value(aml['credit'], blank_if_zero=True), 'class': 'number'},
            {'name': self.format_value(cumulated_balance), 'class': 'number'},
        ]
        if self.user_has_groups('base.group_multi_currency'):
            columns.insert(3, {'name': currency and aml['amount_currency'] and self.format_value(aml['amount_currency'],
                                                                                                 currency=currency,
                                                                                                 blank_if_zero=True) or '',
                               'class': 'number'})
        return {
            'id': aml['id'],
            'caret_options': caret_type,
            'class': 'top-vertical-align',
            'parent_id': 'account_%d' % aml['account_id'],
            'name': aml['move_name'],
            'columns': columns,
            'level': 2,
        }


class ReportPartnerLedger(models.AbstractModel):
    _inherit = "account.partner.ledger"

    pdc = False
    payment_date_check = False

    @api.model
    def _get_report_line_partner(self, options, partner, initial_balance, debit, credit, balance):
        company_currency = self.env.company.currency_id
        unfold_all = self._context.get('print_mode') and not options.get('unfolded_lines')

        columns = [
            {'name': self.format_value(initial_balance), 'class': 'number'},
            {'name': self.format_value(debit), 'class': 'number'},
            {'name': self.format_value(credit), 'class': 'number'},
        ]
        if self.user_has_groups('base.group_multi_currency'):
            columns.append({'name': ''})
        columns.append({'name': self.format_value(balance), 'class': 'number'})

        return {
            'id': 'partner_%s' % (partner.id if partner else 0),
            'partner_id': partner.id if partner else None,
            'name': partner is not None and (partner.name or '')[:128] or _('Unknown Partner'),
            'columns': columns,
            'level': 2,
            'trust': partner.trust if partner else None,
            'unfoldable': not company_currency.is_zero(debit) or not company_currency.is_zero(credit),
            'unfolded': 'partner_%s' % (partner.id if partner else 0) in options['unfolded_lines'] or unfold_all,
            'colspan': 11,
        }

    @api.model
    def _get_report_line_total(self, options, initial_balance, debit, credit, balance):
        columns = [
            {'name': self.format_value(initial_balance), 'class': 'number'},
            {'name': self.format_value(debit), 'class': 'number'},
            {'name': self.format_value(credit), 'class': 'number'},
        ]
        if self.user_has_groups('base.group_multi_currency'):
            columns.append({'name': ''})
        columns.append({'name': self.format_value(balance), 'class': 'number'})
        return {
            'id': 'partner_ledger_total_%s' % self.env.company.id,
            'name': _('Total'),
            'class': 'total',
            'level': 1,
            'columns': columns,
            'colspan': 11,
        }

    def _get_columns_name(self, options):
        columns = [
            {},
            # {'name': _('JRNL')},
            {'name': _('Voucher #')},
            {'name': _('Journal Name'), 'class': 'whitespace_print'},
            {'name': _('Remarks')},
            {'name': _('Check Number'), 'class': 'whitespace_print'},
            {'name': _('Project')},
            {'name': _('Property')},
            {'name': _('Voucher Status'), 'class': 'whitespace_print'},
            {'name': _('Account')},
            {'name': _('Ref')},
            {'name': _('Maturity Date'), 'class': 'date'},
            # {'name': _('Matching Number')},
            {'name': _('Initial Balance'), 'class': 'number'},
            {'name': _('Debit'), 'class': 'number'},
            {'name': _('Credit'), 'class': 'number'}]

        if self.user_has_groups('base.group_multi_currency'):
            columns.append({'name': _('Amount Currency'), 'class': 'number'})

        columns.append({'name': _('Balance'), 'class': 'number'})

        return columns

    @api.model
    def _get_report_line_move_line(self, options, partner, aml, cumulated_init_balance, cumulated_balance):
        if aml['payment_id']:
            caret_type = 'account.payment'
        else:
            caret_type = 'account.move'

        date_maturity = aml['maturity_date'] and format_date(self.env, fields.Date.from_string(aml['maturity_date']))
        line_name = self._format_aml_name(aml['name'], aml['ref'], aml['move_name'])
        columns = [
            {'name': aml['voucher_name']},
            {'name': aml['journal_name'], 'class': 'whitespace_print'},
            {'name': aml['remarks_name'], 'class': 'whitespace_print'},
            {'name': aml['check_number']},
            {'name': aml['project_name'], 'title': aml['project_name'], 'class': 'whitespace_print'},
            {'name': aml['property_name'], 'title': aml['property_name'], 'class': 'whitespace_print'},
            {'name': aml['move_state']},
            {'name': aml['account_name']},
            {'name': line_name, 'title': line_name, 'class': 'whitespace_print'},
            {'name': date_maturity or '', 'class': 'date'},
            # {'name': aml['matching_number'] or ''},
            {'name': self.format_value(cumulated_init_balance), 'class': 'number'},
            {'name': self.format_value(aml['debit'], blank_if_zero=True), 'class': 'number'},
            {'name': self.format_value(aml['credit'], blank_if_zero=True), 'class': 'number'},
        ]
        if self.user_has_groups('base.group_multi_currency'):
            if aml['currency_id']:
                currency = self.env['res.currency'].browse(aml['currency_id'])
                formatted_amount = self.format_value(aml['amount_currency'], currency=currency, blank_if_zero=True)
                columns.append({'name': formatted_amount, 'class': 'number'})
            else:
                columns.append({'name': ''})
        columns.append({'name': self.format_value(cumulated_balance), 'class': 'number'})
        return {
            'id': aml['id'],
            'parent_id': 'partner_%s' % (partner.id if partner else 0),
            'name': format_date(self.env, aml['date']),
            'class': 'text' + aml.get('class', ''),  # do not format as date to prevent text centering
            'columns': columns,
            'caret_options': caret_type,
            'level': 2,
        }

    @api.model
    def _get_query_amls(self, options, expanded_partner=None, offset=None, limit=None):
        ''' Construct a query retrieving the account.move.lines when expanding a report line with or without the load
        more.
        :param options:             The report options.
        :param expanded_partner:    The res.partner record corresponding to the expanded line.
        :param offset:              The offset of the query (used by the load more).
        :param limit:               The limit of the query (used by the load more).
        :return:                    (query, params)
        '''
        unfold_all = options.get('unfold_all') or (self._context.get('print_mode') and not options['unfolded_lines'])

        # Get sums for the account move lines.
        # period: [('date' <= options['date_to']), ('date', '>=', options['date_from'])]
        if expanded_partner is not None:
            domain = [('partner_id', '=', expanded_partner.id)]
        elif unfold_all:
            domain = []
        elif options['unfolded_lines']:
            domain = [('partner_id', 'in', [int(line[8:]) for line in options['unfolded_lines']])]

        new_options = self._get_options_sum_balance(options)
        tables, where_clause, where_params = self._query_get(new_options, domain=domain)
        ct_query = self.env['res.currency']._get_query_currency_table(options)

        query = '''
                SELECT
                    account_move_line.id,
                    account_move_line.date,
                    account_move_line.maturity_date,
                    account_move_line.name,
                    account_move_line.ref,
                    account_move_line.company_id,
                    account_move_line.account_id,
                    account_move_line.payment_id,
                    account_move_line.partner_id,
                    account_move_line.currency_id,
                    account_move_line.amount_currency,
                    account_move_line.matching_number,
                    ROUND(account_move_line.debit * currency_table.rate, currency_table.precision)   AS debit,
                    ROUND(account_move_line.credit * currency_table.rate, currency_table.precision)  AS credit,
                    ROUND(account_move_line.balance * currency_table.rate, currency_table.precision) AS balance,
                    account_move_line__move_id.name         AS move_name,
                    company.currency_id                     AS company_currency_id,
                    partner.name                            AS partner_name,
                    account_move_line__move_id.move_type    AS move_type,
                    account.code                            AS account_code,
                    voucher.name                            AS voucher_name,
                    project.name                            AS project_name,
                    property.name                            AS property_name,
                    voucher.state                            AS move_state,
                    account.name                            AS account_name,
                    journal.code                            AS journal_code,
                    account_move_line.remarks               AS remarks_name,
                    account_move_line.check_number         AS check_number,
                    journal.name                            AS journal_name

                FROM %s
                LEFT JOIN %s ON currency_table.company_id = account_move_line.company_id
                LEFT JOIN res_company company               ON company.id = account_move_line.company_id
                LEFT JOIN account_move voucher               ON voucher.id = account_move_line.move_id
                LEFT JOIN res_partner partner               ON partner.id = account_move_line.partner_id
                LEFT JOIN account_asset_asset project               ON project.id = account_move_line.asset_project_id
                LEFT JOIN account_asset_asset property               ON property.id = account_move_line.property_id
                LEFT JOIN account_account account           ON account.id = account_move_line.account_id
                LEFT JOIN account_journal journal           ON journal.id = account_move_line.journal_id
                WHERE %s
                ORDER BY account_move_line.date, account_move_line.id
            ''' % (tables, ct_query, where_clause)

        if offset:
            query += ' OFFSET %s '
            where_params.append(offset)
        if limit:
            query += ' LIMIT %s '
            where_params.append(limit)

        return query, where_params

    # @api.model
    # def _get_partner_ledger_lines(self, options, line_id=None):
    #     ''' Get lines for the whole report or for a specific line.
    #     :param options: The report options.
    #     :return:        A list of lines, each one represented by a dictionary.
    #     '''
    #     lines = []
    #     unfold_all = options.get('unfold_all') or (self._context.get('print_mode') and not options['unfolded_lines'])
    #
    #     expanded_partner = line_id and self.env['res.partner'].browse(int(line_id[8:]))
    #     partners_results = self._do_query(options, expanded_partner=expanded_partner)
    #
    #     total_initial_balance = total_debit = total_credit = total_balance = 0.0
    #     check = True
    #     newcumulated_balance = 0.0
    #     # partners_results = sorted(partners_results, key=lambda i: i[1]['initial_balance']['balance'], reverse=True)
    #     for partner, results in partners_results:
    #         is_unfolded = 'partner_%s' % (partner.id if partner else 0) in options['unfolded_lines']
    #
    #         # res.partner record line.
    #         partner_sum = results.get('sum', {})
    #         partner_init_bal = results.get('initial_balance', {})
    #
    #         initial_balance = partner_init_bal.get('balance', 0.0)
    #         debit = partner_sum.get('debit', 0.0)
    #         credit = partner_sum.get('credit', 0.0)
    #         balance = initial_balance + partner_sum.get('balance', 0.0)
    #
    #         lines.append(self._get_report_line_partner(options, partner, initial_balance, debit, credit, balance))
    #
    #         total_initial_balance += initial_balance
    #         total_debit += debit
    #         total_credit += credit
    #         total_balance += balance
    #
    #         if unfold_all or is_unfolded:
    #             account_init_bal = results.get('initial_balance', {})
    #             cumulated_balance = initial_balance
    #             cumulated_balance = newcumulated_balance
    #             if not options.get('no_init'):
    #                 cumulated_balance = account_init_bal.get('balance', 0.0) + partner_sum.get('balance', 0.0)
    #             # account.move.line record lines.
    #             amls = results.get('lines', [])
    #
    #             load_more_remaining = len(amls)
    #             load_more_counter = self._context.get('print_mode') and load_more_remaining or self.MAX_LINES
    #
    #             for aml in amls:
    #                 # Don't show more line than load_more_counter.
    #                 if options.get('no_init') and check:
    #                     check = False
    #                     cumulated_balance = 0.0
    #                 if load_more_counter == 0:
    #                     break
    #
    #                 cumulated_init_balance = cumulated_balance
    #                 cumulated_balance += aml['balance']
    #                 lines.append(self._get_report_line_move_line(options, partner, aml, cumulated_init_balance,
    #                                                              cumulated_balance))
    #
    #                 load_more_remaining -= 1
    #                 load_more_counter -= 1
    #
    #             if load_more_remaining > 0:
    #                 # Load more line.
    #                 lines.append(self._get_report_line_load_more(
    #                     options,
    #                     partner,
    #                     self.MAX_LINES,
    #                     load_more_remaining,
    #                     cumulated_balance,
    #                 ))
    #
    #     if not line_id:
    #         # Report total line.
    #         lines.append(self._get_report_line_total(
    #             options,
    #             total_initial_balance,
    #             total_debit,
    #             total_credit,
    #             total_balance
    #         ))
    #     return lines
