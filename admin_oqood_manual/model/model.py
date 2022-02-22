# -*- coding: utf-8 -*-
from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    related_move_type = fields.Selection(selection=[
            ('entry', 'Journal Entry'),
            ('out_invoice', 'Customer Invoice'),
            ('out_refund', 'Customer Credit Note'),
            ('in_invoice', 'Vendor Bill'),
            ('in_refund', 'Vendor Credit Note'),
            ('out_receipt', 'Sales Receipt'),
            ('in_receipt', 'Purchase Receipt'),
        ], string='Related Move Type', related='move_id.move_type')

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    oqood_received_manual = fields.Float('Oqood Received Manual')
    oqood_received_auto = fields.Float('Oqood Received Auto', compute='compute_admin_oqood_auto', store=True)
    admin_received_manual = fields.Float('Admin Received Manual')
    admin_received_auto = fields.Float('Admin Received Auto', compute='compute_admin_oqood_auto', store=True)
    oqood_received = fields.Float('Oqood Received', compute='compute_oqood_received', store=True)
    admin_received = fields.Float('Admin Fee Received', compute='compute_admin_received', store=True)

    @api.depends('other_charges_inv_ids','other_charges_inv_ids.state','other_charges_inv_ids.amount_residual')
    def compute_admin_oqood_auto(self):
        for rec in self:
            admin_received = 0
            oqood_received = 0
            if rec.other_charges_inv_ids:
                for line in rec.other_charges_inv_ids:
                    if line and line.invoice_line_ids and 'admin' in line.invoice_line_ids[0].name.lower() and line.state=='posted':
                        admin_received = line.amount_total - line.amount_residual
                    if line and line.invoice_line_ids and 'oqood' in line.invoice_line_ids[0].name.lower() and line.state=='posted':
                        oqood_received = line.amount_total - line.amount_residual
            rec.admin_received_auto = admin_received
            rec.oqood_received_auto = oqood_received


    @api.depends('admin_received_manual','admin_received_auto')
    def compute_admin_received(self):
        for rec in self:
            admin_received = 0
            if rec.admin_received_manual:
                admin_received = rec.admin_received_manual
            else:
                admin_received = rec.admin_received_auto
            rec.admin_received = admin_received

    @api.depends('oqood_received_manual','oqood_received_auto')
    def compute_oqood_received(self):
        for rec in self:
            oqood_received = 0
            if rec.oqood_received_manual:
                oqood_received = rec.oqood_received_manual
            else:
                oqood_received = rec.oqood_received_auto
            rec.oqood_received = oqood_received

    def map_old_oqood_admin(self):
        sos = self.env['sale.order'].search([])
        for rec in sos:
            rec.oqood_received_manual = rec.oqood_received
            rec.admin_received_manual = rec.admin_received

    # @api.model
    # def cron_asset_project_id_missed(self):
    #     sos = self.env['sale.order'].search([])
    #     for rec in sos:
    #         rec.schedule_a = rec.asset_project_id.schedule_a
    #         rec.schedule_b = rec.asset_project_id.schedule_b
    #         rec.schedule_c = rec.asset_project_id.schedule_c
    #         rec.schedule_d = rec.asset_project_id.schedule_d
    #         rec.schedule_e = rec.asset_project_id.schedule_e
    #         rec.schedule_f = rec.asset_project_id.schedule_f
    #         rec.schedule_g = rec.asset_project_id.schedule_g
    #         rec.schedule_h = rec.asset_project_id.schedule_h
    #         rec.schedule_i = rec.asset_project_id.schedule_i
    #         rec.schedule_a_eng = rec.asset_project_id.schedule_a_eng
    #         rec.schedule_b_eng = rec.asset_project_id.schedule_b_eng
    #         rec.schedule_c_eng = rec.asset_project_id.schedule_c_eng
    #         rec.schedule_d_eng = rec.asset_project_id.schedule_d_eng
    #         rec.schedule_e_eng = rec.asset_project_id.schedule_e_eng
    #         rec.schedule_f_eng = rec.asset_project_id.schedule_f_eng
    #         rec.schedule_g_eng = rec.asset_project_id.schedule_g_eng
    #         rec.schedule_h_eng = rec.asset_project_id.schedule_h_eng
    #         rec.schedule_i_eng = rec.asset_project_id.schedule_i_eng
    #         rec.sale_term_id = rec.asset_project_id.sale_term_id.id
    #         rec.payment_plan_ids = False
    #         if not rec.env.context.get('from_method'):
    #             rec.property_id = False
    #         pp_lines = rec.payment_plan_ids
    #         if rec.asset_project_id:
    #             for l in rec.asset_project_id.payment_plan_ids:
    #                 pp_lines += pp_lines.new({
    #                     'name': l.name,
    #                     'percentage': l.percentage,
    #                     'payment_date_disc': l.payment_date_disc,
    #                     'sale_id': rec.id,
    #                 })
    #         if pp_lines:
    #             rec.payment_plan_ids = pp_lines
    #         rec.admin_fee = rec.asset_project_id.admin_fee + rec.asset_project_id.vat_input_amount + rec.asset_project_id.other_income_amount

    @api.model
    def cron_dld_schedule(self,spa):
        sos = self.env['sale.order'].search([('id','=',spa)])
        for rec in sos:
            rec.payment_plan_ids = False
            pp_lines = rec.payment_plan_ids
            if rec.asset_project_id:
                for l in rec.asset_project_id.payment_plan_ids:
                    pp_lines += pp_lines.new({
                        'name': l.name,
                        'percentage': l.percentage,
                        'payment_date_disc': l.payment_date_disc,
                        'sale_id': rec.id,
                    })
            if pp_lines:
                rec.payment_plan_ids = pp_lines