# See LICENSE file for full copyright and licensing details

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class ContractExpiryReport(models.TransientModel):
    _name = 'contract.expiry.report'
    _description = 'Contract Expiary Report'

    start_date = fields.Date(
        string='Start date',
        required=True)
    end_date = fields.Date(
        string='End date',
        required=True)

    @api.constrains('start_date', 'end_date')
    def check_date_overlap(self):
        """
        This is a constraint method used to check the from date smaller than
        the Exiration date.
        @param self : object pointer
        """
        for ver in self:
            if ver.start_date and ver.end_date and \
                    ver.end_date < ver.start_date:
                raise ValidationError(_(
                    'End date should be greater than Start Date!'))

    
    def open_contract_expiry_tree(self):
        """
        This method is used to open record in tree view between selected dates
        @param self : object pointer
        """
        analytic_obj = self.env["account.analytic.account"]
        wiz_form_id = self.env.ref(
            'property_management.property_analytic_view_tree').id
        for data1 in self:
            data = data1.read([])[0]
            start_date = data['start_date']
            end_date = data['end_date']
            tenancy_ids = analytic_obj.search(
                [('date', '>=', start_date), ('date', '<=', end_date)])
        return {'name': _('Tenancy Contract Expiary'),
                'view_mode': 'tree',
                'view_id': wiz_form_id,
                # 'view_type': 'form',
                'res_model': 'account.analytic.account',
                'type': 'ir.actions.act_window',
                'target': 'current',
                'domain': [('id', 'in', tenancy_ids.ids)],
                }

    
    def print_report(self):
        """
        This method is used to printng a report
        @param self : object pointer
        """
        data = {
            'ids': self.ids,
            'model': 'account.asset.asset',
            'form': self.read(['start_date', 'end_date'])[0]
        }
        return self.env.ref(
            'property_management.action_report_contract_expiry').report_action(
            [], data=data)
