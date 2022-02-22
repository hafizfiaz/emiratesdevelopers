from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class PropertyPriceWizard(models.TransientModel):
    _name = "property.price.wizard"
    _description = 'Property Price Wizard'

    asset_project_id = fields.Many2one('account.asset.asset', 'Project', domain="[('project', '=', True)]")
    property_id = fields.Many2one('account.asset.asset', string='Property', required=True)
    value = fields.Float('Price', related='property_id.value')
    new_value = fields.Float('New Price')


    @api.onchange('asset_project_id')
    def onchange_asset_project_id(self):
        property_ids = self.env['account.asset.asset'].search(
            [('state', '=', 'draft'),('parent_id', '=', self.asset_project_id.id)])
        return {'domain': {'property_id': [('id', 'in', property_ids.ids)]}}

    def action_apply(self):
        # prop_ids = self._context.get('active_ids', [])
        # properties = self.env['account.asset.asset'].search([('id','in',prop_ids)
        if self.new_value:
            if self.property_id.state != 'draft':
                raise ValidationError(_('You are just allowed to change price of available properties'))
            if self.new_value < self.property_id.min_value:
                raise ValidationError(_('You are not allowed to enter New Value less then Minimum Price (%s)') % (self.property_id.min_value,))
            self.property_id.value = self.new_value
        else:
            raise ValidationError("Please enter new value if you want to change")
