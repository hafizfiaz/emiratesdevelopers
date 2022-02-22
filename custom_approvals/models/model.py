# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
from odoo.exceptions import UserError, ValidationError
import time
from datetime import datetime
from datetime import timedelta


class Approval(models.Model):
    _name = 'approval.approval'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Name', required=True, tracking=True)
    previous_state = fields.Char(string='Previous State')
    amount = fields.Float(string='Amount', tracking=True)
    approval_type_id = fields.Many2one('approval.type', string='Approval Type', tracking=True)
    remarks = fields.Text(string='Remarks', tracking=True)
    gm_remarks = fields.Text(string='GM Remarks', tracking=True)
    is_gm_state = fields.Boolean(string='Is GM state', default=False, tracking=True)
    is_ceo_state = fields.Boolean(string='Is CEO state', default=False, tracking=True)
    ceo_remarks = fields.Text(string='CEO Remarks', tracking=True)
    state = fields.Selection([('draft', 'Draft'), ('under_manager_review', 'Under Manager Review'),
                               ('under_accounts_verification', 'Under Accounts Verification'),
                               ('under_gm_review', 'Under COO Review'),
                               ('under_ceo_review', 'Under CEO Review'),
                               ('approve', 'Approved'),
                               ('refused', 'Refused'),
                               ('rejected', 'Rejected'),('cancelled', 'Cancelled')], string="status",
                                default='draft', tracking=True)
    invoice_check = fields.Boolean(string="Invoice", related='approval_type_id.invoice_check', store=True)
    # invisible_check = fields.Boolean(string="Invisible", store=True, compute="_compute_invoice")
    invoice_ids = fields.One2many('account.move', 'approval_id', string="Invoices")
    sequence = fields.Char('Sequence', readonly=True)
    approve_user_id = fields.Many2one('res.users', string="Approved By")

    @api.model
    def create(self, values):
        sequence = self.env['ir.sequence'].next_by_code('approval.approval')
        values['sequence'] = sequence
        return super(Approval, self).create(values)


    def action_create_bill(self):
        ctx = self._context.copy()
        ctx.update(
            {'default_approval_id': self.id, 'approval': True, 'default_move_type': 'in_invoice', 'move_type': 'in_invoice',
             'journal_type': 'purchase','default_approved_by':self.approve_user_id.id})
        view_id = self.env.ref('account.view_move_form').id
        model = 'account.move'
        return {
            'name': _('Create invoice/bill'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': model,
            'view_id': view_id,
            'context': ctx,
        }

    @api.model
    def _cron_add_approval(self):
        for data in self.search([]):
            for line in data.invoice_ids:
                # line.approval_id = data.id
                line.write({'approval_id': data.id})


    
    def action_draft(self):
        self.write({'state': 'draft'})

    
    def action_submit_to_manager(self):
        self.write({'previous_state': self.state})
        if self.approval_type_id.manager_review:
            self.write({'state': 'under_manager_review'})
        if not self.approval_type_id.manager_review and self.approval_type_id.accounts_review:
            self.write({'state': 'under_accounts_verification'})
        if not self.approval_type_id.manager_review and not self.approval_type_id.accounts_review and self.approval_type_id.gm_review:
            self.write({'state': 'under_gm_review','is_gm_state': True})
        if not self.approval_type_id.manager_review and not self.approval_type_id.accounts_review and not self.approval_type_id.gm_review and self.approval_type_id.ceo_review:
            self.write({'state': 'under_ceo_review','is_ceo_state': True})
        if not self.approval_type_id.manager_review and not self.approval_type_id.accounts_review and not self.approval_type_id.gm_review and not self.approval_type_id.ceo_review:
            self.write({'state': 'approve'})


    
    def action_refuse(self):
        users = []
        for rec in self.approval_type_id.manager_ids:
            users.append(rec.id)
        if self.env.user.id in users:
            self.write({'previous_state': self.state})
            self.write({'state': 'refused'})
        else:
            raise UserError(_("You are not allowed to perform this action"))

    
    def action_manager_cancel(self):
        users = []
        for rec in self.approval_type_id.manager_ids:
            users.append(rec.id)
        if self.env.user.id in users:
            self.write({'previous_state': self.state})
            self.write({'state': 'cancelled'})
        else:
            raise UserError(_("You are not allowed to perform this action"))

    
    def action_accounts_cancel(self):
        users = []
        for rec in self.approval_type_id.accounts_approvers_ids:
            users.append(rec.id)
        if self.env.user.id in users:
            self.write({'previous_state': self.state})
            self.write({'state': 'cancelled'})
        else:
            raise UserError(_("You are not allowed to perform this action"))


    
    def action_under_review(self):
        users = []
        for rec in self.approval_type_id.manager_ids:
            users.append(rec.id)
        if self.env.user.id in users:
            self.write({'previous_state': self.state})
            if self.approval_type_id.accounts_review:
                self.write({'state': 'under_accounts_verification'})
            if not self.approval_type_id.accounts_review and self.approval_type_id.gm_review:
                self.write({'state': 'under_gm_review','is_gm_state': True})
            if not self.approval_type_id.accounts_review and not self.approval_type_id.gm_review and self.approval_type_id.ceo_review:
                self.write({'state': 'under_ceo_review','is_ceo_state': True})
            if not self.approval_type_id.accounts_review and not self.approval_type_id.gm_review and not self.approval_type_id.ceo_review:
                self.write({'state': 'approve'})
        else:
            raise UserError(_("You are not allowed to perform this action"))


    
    def action_under_accounts_verification(self):
        users = []
        for rec in self.approval_type_id.accounts_approvers_ids:
            users.append(rec.id)
        if self.env.user.id in users:
            self.write({'previous_state': self.state})
            if self.approval_type_id.gm_review:
                self.write({'state': 'under_gm_review','is_gm_state': True})
            if not self.approval_type_id.gm_review and self.approval_type_id.ceo_review:
                self.write({'state': 'under_ceo_review','is_ceo_state': True})
            if not self.approval_type_id.gm_review and not self.approval_type_id.ceo_review:
                self.write({'state': 'approve'})
        else:
            raise UserError(_("You are not allowed to perform this action"))

    
    def action_accounts_reject(self):
        users = []
        for rec in self.approval_type_id.accounts_approvers_ids:
            users.append(rec.id)
        if self.env.user.id in users:
            self.write({'previous_state': self.state})
            self.write({'state': 'rejected'})
        else:
            raise UserError(_("You are not allowed to perform this action"))

    
    def action_approved(self):
        self.write({'previous_state': self.state})
        self.write({'state': 'approve'})

    
    def action_ceo_rejected(self):
        self.write({'previous_state': self.state})
        self.write({'state': 'rejected'})

    
    def action_reject(self):
        self.write({'previous_state': self.state})
        self.write({'state': 'rejected'})

    
    def action_cancel(self):
        self.write({'state': 'cancelled'})

    
    def action_send_back(self):
        self.write({'state': self.previous_state})

    def action_under_approve(self):
        self.write({'previous_state': self.state})
        self.write({'approve_user_id': self.env.user.id})
        if self.approval_type_id.ceo_review:
            self.write({'state': 'under_ceo_review','is_ceo_state': True})
        if not self.approval_type_id.ceo_review:
            self.write({'state': 'approve'})

    def action_ceo_approved(self):
        self.write({'previous_state': self.state})
        self.write({'approve_user_id': self.env.user.id})
        self.write({'state': 'approve'})


class ApprovalType(models.Model):
    _name = 'approval.type'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Approval Type', required=True, tracking=True)
    manager_ids = fields.Many2many('res.users','approval_user_manager_rel','approval_id','user_manager_id',
                                   string='Manager Review', tracking=True)
    accounts_approvers_ids = fields.Many2many('res.users','approval_user_accounts_rel','approval_id','user_accounts_id',
                                              string='Accounts Approvers', tracking=True)
    manager_review = fields.Boolean(string='Manager Review', tracking=True)
    accounts_review = fields.Boolean(string='Accounts Review', tracking=True)
    gm_review = fields.Boolean(string='GM Review', tracking=True)
    ceo_review = fields.Boolean(string='CEO Review', tracking=True)
    invoice_check = fields.Boolean(string="Invoice")

    # active = fields.Boolean(string='Active')

    # _defaults = {
    #     'active': True
    # }


class AccountMove(models.Model):
    _inherit = 'account.move'

    approval_id = fields.Many2one('approval.approval',string="Approval")
    approved_by = fields.Many2one('res.users',string="Approved By")

    @api.model
    def create(self, vals):
        approval = False
        if self.env.context.get('approval'):
            vals['approval_id'] = self.env.context.get('default_approval_id')
            approval = self.env['approval.approval'].search([('id', '=', self.env.context.get('default_approval_id'))])
        res = super(AccountMove, self).create(vals)
        if approval:
            approval.invoice_ids = [(4, res.id)]
        return res