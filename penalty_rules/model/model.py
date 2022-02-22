# -*- coding: utf-8 -*-
from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

class WaiveOff(models.TransientModel):
    _name = 'waive.off'
    _description = 'Waive Off'

    type = fields.Selection([('full','Full'),('partial','Partial')], "Type", required=True, default='full')
    amount = fields.Float("Total Penalty Amount", readonly=True)
    already_waive_off = fields.Boolean("Already Waive Off", readonly=True)
    already_waive_off_amount = fields.Float("Already Waive Off", readonly=True)
    waive_off_amount = fields.Float("Waive Off Amount")
    to_reduce = fields.Boolean('Reduce Waive Off')
    to_reduce_amount = fields.Float('Reduce By Amount')
    penalty_status = fields.Char(' Penalty Status')


    def action_confirm(self):
        rule_id = self.env.context['active_id']
        rule_ids = self.env['penalty.rules'].search([('id','=',rule_id)])
        if rule_ids:
            if self.already_waive_off:
                if self.to_reduce:
                    new_amount = self.already_waive_off_amount - self.to_reduce_amount
                    if self.to_reduce_amount > self.already_waive_off_amount:
                        raise UserError(_("You can not reduce more then waive off amount"))
                    rule_ids.waive_off_amount = new_amount
                    if new_amount == 0:
                        rule_ids.penalty_status = 'charged'
                    else:
                        rule_ids.penalty_status = 'partially'
                else:
                    new_amount = self.already_waive_off_amount + self.waive_off_amount
                    if new_amount > rule_ids.penalty_amount:
                        raise UserError(_("Waive Off Amount Should be Less then Penalty Amount"))
                    rule_ids.waive_off_amount = new_amount
                    if new_amount == self.amount:
                        rule_ids.penalty_status = 'waive_off'
                    else:
                        rule_ids.penalty_status = 'partially'
            else:
                if self.waive_off_amount > rule_ids.penalty_amount:
                    raise UserError(_("Waive Off Amount Should be Less then Penalty Amount"))
                if self.type == 'partial':
                    rule_ids.waive_off_amount = self.waive_off_amount
                    if self.waive_off_amount == self.amount:
                        rule_ids.penalty_status = 'waive_off'
                    else:
                        rule_ids.penalty_status = 'partially'
                else:
                    rule_ids.waive_off_amount = rule_ids.penalty_amount
                    rule_ids.penalty_status = 'waive_off'


