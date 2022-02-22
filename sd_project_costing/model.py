from odoo import models, fields, api, _
from odoo.exceptions import UserError
from dateutil.relativedelta import relativedelta
from datetime import datetime, timedelta, date


class ProjectCosting(models.Model):
    _name = 'project.costing'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Project Costing'

    def _get_default_model_ids(self):
        return self.env['ir.model'].search([('model', '=', self._name)])[0].id

    name = fields.Char('Name', tracking=True)
    contractor = fields.Many2one('res.partner', 'Contractor', tracking=True)
    contractor_id = fields.One2many('costing.contractor', 'project', 'Contractor ID', tracking=True)
    project = fields.Many2one('account.asset.asset', 'Related Project', domain="[('project', '=', True)]",
                              tracking=True)
    plot_size_sqft = fields.Float('Plot Size Sqft', tracking=True)
    saleable_area_sqft = fields.Float('Saleable Area Sqft', tracking=True)
    construction_start_date = fields.Date("Construction Start Date", tracking=True)
    construction_end_date = fields.Date("Construction End Date", tracking=True)
    duration = fields.Char('Planned Duration', compute='get_dates_difference', tracking=True, store=True)
    actual_duration = fields.Char('Actual Duration Till Date', compute='get_current_difference', tracking=True,
                                  store=True)
    handover_date = fields.Date('Expected Handover Date', related="project.handover_date", tracking=True, store=True)

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


    land_cost = fields.Float('Land Cost', tracking=True)
    total_contract_value = fields.Float('Total Contract Value', tracking=True)
    consultancy_cost = fields.Float('Consultancy Cost', tracking=True)
    other_cost = fields.Float('Other Cost', tracking=True)
    total_project_cost = fields.Float('Total Project Cost', compute='get_total_cost', store=True, tracking=True)
    retention_amount = fields.Float('Retention Amount', tracking=True)
    retention_amount_perc = fields.Float('Retention Amount Percentage', tracking=True)
    total_payments = fields.Float('Total Payment', compute="get_contractor_vals", tracking=True, store=True)
    total_invoiced = fields.Float('Total Invoiced', compute="get_contractor_vals", tracking=True, store=True)
    advance_payments = fields.Float('Advance Payment', compute="get_contractor_vals", tracking=True, store=True)
    stage_id = fields.Many2one('project.stage', 'Status')
    model_id = fields.Many2one('ir.model', string='Projects', default=_get_default_model_ids)
    state_change = fields.Char(compute="get_state", store=True, string="State Change", tracking=True)
    receipt_lines = fields.One2many('account.payment', 'costing_receipt_id', 'Payments', tracking=True)
    move_ids = fields.One2many('account.move', 'costing_bill_id', string='Bills', tracking=True)
    other_bill_ids = fields.One2many('account.move', 'costing_other_bill_id', string='Other Bills', tracking=True)
    add_charges_ids = fields.One2many('project.costing.lines', 'add_id', string='Add', tracking=True)
    less_charges_ids = fields.One2many('project.costing.lines', 'less_id', string='Less', tracking=True)
    savings = fields.Float('Savings', tracking=True)
    vat_perc = fields.Float('VAT %', tracking=True)
    net_cost_exc_vat = fields.Float('Net Cost Exc VAT', compute="get_cost_exc_vat", tracking=True, store=True)

    all_contractors = fields.Many2one('res.partner', 'All Contractors', related='contractor_id.contractor', store=True)

    land_cost_ap_ledger = fields.Float('Land Cost As Per Ledger', tracking=True)
    contract_value_ap_ledger = fields.Float('Contract Value As Per Ledger', tracking=True)
    consultancy_cost_ap_ledger = fields.Float('Consultancy Cost As Per Ledger', tracking=True)
    other_cost_ap_ledger = fields.Float('Other Cost As Per Ledger', tracking=True)

    @api.model
    def cron_values_ap_ledger(self):
        june_30 = date(2019, 6, 30)
        for rec in self.env['project.costing'].search([]):
            if rec.project:
                land_cost_tag = ''
                contract_tag = ''
                consultancy_tag = ''
                other_tag = ''
                if rec.project.name == 'Samana Golf Avenue':
                    land_cost_tag = 'Land Cost- Golf'
                    contract_tag = 'Project Cost- Golf'
                    consultancy_tag = 'Consultancy Cost- Golf'
                    other_tag = 'Other Project Cost- Golf'
                if rec.project.name == 'Samana Greens':
                    land_cost_tag = 'Land Cost- Samana Greens'
                    contract_tag = 'Project Cost- Greens'
                    consultancy_tag = 'Consultancy Cost- Greens'
                    other_tag = 'Other Project Cost- Greens'
                if rec.project.name == 'Samana Hills':
                    land_cost_tag = 'Land Cost- Hills'
                    contract_tag = 'Project Cost- Hills'
                    consultancy_tag = 'Consultancy Cost- Hills'
                    other_tag = 'Other Project Cost- Hills'
                if rec.project.name == 'Samana Waves':
                    land_cost_tag = 'Land Cost- Waves'
                    contract_tag = 'Project Cost- Waves'
                    consultancy_tag = 'Consultancy Cost- Waves'
                    other_tag = 'Other Project Cost- Waves'
                if rec.project.name == 'Samana Park Views':
                    land_cost_tag = 'Land Cost- Park View'
                    contract_tag = 'Project Cost- Park Views'
                    consultancy_tag = 'Consultancy Cost- Park Views'
                    other_tag = 'Other Project Cost- Park View'
                land_cost_tags = self.env['account.account.tag'].search([('name', '=', land_cost_tag)], limit=1)
                contract_tags = self.env['account.account.tag'].search([('name', '=', contract_tag)], limit=1)
                consultancy_tags = self.env['account.account.tag'].search([('name', '=', consultancy_tag)], limit=1)
                other_tags = self.env['account.account.tag'].search([('name', '=', other_tag)], limit=1)
                land_cost_sum = 0
                contract_sum = 0
                consultancy_sum = 0
                other_sum = 0
                aml = self.env['account.move.line'].search([('parent_state', '=', 'posted'), ('date', '>', june_30)])
                if land_cost_tags:
                    land_cost_sum = sum(aml.filtered(lambda m: land_cost_tags.id in m.account_id.tag_ids.ids).mapped("balance"))
                if contract_tags:
                    contract_sum = sum(aml.filtered(lambda m: contract_tags.id in m.account_id.tag_ids.ids).mapped("balance"))
                if consultancy_tags:
                    consultancy_sum = sum(aml.filtered(lambda m: consultancy_tags.id in m.account_id.tag_ids.ids).mapped("balance"))
                if other_tags:
                    other_sum = sum(aml.filtered(lambda m: other_tags.id in m.account_id.tag_ids.ids).mapped("balance"))
                rec.land_cost_ap_ledger = land_cost_sum
                rec.contract_value_ap_ledger = contract_sum
                rec.consultancy_cost_ap_ledger = consultancy_sum
                rec.other_cost_ap_ledger = other_sum

    @api.depends('total_contract_value', 'savings')
    def get_cost_exc_vat(self):
        for rec in self:
            rec.net_cost_exc_vat = rec.total_contract_value - rec.savings

    @api.depends('contractor_id', 'contractor_id.advance_payments', 'contractor_id.total_payments',
                 'contractor_id.total_invoiced')
    def get_contractor_vals(self):
        retention = 0
        retention_perc = 0
        advance = 0
        total = 0
        invoiced = 0
        pc = 0
        for rec in self:
            for recss in rec.contractor_id:
                # retention += recss.retention_amount
                # retention_perc += recss.retention_amount_perc
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

    # @api.depends('other_bill_ids')
    # def payment_posted_sum(self):
    #     for rec in self:
    #         payments = self.env['account.payment'].search(
    #             [('state', '=', 'posted'), ('partner_id', 'in', rec.contractor_id.contractor.ids)])
    #         summ = len(payments)
    #         rec.total_payments = summ
    #
    # @api.depends('move_ids')
    # def payment_invoice_sum(self):
    #     for rec in self:
    #         payments = self.env['account.move'].search([('partner_id', 'in', rec.contractor_id.contractor.ids)])
    #         summ = len(payments)
    #         rec.total_invoiced = summ

    @api.depends('stage_id')
    def get_state(self):
        for rec in self:
            rec.state_change = rec.stage_id.name

    @api.depends('retention_amount', 'total_contract_value')
    def retention_perc(self):
        for rec in self:
            if rec.retention_amount and rec.total_contract_value:
                rec.retention_amount_perc = rec.retention_amount / rec.total_contract_value * 100

    @api.depends('land_cost', 'total_contract_value', 'consultancy_cost', 'other_cost')
    def get_total_cost(self):
        for rec in self:
            rec.total_project_cost = rec.land_cost + rec.total_contract_value + rec.consultancy_cost + rec.other_cost

    def write(self, vals):
        result = super(ProjectCosting, self).write(vals)
        stage_id = vals.get('stage_id', False)
        if stage_id:
            stage_ids = self.env['project.stage'].search([('id', '=', stage_id)])
            if stage_ids.mail_template_id:
                model_id = self.env['ir.model'].search([('model', '=', self._name)])
                email_template = stage_ids.mail_template_id
                email_template.email_to = stage_ids.get_partner_ids(stage_ids.responsible_id)
                email_template.model_id = model_id.id
                email_template.send_mail(self.id, force_send=True)
            if self.env.user.id not in stage_ids.responsible_id.ids:
                raise UserError(_("Only Responsible Person Can Change the Stage"))
        return result


class ProjectCostingLine(models.Model):
    _name = 'project.costing.lines'
    _description = 'Project Costing Lines'

    detail = fields.Char('Detail')
    amount = fields.Float('Amount')
    date = fields.Date("Date")
    remarks = fields.Char("Remarks")
    add_id = fields.Many2one('project.costing', 'Project Costing')
    less_id = fields.Many2one('project.costing', 'Project Costing')


class AccountPayment(models.Model):
    _inherit = "account.payment"

    costing_receipt_id = fields.Many2one('project.costing', 'Project Costing')


class AccountBills(models.Model):
    _inherit = "account.move"

    costing_bill_id = fields.Many2one('project.costing', 'Project Costing')
    costing_other_bill_id = fields.Many2one('project.costing', 'Project Costing')
