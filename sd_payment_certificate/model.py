from odoo import models, fields, api, _
from datetime import datetime
from odoo.exceptions import UserError
from dateutil.relativedelta import relativedelta


class PaymentCertificate(models.Model):
    _name = 'payment.certificate'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Payment Certificate'

    name = fields.Char('Name', tracking=True)
    contractor = fields.Many2one('res.partner', 'Contractor', tracking=True)
    pc_date = fields.Date("PC Date", tracking=True)
    reference = fields.Char('Reference No', tracking=True)
    project_costing = fields.Many2one('project.costing', 'Related Project', tracking=True)
    pc_amount = fields.Float('PC Amount')
    remarks = fields.Text('Remarks')
    payment_certificate_line = fields.One2many("consume.material.line", 'payment_certificate', 'Consume Material Lines')
    payment_ids = fields.One2many("account.payment", 'payment_certificate', 'Payments')
    move_ids = fields.One2many('account.move', 'costing_bill_id', string='Bills', tracking=True)
    costing_contractor = fields.Many2one('costing.contractor','Costing Contractor')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirm', 'Confirmed'),
        ('cancel', 'Canceled')
    ], string='Status', readonly=True, default='draft')

    def action_confirm(self):
        self.write({'state': 'confirm'})

    def action_cancel(self):
        self.write({'state': 'cancel'})

    def back_to_draft(self):
        self.write({'state': 'draft'})


class ConsumedMaterialLine(models.Model):
    _name = 'consume.material.line'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Consumed Material Line Form'

    project_costing = fields.Many2one('project.costing', 'Project Costing')
    related_planned_boq = fields.Many2one('planned.boq', 'Related Planned BOQ')
    planned_qty = fields.Float('Planned Qty', related='related_planned_boq.activity_quantity', store=True,
                               tracking=True)
    unit = fields.Char('Unit', related='related_planned_boq.unit', store=True, tracking=True)
    planned_per_unit_price = fields.Float('Planned Per Unit Price', related='related_planned_boq.unit_price',
                                          store=True, tracking=True)
    consumed_qty = fields.Float('Consumed Qty')
    actual_price = fields.Float('Actual Price Per Unit')
    total_price = fields.Float('Total Price')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirm', 'Confirmed'),
        ('cancel', 'Canceled')
    ], string='Status', readonly=True, default='draft', tracking=True)
    # sequence = fields.Integer('Serial No.', compute='_get_line_numbers', tracking=True)
    payment_certificate = fields.Many2one("payment.certificate", 'Payment Certificate')

    # def _get_line_numbers(self):
    #     for rec in self:
    #         if rec.payment_certificate:
    #             line_num = 0
    #             for line in rec.env['consume.material.line'].search([('payment_certificate', '!=', False)],
    #                                                                 order='pc_date asc'):
    #                 line_num += 1
    #                 if line.id == rec.id:
    #                     break
    #             rec.sequence = line_num
    #         else:
    #             rec.sequence = 0

    def action_confirm(self):
        self.write({'state': 'confirm'})

    def action_cancel(self):
        self.write({'state': 'cancel'})

    def back_to_draft(self):
        self.write({'state': 'draft'})


class AccountPayment(models.Model):
    _inherit = "account.payment"

    payment_certificate = fields.Many2one("payment.certificate", 'Payment Certificate')


class AllContractor(models.Model):
    _inherit = "costing.contractor"

    payment_certificate_ids = fields.One2many('payment.certificate', 'costing_contractor', string='Payment Certificate',
                             tracking=True)
    total_pc_value = fields.Float('Total PC Value', compute="payment_certicate_ids", tracking=True, store=True)

    @api.depends('payment_certificate_ids','payment_certificate_ids.pc_amount')
    def payment_certicate_ids(self):
        for rec in self:
            payments = self.env['payment.certificate'].search([('contractor', 'in', rec.contractor.ids)])
            for recss in payments:
                rec.total_pc_value += recss.pc_amount