class PenaltyRules(models.Model):
    _name = 'penalty.rules'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Penalty Rules'

    installment_start_value = fields.Float('Instalment Start Value', tracking=True)
    installment_ending_value = fields.Float('Instalment Ending Value', tracking=True)
    incremental_days_start = fields.Float('Incremental Days Start', tracking=True)
    incremental_days_end = fields.Float('Incremental Days End', tracking=True)
    delay_days = fields.Float('Delay Days', tracking=True)
    penalty_criteria = fields.Selection([('fixed','Fixed'),('pecentage','Percentage')], string='Penalty Criteria', default='fixed', tracking=True)
    penalty_amount = fields.Float(string='Penalty Amount', tracking=True)
    waive_off_amount = fields.Float(string='Waive Off Amount', tracking=True)
    first_penalty_project_id = fields.Many2one('account.asset.asset', 'First Penalty Project', domain="[('project', '=', True)]")
    recurring_penalty_project_id = fields.Many2one('account.asset.asset', 'Recurring Penalty Project', domain="[('project', '=', True)]")
    first_penalty_srs_id = fields.Many2one('sale.rent.schedule', 'First Penalty Related Installment')
    recurring_penalty_srs_id = fields.Many2one('sale.rent.schedule', 'Recurring Penalty  Related Installment')

    recurring_id = fields.Integer('Recurring Penalty', tracking=True)
    penalty_status = fields.Selection([('charged','Penalty Charged'),('under_approval_waive_off','Under Approval To Waive Off'),
                                       ('partially','Partially Waive Off'),('waive_off','Waive Off')],
                                      string='Penalty Status', default='charged', tracking=True)
    asset_project_id = fields.Many2one('account.asset.asset', 'Project', domain="[('project', '=', True)]")
    property_id = fields.Many2one('account.asset.asset', string='Property', tracking=True)

    installment_delay_days = fields.Integer(string='Installment Delay Days', compute='get_installment_info', store=True)
    receipt_total = fields.Float(string='Received Amount', compute='get_installment_info', store=True)
    installment_status = fields.Selection([('paid', 'Paid'), ('unpaid', 'Unpaid'),
                                           ('partially_paid', 'Partially Paid'),('pdc_secured', 'PDC Secured'),
                                           ('default', 'Default'), ('cancel', 'Cancel')],
                                          string='Installment Status', compute='get_installment_info', store=True)
    pen_amt = fields.Float(string='OverDue Amount', compute='get_installment_info', store=True)
    related_installment = fields.Many2one('sale.rent.schedule', 'Related Installment', compute='get_installment_info', store=True, tracking=True)

    def action_fully_waive_off(self):
        for rec in self:
            flag = self.env['res.users'].has_group('base.group_erp_manager')
            if not flag:
                raise UserError('You are not allowed to perform this action')
            rec.waive_off_amount = rec.penalty_amount
            rec.penalty_status = 'waive_off'

    @api.depends('first_penalty_srs_id','first_penalty_srs_id.delay_days','first_penalty_srs_id.receipt_total',
                 'first_penalty_srs_id.installment_status','first_penalty_srs_id.pen_amt',
                 'recurring_penalty_srs_id','recurring_penalty_srs_id.delay_days','recurring_penalty_srs_id.receipt_total',
                 'recurring_penalty_srs_id.installment_status','recurring_penalty_srs_id.pen_amt')
    def get_installment_info(self):
        for rec in self:
            if rec.first_penalty_srs_id:
                rec.installment_delay_days = rec.first_penalty_srs_id.delay_days
                rec.receipt_total = rec.first_penalty_srs_id.receipt_total
                rec.installment_status = rec.first_penalty_srs_id.installment_status
                rec.pen_amt = rec.first_penalty_srs_id.pen_amt
                rec.related_installment = rec.first_penalty_srs_id.id
            if rec.recurring_penalty_srs_id:
                rec.installment_delay_days = rec.recurring_penalty_srs_id.delay_days
                rec.receipt_total = rec.recurring_penalty_srs_id.receipt_total
                rec.installment_status = rec.recurring_penalty_srs_id.installment_status
                rec.pen_amt = rec.recurring_penalty_srs_id.pen_amt
                rec.related_installment = rec.recurring_penalty_srs_id.id


    @api.onchange('asset_project_id')
    def onchange_asset_project_id(self):
        property_ids = self.env['account.asset.asset'].search(
            [('parent_id', '=', self.asset_project_id.id)])
        return {'domain': {'property_id': [('id', 'in', property_ids.ids)]}}

    # @api.depends('waive_off_amount')
    # def get_penalty_value(self):
    #     for rec in self:
    #         if rec.waive_off_amount:
    #             rec.penalty_amount = rec.penalty_amount - rec.waive_off_amount



    def action_under_approval_waive_off(self):
        self.penalty_status = 'under_approval_waive_off'

    @api.model
    def pr_get_project_property(self):
        pr = self.env['penalty.rules'].search([])
        for rec in pr:
            if rec.first_penalty_srs_id:
                rec.property_id = rec.first_penalty_srs_id.property_id.id
                rec.asset_project_id = rec.first_penalty_srs_id.asset_property_id.id
                rec.installment_delay_days = rec.first_penalty_srs_id.delay_days
                rec.receipt_total = rec.first_penalty_srs_id.receipt_total
                rec.installment_status = rec.first_penalty_srs_id.installment_status
                rec.pen_amt = rec.first_penalty_srs_id.pen_amt
                rec.related_installment = rec.first_penalty_srs_id.id
            if rec.recurring_penalty_srs_id:
                rec.property_id = rec.recurring_penalty_srs_id.property_id.id
                rec.asset_project_id = rec.recurring_penalty_srs_id.asset_property_id.id
                rec.installment_delay_days = rec.recurring_penalty_srs_id.delay_days
                rec.receipt_total = rec.recurring_penalty_srs_id.receipt_total
                rec.installment_status = rec.recurring_penalty_srs_id.installment_status
                rec.pen_amt = rec.recurring_penalty_srs_id.pen_amt
                rec.related_installment = rec.recurring_penalty_srs_id.id



    # already_waive_off = fields.Float("Already Waive Off", readonly=True)
    # waive_off_amount = fields.Float("Waive Off Amount")
    # to_reduce = fields.Boolean('Reduce Waive Off')
    # to_reduce_amount = fields.Float('Reduce By Amount')


    def action_waive_off(self):
        ctx = dict(
            rule_id = self.id,
            default_amount = self.penalty_amount,
            default_already_waive_off_amount = self.waive_off_amount,
            default_penalty_status = self.penalty_status,
        )
        if self.waive_off_amount:
            ctx.update({
                'default_already_waive_off' : True,
                'default_type' : 'partial'
            })
        if self.penalty_status == 'waive_off':
            ctx.update({
                'default_already_waive_off' : True,
                'default_to_reduce' : True
            })
        return {
            'name': _('Waive Off Wiz'),
            'view_mode': 'form',
            'res_model': 'waive.off',
            'view_id': self.env.ref('penalty_rules.waive_off_wizard').id,
            'type': 'ir.actions.act_window',
            'context': ctx,
            'target': 'new'
        }


