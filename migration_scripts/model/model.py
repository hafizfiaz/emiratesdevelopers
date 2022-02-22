# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
import time
from odoo.tools.translate import _
from lxml import etree
from odoo.exceptions import UserError, ValidationError
import xmlrpc.client

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    old_booking_id_all = fields.Integer('Old Booking id all')
    old_booking_id = fields.Integer('Old Booking id')

class IrAttachment(models.Model):
    _inherit = 'ir.attachment'

    old_id = fields.Integer('Old Id')


class CustomerRequest(models.Model):
    _name = 'migration.script'
    _description = 'Migration Scripts'

    name = fields.Char('Name', required=True)
    query_chk = fields.Boolean('Query', default=False)
    return_chk = fields.Boolean('Will Return', default=False)
    query_text = fields.Text('Query Text')
    result = fields.Char('Result')

    def run_query(self):
        if self.query_text and self.return_chk:
            query = self.query_text
            self._cr.execute(query)
            res = self._cr.fetchall()
            self._cr.commit()
            self.result = str(res)
        if self.query_text and not self.return_chk:
            query = self.query_text
            self._cr.execute(query)
            self._cr.commit()

    def db_connection(self):
        url = 'http://51.83.184.61:8069'
        db = "developer12"
        username = "admin"
        password = "Admin@564"
        # info = xmlrpc.client.ServerProxy('http://51.75.52.98:8069').start()
        # url, db, username, password = \
        #     info['host'], info['database'], info['user'], info['password']

        common = xmlrpc.client.ServerProxy('{}/xmlrpc/2/common'.format(url))
        common.version()
        uid = common.authenticate(db, username, password, {})
        models = xmlrpc.client.ServerProxy('{}/xmlrpc/2/object'.format(url))

        payment_ids = models.execute_kw(db, uid, password,
                                        'crm.booking', 'search',
                                        [[['joined_active', '=', True]]])
        pay_record = models.execute_kw(db, uid, password,
                                       'crm.booking', 'read', [payment_ids],
                                       {'fields': ['joined_active', 'joined_partner_id', 'id']})
        # vals_list = []
        count = 0
        for line in pay_record:
            spa = self.env['sale.order'].search([('old_booking_id_all', '=', line['id'])])
            if spa and not spa.joint_active:
                spa.joint_active = [(6, 0, line['joined_active'])]
                spa.joint_partner_id = [(6, 0, line['joined_partner_id'])]
            count += 1
            print(count)
    # ====================================================================================

    # payment_ids = models.execute_kw(db, uid, password,
    #                                 'sale.order', 'search',
    #                                 [[['joined_active', '=', True]]])
    # pay_record = models.execute_kw(db, uid, password,
    #                                'sale.order', 'read', [payment_ids],
    #                                {'fields': ['joined_active', 'joined_partner_id', 'id']})
    # # vals_list = []
    # count=0
    # for line in pay_record:
    #     spa = self.env['sale.order'].search([('id', '=', line['id'])])
    #     if spa:
    #         spa.joint_active = [(6, 0, line['joined_active'])]
    #         spa.joint_partner_id = [(6, 0, line['joined_partner_id'])]
    #     count+=1
    #     print(count)
    # ====================================================================================
    # payment_ids = models.execute_kw(db, uid, password,
    #                                 'sale.order', 'search',
    #                                 [[['salesperson_ids', '!=', False]]])
    # pay_record = models.execute_kw(db, uid, password,
    #                                'sale.order', 'read', [payment_ids],
    #                                {'fields': ['salesperson_ids', 'id']})
    # # vals_list = []
    # count=0
    # for line in pay_record:
    #     spa = self.env['sale.order'].search([('id', '=', line['id'])])
    #     if spa:
    #         spa.salesperson_ids = [(6, 0, line['salesperson_ids'])]
    #     count+=1
    #     print(count)
    # =============================================================================

    # payment_ids = models.execute_kw(db, uid, password,
        #                                 'account.invoice', 'search',
        #                                 [[['approval_id', '!=', False]]])
        # pay_record = models.execute_kw(db, uid, password,
        #                                'account.invoice', 'read', [payment_ids],
        #                                {'fields': ['approval_id', 'approved_by', 'id']})
        #
        # # # vals_list = []
        # for line in pay_record:
        #     invoices = self.env['account.move'].search([('old_invoice_id', '=', line['id'])])
        #     if invoices:
        #         if line['approval_id']:
        #             invoices.approval_id = line['approval_id'][0]
        #         if line['approved_by']:
        #             invoices.approved_by = line['approved_by'][0]

        # payment_ids = models.execute_kw(db, uid, password,
        #                                 'account.invoice', 'search',
        #                                 [[['rental', '=', True]]])
        # pay_record = models.execute_kw(db, uid, password,
        #                                'account.invoice', 'read', [payment_ids],
        #                                {'fields': ['rental_schedule_id', 'id']})
        # vals_list = []
        # for line in pay_record:
        #     # invoices = self.env['tenancy.rent.schedule'].search([('id', 'in', line['rental_schedule_id'][0])])
        #     type_tuple = (line['rental_schedule_id'][0],line['id'])
        #     vals_list.append(type_tuple)
        #
        # for data in vals_list:
        #     type_query = "UPDATE account_move SET rental_schedule_id=%s, rental=True where old_invoice_id=%s"
        #     self._cr.execute(type_query, data)
        #     self._cr.commit()

        # payment_ids = models.execute_kw(db, uid, password,
        #                                 'account.payment', 'search',
        #                                 [[['invoice_lines', '!=', False]]])
        # pay_record = models.execute_kw(db, uid, password,
        #                                'account.payment', 'read', [payment_ids],
        #                                {'fields': ['invoice_lines', 'id']})
        # # vals_list = []
        # for line in pay_record:
        #     if line['invoice_lines']:
        #         payment = self.env['account.payment'].search([('id', '=', line['id'])])
        #         invoices = self.env['account.move'].search([('old_invoice_id', 'in', line['invoice_lines'])])
        #         if payment and invoices:
        #             payment.invoice_lines = [(6, 0, invoices.ids)]


        # type_ids = models.execute_kw(db, uid, password,
        #                              'vendor.type', 'search',
        #                              [[['name', '!=', False]]])
        # type_record = models.execute_kw(db, uid, password,
        #                                 'vendor.type', 'read', [type_ids])
        # vals_list = []
        # for line in type_record:
        #     type_tuple = (line['id'],
        #                   line['name'],
        #                   line['vendor_active'],
        #                   line['create_uid'][0],
        #                   line['create_date'],
        #                   line['write_uid'][0],
        #                   line['write_date']
        #                   )
        #     vals_list.append(type_tuple)
        #
        # for data in vals_list:
        #     type_query = """INSERT INTO public.vendor_type(
        #         id, name, vendor_active, create_uid, create_date,
        #         write_uid, write_date)
        #         VALUES (%s, %s, %s, %s,
        #                 %s, %s, %s);"""
        #
        #     self._cr.execute(type_query, data)
        #     self._cr.commit()
        #
        # payment_ids = models.execute_kw(db, uid, password,
        #                         'account.payment', 'search',
        #                         [[['vendor_type', '!=', False]]])
        #
        # pay_record = models.execute_kw(db, uid, password,
        #                                'account.payment', 'read', [payment_ids], {'fields': ['vendor_type', 'id']})
        # vals_list = []
        # for line in pay_record:
        #     type_tuple = (line['vendor_type'][0],line['id'])
        #     vals_list.append(type_tuple)
        #
        # for data in vals_list:
        #     type_query = "UPDATE account_payment SET vendor_type=%s where id=%s"
        #     self._cr.execute(type_query, data)
        #     self._cr.commit()


        # payment_ids = models.execute_kw(db, uid, password,
        #                                 'account.payment', 'search',
        #                                 [[['approval_from_ids', '!=', False]]])
        # pay_record = models.execute_kw(db, uid, password,
        #                                'account.payment', 'read', [payment_ids],
        #                                {'fields': ['approval_from_ids', 'id']})
        # # vals_list = []
        # for line in pay_record:
        #     payment = self.env['account.payment'].search([('id', '=', line['id'])])
        #     if payment:
        #         payment.approval_from_ids = [(6, 0, line['approval_from_ids'])]

            # type_tuple = (line['check_number'],line['id'])
            # vals_list.append(type_tuple)

        # for data in vals_list:
        #     type_query = "UPDATE account_payment SET check_number=%s where id=%s"
        #     self._cr.execute(type_query, data)
        #     self._cr.commit()

        # payment_ids = models.execute_kw(db, uid, password,
        #                         'account.payment', 'search',
        #                         [[['check_number', '!=', False]]])
        # pay_record = models.execute_kw(db, uid, password,
        #                                'account.payment', 'read', [payment_ids], {'fields': ['check_number', 'id']})
        # vals_list = []
        # for line in pay_record:
        #     type_tuple = (line['check_number'],line['id'])
        #     vals_list.append(type_tuple)
        #
        # for data in vals_list:
        #     type_query = "UPDATE account_payment SET check_number=%s where id=%s"
        #     self._cr.execute(type_query, data)
        #     self._cr.commit()

        # type_ids = models.execute_kw(db, uid, password,
        #                         'approval.type', 'search',
        #                         [[['name', '!=', False]]])
        # type_record = models.execute_kw(db, uid, password,
        #                              'approval.type', 'read', [type_ids])
        # vals_list = []
        # for line in type_record:
        #     type_tuple = (line['id'],
        #                   line['name'],
        #                   line['manager_review'],
        #                   line['accounts_review'],
        #                   line['gm_review'],
        #                   line['ceo_review'],
        #                   line['invoice_check'],
        #                   line['create_uid'][0],
        #                   line['create_date'],
        #                   line['write_uid'][0],
        #                   line['write_date']
        #                   )
        #     vals_list.append(type_tuple)
        #
        # for data in vals_list:
        #     type_query = """INSERT INTO public.approval_type(
        #         id, name, manager_review, accounts_review, gm_review, ceo_review,
        #         invoice_check, create_uid, create_date,
        #         write_uid, write_date)
        #         VALUES (%s, %s, %s, %s, %s,
        #                 %s, %s, %s, %s,
        #                 %s, %s);"""
        #
        #     self._cr.execute(type_query, data)
        #     self._cr.commit()
        #
        # approval_ids = models.execute_kw(db, uid, password,
        #                         'approval.approval', 'search',
        #                         [[['name', '!=', False]]])
        # approval_record = models.execute_kw(db, uid, password,
        #                              'approval.approval', 'read', [approval_ids])
        # vals_list = []
        # for line in approval_record:
        #     attachment = None
        #     if line['message_main_attachment_id']:
        #         attach = self.env['ir.attachment'].sudo().search([('old_id', '=', line['message_main_attachment_id'][0])])
        #         if attach:
        #             attachment= attach.id
        #
        #     type_tuple = (line['id'],
        #                   line['name'],
        #                   line['previous_state'],
        #                   line['amount'],
        #                   line['approval_type_id'][0] if line['approval_type_id'] else None,
        #                   line['remarks'],
        #                   line['gm_remarks'],
        #                   line['is_gm_state'],
        #                   line['is_ceo_state'],
        #                   line['ceo_remarks'],
        #                   line['state'],
        #                   line['invoice_check'],
        #                   line['create_uid'][0],
        #                   line['create_date'],
        #                   line['write_uid'][0],
        #                   line['write_date'],
        #                   line['sequence'],
        #                   line['approve_user_id'][0] if line['approve_user_id'] else None,
        #                   attachment,
        #                   )
        #     vals_list.append(type_tuple)
        #
        # for data in vals_list:
        #     type_query = """INSERT INTO public.approval_approval(
        #     id, name, previous_state, amount, approval_type_id, remarks,
        #     gm_remarks, is_gm_state, is_ceo_state, ceo_remarks, state, invoice_check,
        #     create_uid, create_date, write_uid,
        #     write_date, sequence, approve_user_id ,message_main_attachment_id)
        #     VALUES (%s, %s, %s, %s, %s, %s,
        #             %s, %s, %s, %s, %s, %s,
        #             %s, %s, %s,
        #             %s, %s, %s, %s);"""
        #
        #     self._cr.execute(type_query, data)
        #     self._cr.commit()