class ProjectCosting(models.Model):
    _inherit = "project.costing"

    pc_ids = fields.One2many('payment.certificate', 'project_costing', string='Payment Certificate IDs', tracking=True)
    total_pc_value = fields.Float('Total PC Value', compute="pc_vals", tracking=True, store=True)

    @api.depends('contractor_id', 'contractor_id.total_pc_value')
    def pc_vals(self):
        pc = 0
        for rec in self:
            for recss in rec.contractor_id:
                pc += recss.total_pc_value
            rec.total_pc_value = pc

    @api.depends('contractor_id',
                 'contractor_id.advance_payments','contractor_id.total_payments',
                 'contractor_id.total_invoiced','contractor_id.total_pc_value')
    def get_contractor_vals(self):
        retention = 0
        retention_perc = 0
        advance = 0
        total = 0
        invoiced = 0
        pc = 0
        for rec in self:
            for recss in rec.contractor_id:
                retention += recss.retention_amount
                retention_perc += recss.retention_amount_perc
                advance += recss.advance_payments
                total += recss.total_payments
                invoiced += recss.total_invoiced
                pc += recss.total_pc_value
            # rec.retention_amount = retention
            # rec.retention_amount_perc = retention_perc
            rec.advance_payments = advance
            rec.total_payments = total
            rec.total_invoiced = invoiced
            rec.total_pc_value = pc

class AccountBills(models.Model):
    _inherit = "account.move"

    costing_bill_id = fields.Many2one('payment.certificate', 'Payment Certificate')


class PlannedBoq(models.Model):
    _name = 'planned.boq'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Planned BOQ'

    sequence = fields.Char('Sequence', readonly=True)
    name = fields.Char('Activity Name', tracking=True)
    start_date = fields.Date('Start Date', tracking=True)
    end_date = fields.Date('End Date', tracking=True)
    duration = fields.Char('Duration', compute='get_dates_difference', tracking=True)
    main_activity = fields.Many2one('planned.boq', 'Main Activity', tracking=True)
    main_activity_tab = fields.Many2many("planned.boq", 'new_users', 'visible_id', 'main_activity', string='Users')
    project_costing = fields.Many2one('project.costing', 'Project Costing', tracking=True)

    activity_quantity = fields.Float('Activity Quantity', tracking=True)
    unit = fields.Char('Unit', tracking=True)
    unit_price = fields.Float('Unit Price', tracking=True)
    activity_price = fields.Float('Activity Price', tracking=True)
    sub_activity_total = fields.Float('Sub Activities Total', tracking=True)
    total = fields.Float('Total', tracking=True)
    boq_planned_lines = fields.One2many("consume.material.line", 'related_planned_boq', 'Consume Material Lines')

    @api.depends('start_date', 'end_date')
    def get_dates_difference(self):
        for rec in self:
            difference2 = 0
            if rec.start_date and rec.end_date:
                if rec.end_date < rec.start_date:
                    raise UserError('End date is greater then start date')
                difference = relativedelta(rec.end_date + relativedelta(days=1), rec.start_date)
                difference2 = str(difference.years) + ' Years ' + str(difference.months) + ' Months ' \
                              + str(difference.days) + ' Days '
            rec.duration = difference2

    @api.model
    def create(self, vals):
        if not vals.get('sequence', ''):
            vals['sequence'] = self.env['ir.sequence'].next_by_code(
                'planned.boq')
        result = super(PlannedBoq, self).create(vals)
        return result

    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirm', 'Confirmed'),
        ('cancel', 'Canceled')
    ], string='Status', readonly=True, default='draft', tracking=True)

    def action_confirm(self):
        self.write({'state': 'confirm'})

    def action_cancel(self):
        self.write({'state': 'cancel'})

    def back_to_draft(self):
        self.write({'state': 'draft'})
