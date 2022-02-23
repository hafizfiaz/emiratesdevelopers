from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class ConvertPdcsWizard(models.TransientModel):
    _name = "convert.pdcs.wizard"
    _description = 'Convert PDC Wiz'

    bank_deposit = fields.Many2one('res.partner.bank', 'Bank where the check is deposit/cashed',
                                   help='This bank indicate the name of the bank which the check is deposit and cashed')

    # @api.multi
    def action_convert_pdcs(self):
        payment_ids = self._context.get('active_ids', [])
        payment_obj = self.env['account.payment'].search([('id','in',payment_ids)])
        for line in payment_obj:
            if line.chk:
                line.write({'bank_deposit':self.bank_deposit.id})
                line.voucher_posted()
            else:
                line.post()
