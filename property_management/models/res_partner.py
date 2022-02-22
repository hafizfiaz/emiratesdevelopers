# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details

import re

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class ResPartner(models.Model):
    _inherit = "res.partner"

    tenant = fields.Boolean(
        string='Tenant',
        help="Check this box if this contact is a tenant.")
    occupation = fields.Char(
        string='Occupation')
    agent = fields.Boolean(
        string='Agent',
        help="Check this box if this contact is a Agent.")
    mobile = fields.Char(
        string='Mobile')

    
    def write(self, vals):
        res = super(ResPartner, self).write(vals)
        # tenant_group = \
        #     self.env.ref('property_management.group_property_user')
        # agent_group = \
        #     self.env.ref('property_management.group_property_agent')
        # for partner in self:
        #     if 'tenant' in vals:
        #         if not partner.tenant:
        #             if partner.user_ids.has_group(
        #                     'property_management.group_property_user'):
        #                 partner.user_ids.write(
        #                     {'groups_id': [(3, tenant_group.id)]})
        #         else:
        #             partner.user_ids.write(
        #                 {'groups_id': [(4, tenant_group.id)]})
        #     if 'agent' in vals:
        #         if not partner.agent:
        #             if partner.user_ids.has_group(
        #                     'property_management.group_property_agent'):
        #                 partner.user_ids.write(
        #                     {'groups_id': [(3, agent_group.id)]})
        #         else:
        #             partner.user_ids.write(
        #                 {'groups_id': [(4, agent_group.id)]})
        return res

    # @api.constrains('mobile')
    # def _check_value(self):
    #     return True
        # """
        # Check the mobile number in special formate if you enter wrong
        # mobile formate then raise ValidationError
        # """
        # for val in self:
        #     if val.mobile:
        #         if re.match(
        #                 "^\+|[1-9]{1}[0-9]{3,14}$", val.mobile) is not None:
        #             pass
        #         else:
        #             raise ValidationError(
        #                 _('Please Enter Valid Mobile Number!'))

    # @api.constrains('email')
    # def _check_values(self):
    #     return True
        # """
        # Check the email address in special formate if you enter wrong
        # mobile formate then raise ValidationError
        # """
        # for val in self:
        #     if val.email:
        #         if re.match("^[a-zA-Z0-9._+-]+@[a-zA-Z0-9]+\.[a-zA-Z0-9.]*"
        #                     "\.*[a-zA-Z]{2,4}$", val.email) is not None:
        #             pass
        #         else:
        #             raise ValidationError(_('Please Enter Valid Email Id!'))


class ResUsers(models.Model):
    _inherit = "res.users"

    tenant_id = fields.Many2one(
        comodel_name='tenant.partner',
        string='Related Tenant')
    tenant_ids = fields.Many2many(
        comodel_name='tenant.partner',
        relation='rel_ten_user',
        column1='user_id',
        column2='tenant_id',
        string='All Tenants')


class ResCompany(models.Model):
    _inherit = 'res.company'

    default_password = fields.Char(
        string='Default Password')