class AccountAssetAsset(models.Model):
    _inherit = "account.asset.asset"

    first_penalty_ids = fields.One2many('penalty.rules', 'first_penalty_project_id', 'First Penalty')
    recurring_penalty_ids = fields.One2many('penalty.rules', 'recurring_penalty_project_id', 'Recurring Penalty')


class SaleRentSchedule(models.Model):
    _inherit = "sale.rent.schedule"

    first_penalty_ids = fields.One2many('penalty.rules', 'first_penalty_srs_id', 'First Penalty')
    recurring_penalty_ids = fields.One2many('penalty.rules', 'recurring_penalty_srs_id', 'Recurring Penalty')
    penalty = fields.Float('Penalty', compute='get_penalty_amount', store=True, tracking=True)

    @api.model
    def remove_penalty_value(self):
        srs = self.env['sale.rent.schedule'].search([('penalty', '>', 0),('state', '=', 'confirm')])
        for rec in srs:
            if not rec.first_penalty_ids:
                rec.write({'penalty' : 0})

    @api.depends('first_penalty_ids','first_penalty_ids.penalty_amount','first_penalty_ids.waive_off_amount',
                 'recurring_penalty_ids','recurring_penalty_ids.penalty_amount','recurring_penalty_ids.waive_off_amount')
    def get_penalty_amount(self):
        for rec in self:
            total = 0
            if rec.first_penalty_ids:
                for fline in rec.first_penalty_ids:
                    if fline.waive_off_amount:
                        total += fline.penalty_amount - fline.waive_off_amount
                    else:
                        total+= fline.penalty_amount
            if rec.recurring_penalty_ids:
                for rline in rec.recurring_penalty_ids:
                    if rline.waive_off_amount:
                        total += rline.penalty_amount - rline.waive_off_amount
                    else:
                        total+= rline.penalty_amount
            rec.penalty = total

    @api.model
    def del_penalty_all(self):
        self.env.cr.execute('delete from penalty_rules where first_penalty_srs_id is not null or recurring_penalty_srs_id is not null')

    @api.model
    def srs_penalty_auto(self):
        srs = self.env['sale.rent.schedule'].search([('asset_property_id', '=', 472),('installment_status', 'in', ['unpaid','default','partially_paid']),('delay_days','!=',False),('sale_id','!=',False)], order="start_date ASC")
        for rec in srs:
            r_ok = False
            prule = rec.env['penalty.rules']
            if rec.asset_property_id.first_penalty_ids:
                # fline_lines = rec.first_penalty_ids
                for fline1 in rec.asset_property_id.first_penalty_ids:
                    if rec.amount >= fline1.installment_start_value and rec.amount <= fline1.installment_ending_value and rec.delay_days < fline1.delay_days * (-1):
                        r_ok = True
                for fline in rec.asset_property_id.first_penalty_ids:
                    if rec.amount >= fline.installment_start_value and rec.amount <= fline.installment_ending_value and rec.delay_days < fline.delay_days * (-1) and not rec.first_penalty_ids:
                        fnline = prule.create({
                            'delay_days': fline.delay_days * (-1),
                            'penalty_amount': fline.penalty_amount,
                            'asset_project_id': rec.asset_property_id.id,
                            'property_id': rec.property_id.id,
                            'first_penalty_srs_id': rec.id,
                        })
                # if fline_lines:
                #     rec.first_penalty_ids = fline_lines
            if rec.asset_property_id.recurring_penalty_ids and r_ok:
                # rline_lines = rec.recurring_penalty_ids
                for rline in rec.asset_property_id.recurring_penalty_ids:
                    previous = rec.env['penalty.rules'].search([('recurring_id','=', rline.id),('recurring_penalty_srs_id','=', rec.id)])
                    if previous:
                        continue
                    if rec.delay_days < rline.incremental_days_start * -1:
                        rnline = prule.create(  {
                            'delay_days': rline.incremental_days_start * -1,
                            'recurring_id': rline.id,
                            'penalty_amount': rline.penalty_amount,
                            'asset_project_id': rec.asset_property_id.id,
                            'property_id': rec.property_id.id,
                            'recurring_penalty_srs_id': rec.id,
                        })
                    # if rec.delay_days <= rline.incremental_days_start * -1 and rec.delay_days >= rline.incremental_days_end * -1:
                    #     rnline = prule.create({
                    #         'delay_days': rline.incremental_days_start * -1,
                    #         'recurring_id': rline.id,
                    #         'penalty_amount': rline.penalty_amount,
                    #         'asset_project_id': rec.asset_property_id.id,
                    #         'property_id': rec.property_id.id,
                    #         'recurring_penalty_srs_id': rec.id,
                    #     })
                # if rline_lines:
                #     rec.recurring_penalty_ids = rline_lines
