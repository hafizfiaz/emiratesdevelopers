from odoo import models, fields, api, _
from datetime import datetime
from odoo.exceptions import UserError
from dateutil.relativedelta import relativedelta


class CostingContractor(models.Model):
    _name = 'costing.contractor'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Costing Contractor'

    name = fields.Char('Name', tracking=True)
    company_id = fields.Many2one('res.company', string='Company', required=True,
                                 default=lambda self: self.env.user.company_id)
    contractor = fields.Many2one('res.partner', 'Contractor', tracking=True)
    project = fields.Many2one('project.costing', 'Related Project Costing', tracking=True)
    plot_size_sqft = fields.Float('Plot Size Sqft', tracking=True)
    saleable_area_sqft = fields.Float('Saleable Area Sqft', tracking=True)
    construction_start_date = fields.Date("Construction Start Date", tracking=True)
    construction_end_date = fields.Date("Construction End Date", tracking=True)
    duration = fields.Char('Planned Duration', compute='get_dates_difference', tracking=True, store=True)
    actual_duration = fields.Char('Actual Duration Till Date', compute='get_current_difference', tracking=True,
                                  store=True)
    land_cost = fields.Float('Land Cost', tracking=True)
    total_contract_value = fields.Float('Total Contract Value', tracking=True)
    consultancy_cost = fields.Float('Consultancy Cost', tracking=True)
    other_cost = fields.Float('Other Cost', tracking=True)
    total_project_cost = fields.Float('Total Project Cost', compute='get_total_cost', store=True, tracking=True)
    retention_amount = fields.Float('Retention Amount', tracking=True)
    retention_amount_perc = fields.Float('Retention Amount Percentage', compute='retention_perc', tracking=True,
                                         store=True)
    total_payments = fields.Float('Net Payments', compute='net_payment_receipt', tracking=True, store=True)
    total_payments_amount = fields.Float('Payments Total', compute='payment_posted_sum', tracking=True, store=True)
    total_receipts_amount = fields.Float('Receipts Total', compute='receipts_posted_sum', tracking=True, store=True)
    total_invoiced = fields.Float('Total Invoiced', compute='payment_invoice_sum', tracking=True, store=True)
    advance_payments = fields.Float('Advance Payment', compute='invoiced_payment_sum', tracking=True, store=True)
    receipt_lines = fields.One2many('account.payment', 'contractor_receipt_id', 'Payments', tracking=True)
    receipt_ids = fields.One2many('account.payment', 'contractor_receipts_id', 'Receipts', tracking=True)
    move_ids = fields.One2many('account.move', 'contractor_bill_id', string='Bills', tracking=True)
    other_bill_ids = fields.One2many('account.move', 'other_bill_id', string='Other Bills', tracking=True)

    add_charges_ids = fields.One2many('costing.contractor.lines', 'add_id', string='Add', tracking=True)
    less_charges_ids = fields.One2many('costing.contractor.lines', 'less_id', string='Less', tracking=True)

    @api.depends('construction_start_date', 'construction_end_date')
    def get_dates_difference(self):
        for rec in self:
            difference2 = 0
            if rec.construction_start_date and rec.construction_end_date:
                if rec.construction_end_date < rec.construction_start_date:
                    raise UserError('End date is greater then start date')
                difference = relativedelta(rec.construction_end_date + relativedelta(days=1),
                                           rec.construction_start_date)
                difference2 = str(difference.years) + ' Years ' + str(difference.months) + ' Months ' \
                              + str(difference.days) + ' Days '
            rec.duration = difference2

    @api.depends('construction_start_date')
    def get_current_difference(self):
        for rec in self:
            difference2 = 0
            current_date = datetime.now().date()
            if rec.construction_start_date and current_date:
                if current_date < rec.construction_start_date:
                    raise UserError('Current date is greater then start date')
                difference = relativedelta(current_date + relativedelta(days=1), rec.construction_start_date)
                difference2 = str(difference.years) + ' Years ' + str(difference.months) + ' Months ' \
                              + str(difference.days) + ' Days '
            rec.actual_duration = difference2

    @api.depends('total_payments_amount','total_receipts_amount')
    def net_payment_receipt(self):
        for rec in self:
            rec.total_payments = rec.total_payments_amount - rec.total_receipts_amount

    @api.depends('receipt_lines','receipt_lines.amount','receipt_lines.state')
    def payment_posted_sum(self):
        for rec in self:
            amount =0
            for recs in rec.receipt_lines:
                if recs.state not in ['rejected','cancelled']:
                    amount += recs.amount
            rec.total_payments_amount = amount

    @api.depends('receipt_ids','receipt_ids.amount','receipt_ids.state')
    def receipts_posted_sum(self):
        for rec in self:
            amount =0
            for recs in rec.receipt_ids:
                if recs.state not in ['rejected','cancelled']:
                    amount += recs.amount
            rec.total_receipts_amount = amount

    @api.depends('move_ids','move_ids.amount_total')
    def payment_invoice_sum(self):
        for rec in self:
            amount=0
            for recss in rec.move_ids:
                # for sd in recss.invoice_line_ids:
                amount += recss.amount_total
            rec.total_invoiced = amount

    @api.depends('total_payments', 'total_invoiced')
    def invoiced_payment_sum(self):
        for rec in self:
            rec.advance_payments = rec.total_payments - rec.total_invoiced

    @api.depends('retention_amount', 'total_contract_value')
    def retention_perc(self):
        for rec in self:
            if rec.retention_amount and rec.total_contract_value:
                rec.retention_amount_perc = rec.retention_amount / rec.total_contract_value * 100

    @api.depends('land_cost', 'total_contract_value', 'consultancy_cost', 'other_cost')
    def get_total_cost(self):
        for rec in self:
            rec.total_project_cost = rec.land_cost + rec.total_contract_value + rec.consultancy_cost + rec.other_cost


class CostingContractorLine(models.Model):
    _name = 'costing.contractor.lines'
    _description = 'Costing Contractor Lines'

    detail = fields.Char('Detail')
    amount = fields.Float('Amount')
    date = fields.Date("Date")
    remarks = fields.Char("Remarks")
    add_id = fields.Many2one('costing.contractor', 'Costing Contractor')
    less_id = fields.Many2one('costing.contractor', 'Costing Contractor')


class AccountPayment(models.Model):
    _inherit = "account.payment"

    contractor_receipt_id = fields.Many2one('costing.contractor', 'Costing Contractor Payments')
    contractor_receipts_id = fields.Many2one('costing.contractor', 'Costing Contractor Receipts')


class AccountBills(models.Model):
    _inherit = "account.move"

    contractor_bill_id = fields.Many2one('costing.contractor', 'Costing Contractor')
    other_bill_id = fields.Many2one('costing.contractor', 'Costing Contractor')

