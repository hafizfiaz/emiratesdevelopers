# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class ResPartner(models.Model):
    _inherit = "res.partner"

    nationality_id = fields.Many2one('res.country', 'Nationality')
    nationality = fields.Char('Nationality', tracking=True)
    active = fields.Boolean(default=True, tracking=True)
    lock = fields.Boolean('Lock')
    account_id_no = fields.Char(compute='compute_account_id_no', string='Account ID')
    internal_user = fields.Boolean(string='Internal User', default=False)
    is_agent = fields.Boolean(string='Is Agent', default=False)
    customer = fields.Boolean(string='Is Customer', default=False)
    supplier = fields.Boolean(string='Is Vendor', default=False)
    is_tenant = fields.Boolean(string='Tenant', default=False)
    represented_by = fields.Char("Represented by")
    designation = fields.Char("Designation")
    eid_no = fields.Char("EID No")
    passport_no = fields.Char("Passport No")
    visa_no = fields.Char("Visa No")
    passport_expiry_date = fields.Date("Passport Expiry Date")
    visa_expiry_date = fields.Date("Visa Expiry Date")
    email2 = fields.Char("Email 2")
    second_mobile_no = fields.Char("2nd Mobile No")
    home_address = fields.Char("Home Address")


    @api.model
    def cron_account_id_no(self):
        rp = self.env['rec.partner'].search([])
        for rec in rp:
            rec.account_id_no = str(rec.create_date.year)+str(rec.id)

    @api.depends('create_date')
    def compute_account_id_no(self):
        for rec in self:
            rec.account_id_no = str(rec.create_date.year)+str(rec.id)

    def profile_lock(self):
        for rec in self:
            rec.lock = not rec.lock


    @api.model
    def get_profile_lock(self):
        rp = self.env['res.partner'].search([])
        for rec in rp:
            current_date = fields.Date.today()
            delta = current_date - rec.create_date.date()
            if delta.days >= 2:
                rec.lock = True

    @api.model
    def get_profile_lock_all(self, ):
        rp = self.env['res.partner'].search([])
        for rec in rp:
            if not rec.lock:
                rec.lock = True

    def toggle_active(self):
        for partner in self:
            balance = partner.debit - partner.credit
            if partner.active and balance >= 1 or balance <= -1:
                raise ValidationError("Action not allowed!, Account Balance is not zero")
        super(ResPartner, self).toggle_active()

    @api.onchange('nationality_id')
    def _onchange_nationality_id(self):
        for rec in self:
            rec.nationality = rec.nationality_id.name

    @api.model
    def _compute_country(self):
        records = self.env['res.partner'].search([])
        for rec in records:
            country = self.env['res.country'].search([('name', '=ilike', rec.nationality)])
            if country:
                rec.nationality_id = country[0].id