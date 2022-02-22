# See LICENSE file for full copyright and licensing details

import re

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class TenantPartner(models.Model):
    _name = "tenant.partner"
    _description = 'Tenanct Partner'
    _inherits = {'res.partner': 'parent_id'}

    doc_name = fields.Char(
        string='Filename')
    id_attachment = fields.Binary(
        string='Identity Proof')
    tenancy_ids = fields.One2many(
        comodel_name='account.analytic.account',
        inverse_name='tenant_id',
        string='Tenancy Details',
        help='Tenancy Details')
    parent_id = fields.Many2one(
        comodel_name='res.partner',
        string='Partner',
        required=True,
        index=True,
        ondelete='cascade')
    tenant_ids = fields.Many2many(
        comodel_name='tenant.partner',
        relation='agent_tenant_rel',
        column1='agent_id',
        column2='tenant_id',
        string='Tenant Details',
        domain=[('agent', '=', False)])
        # domain=[('customer', '=', True), ('agent', '=', False)])
    mobile = fields.Char(
        string='Mobile')
    # maintenance_ids = fields.One2many(
    #     comodel_name='property.maintenance',
    #     inverse_name='tenant_id',
    #     string='Maintenance Details')

    @api.constrains('email')
    def _check_values(self):
        """
        Check the email address in special formate if you enter wrong
        mobile formate then raise ValidationError
        """
        for val in self:
            if val.email:
                if re.match("^[a-zA-Z0-9._+-]+@[a-zA-Z0-9]+\.[a-zA-Z0-9.]*"
                            "\.*[a-zA-Z]{2,4}$", val.email) is not None:
                    pass
                else:
                    raise ValidationError(_('Please Enter Valid Email Id!'))

    @api.model
    def create(self, vals):
        """
        This Method is used to override orm create method.
        @param self: The object pointer
        @param vals: dictionary of fields value.
        """
        # property_user = False
        res = super(TenantPartner, self).create(vals)
        # password = self.env['res.company'].browse(
        #     vals.get('company_id', False)).default_password
        # if not password:
        #     password = ''
        # create_user = self.env['res.users'].create({
        #     'login': vals.get('email'),
        #     'name': vals.get('name'),
        #     'password': password,
        #     'tenant_id': res.id,
        #     'partner_id': res.parent_id.id,
        # })
        # if res.customer:
        #     property_user = \
        #         self.env.ref('property_management.group_property_user')
        # if res.agent:
        #     property_user = \
        #         self.env.ref('property_management.group_property_agent')
        # if property_user:
        #     property_user.write({'users': [(4, create_user.id)]})
        return res

    @api.model
    def default_get(self, fields):
        """
        This method is used to get default values for tenant.
        @param self: The object pointer
        @param fields: Names of fields.
        @return: Dictionary of values.
        """
        context = dict(self._context or {})
        res = super(TenantPartner, self).default_get(fields)
        if context.get('tenant', False):
            res.update({'tenant': context['tenant']})
        # res.update({'customer': True})
        return res

    
    def unlink(self):
        """
        Overrides orm unlink method.
        @param self: The object pointer
        @return: True/False.
        """
        # user_obj = self.env['res.users']
        # for tenant_rec in self:
        #     if tenant_rec.parent_id and tenant_rec.parent_id.id:
        #         releted_user = tenant_rec.parent_id.id
        #         new_user_rec = user_obj.search(
        #             [('partner_id', '=', releted_user)])
        #         if releted_user and new_user_rec and new_user_rec.ids:
        #             new_user_rec.unlink()
        return super(TenantPartner, self).unlink()

