# -*- coding: utf-8 -*-
from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import base64
import io
try:
    from odoo.tools.misc import xlsxwriter
except ImportError:
    import xlsxwriter


class MailRecipients(models.Model):
    _name = "mail.recipients"

    name = fields.Char('Name')
    from_data = fields.Boolean('From Data', default=False)
    user_ids = fields.Many2many('res.users','user_recipient_rel','recipient_id','user_id', 'Recipients')
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.user.company_id)

    def get_xls_files(self, receipts):
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet('receipts')
        format4 = workbook.add_format({'font_size': 10})
        format2 = workbook.add_format({'font_size': 12, 'bold': True, 'bg_color': '#D3D3D3'})

        sheet.write('A2', "Payment Date ", format2)
        sheet.write('B2', "Created on", format2)
        sheet.merge_range('C2:D2', "Memo", format2)
        sheet.merge_range('E2:F2', "Payment Journal", format2)
        sheet.merge_range('G2:I2', "Maturity Date", format2)
        sheet.merge_range('J2:K2', "Check Number", format2)
        sheet.merge_range('L2:M2', "Project", format2)
        sheet.merge_range('N2:O2', "Booking", format2)
        sheet.merge_range('P2:Q2', "SPA", format2)
        sheet.merge_range('R2:S2', "Property", format2)
        sheet.merge_range('T2:U2', "Customer", format2)
        sheet.merge_range('V2:W2', "Payment Amount", format2)
        sheet.write('X2', "Status ", format2)
        row_number = 2
        col_number = 0
        for rec in receipts:
            a = 'a'
            payment_date = '-'
            create_date = '-'
            maturity_date = '-'
            if rec.payment_date:
                if type(rec.payment_date) == type(a):
                    payment_date = rec.payment_date
                else:
                    payment_date = datetime.strftime(rec.payment_date, "%d/%m/%Y")

            if rec.create_date:
                if type(rec.create_date) == type(a):
                    create_date = rec.create_date
                else:
                    create_date = datetime.strftime(rec.create_date, "%d/%m/%Y")

            if rec.maturity_date:
                if type(rec.maturity_date) == type(a):
                    # if len(lines['maturity_date']) <= 10:
                    maturity_date = rec.maturity_date
                else:
                    maturity_date = datetime.strftime(rec.maturity_date, "%d/%m/%Y")

            sheet.write(row_number, col_number, payment_date, format4)
            sheet.write(row_number, col_number + 1, create_date, format4)
            rname = '-'
            if rec.name:
                rname = rec.name
            sheet.merge_range(row_number, col_number + 2, row_number, col_number + 3, rname,
                              format4)
            sheet.merge_range(row_number, col_number + 4, row_number, col_number + 5,rec.journal_id.name,
                              format4)

            sheet.merge_range(row_number, col_number + 6, row_number, col_number + 8, maturity_date,
                              format4)
            check_number = '-'
            if rec.check_number:
                check_number = rec.check_number
            sheet.merge_range(row_number, col_number + 9, row_number, col_number + 10, check_number,
                              format4)
            asset_project_id = '-'
            if rec.asset_project_id:
                asset_project_id = rec.asset_project_id.name
            sheet.merge_range(row_number, col_number + 11, row_number, col_number + 12, asset_project_id,
                              format4)
            booking_id = '-'
            if rec.booking_id:
                booking_id = rec.booking_id.booking_number

            sheet.merge_range(row_number, col_number + 13, row_number, col_number + 14, booking_id,
                              format4)
            spa_id = '-'
            if rec.spa_id:
                spa_id = rec.spa_id.name
            sheet.merge_range(row_number, col_number + 15, row_number, col_number + 16, spa_id,
                              format4)
            property_id = '-'
            if rec.property_id:
                property_id = rec.property_id.name
            sheet.merge_range(row_number, col_number + 17, row_number, col_number + 18, property_id ,
                              format4)
            partner_id = '-'
            if rec.partner_id:
                partner_id = rec.partner_id.name
            sheet.merge_range(row_number, col_number + 19, row_number, col_number + 20, partner_id ,
                              format4)
            amount = '-'
            if rec.amount:
                amount = rec.amount
            sheet.merge_range(row_number, col_number + 21, row_number, col_number + 22, amount , format4)
            sheet.write(row_number, col_number + 23, rec.state, format4)

            row_number += 1

        # encoded = base64.b64encode(towrite.read())
        workbook.close()
        output.seek(0)
        xls_file = base64.b64encode(output.read())
        output.close()
        return xls_file

    def get_partner_ids(self, user_ids):
        if user_ids:
            anb =  str([user.partner_id.email for user in user_ids]).replace('[', '').replace(']', '')
            return anb.replace("'", '')

    @api.model
    def send_unallocated_and_draft_receipt_email(self):
        mr = self.env['mail.recipients'].search([('name','=','Unallocated and Draft Receipts Recipients')])
        for rec in mr:
            # docs = self._context.get('active_ids', [])
            domain_unallocated =[('payment_type','=','inbound'),('state', 'not in', ['draft','cancelled']),
                                 ('booking_id', '=', False)]
            receipt_list =[]
            receipt_ids = self.env['account.payment'].search(domain_unallocated)
            for record in receipt_ids:
                if record.invoice_ids or record.reconciled_invoice_ids:
                    receipt_list.append(record.id)
            domain_draft =[('payment_type','=','inbound'),('state', '=', 'draft')]

            receipt_ids_unallocated = rec.env['account.payment'].search([('id','in',receipt_list)])
            receipt_ids_draft = rec.env['account.payment'].search(domain_draft)
            xls_file_draft = rec.get_xls_files(receipt_ids_draft)
            xls_file_unallocated = rec.get_xls_files(receipt_ids_unallocated)

            if rec.user_ids:
                email_template = rec.env.ref('account_receipts_custom.unallocated_and_draft_receipts_email')

                report_name_unallocated = 'sd_unallocated_receipts'
                report_name_draft = 'sd_draft_receipts'
                filename_unallocated = "%s.%s" % (report_name_unallocated, "xlsx")
                filename_draft = "%s.%s" % (report_name_draft, "xlsx")
                attachment_unallocated = rec.env['ir.attachment'].create({
                    'name': filename_unallocated,
                    'datas': xls_file_unallocated,
                    'datas_fname': filename_unallocated,
                    'type': 'binary',
                })
                attachment_draft = rec.env['ir.attachment'].create({
                    'name': filename_draft,
                    'datas': xls_file_draft,
                    'datas_fname': filename_draft,
                    'type': 'binary',
                })
                email_template.email_to = rec.get_partner_ids(rec.user_ids)
                email_template.attachment_ids = [(6, 0, [attachment_unallocated.id,attachment_draft.id])]
                email_template.send_mail(rec.id, force_send=True)

