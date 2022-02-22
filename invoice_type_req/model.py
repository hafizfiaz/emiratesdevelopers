from odoo import models, fields, api, _


class AccountMove(models.Model):
    _inherit = 'account.move'

    invoice_type = fields.Selection([('installment', 'Installment'),
                                     ('oqood', 'Oqood Fee'),
                                     ('admin', 'Admin Fee'),
                                     ('handover', 'Handover Fee'),
                                     ('service', 'Service Charges'),
                                     ('dewa', 'Dewa Charges'),
                                     ('deed', 'Title Deed'),
                                     ('termination', 'Termination Fee'),
                                     ('premium', 'Premium Finish'),
                                     ('rental', 'Rental Schedule'),
                                     ('commission', 'Commission')], tracking=True)

    @api.model
    def cron_comm_invoice_type(self):
        count = 0
        for rec in self.env['commission.invoice'].search([]):
            if rec.invc_id:
                rec.invc_id.invoice_type = 'commission'
            count += 1
            print(count)

    def invoice_type_cron(self):
        self.cron_comm_invoice_type()
        self.cron_installment_invoice_type()
        self.cron_other_invoice_type()
        self.cron_rental_invoice_type()
        self.cron_premium_invoice_type()
        self.cron_oqood_admin_invoice_type()


    @api.model
    def cron_installment_invoice_type(self):
        count = 0
        for rec in self.env['sale.rent.schedule'].search([('inv', '=', True)]):
            if rec.invoice_ids:
                for inv in rec.invoice_ids:
                    inv.invoice_type = 'installment'
            else:
                if rec.invc_id:
                    rec.invc_id.invoice_type = 'installment'
            count += 1
            print(count)

    @api.model
    def cron_rental_invoice_type(self):
        count = 0
        for rec in self.env['tenancy.rent.schedule'].search([]):
            if rec.invc_id:
                rec.invc_id.invoice_type = 'rental'
            count += 1
            print(count)
        count = 0
        for rec in self.env['account.move'].search([('move_type', '=', 'out_invoice'),('rental', '=', True)]):
            if rec.rental and not rec.invoice_type:
                rec.invoice_type = 'rental'
            count += 1
            print(count)

    @api.model
    def cron_premium_invoice_type(self):
        count = 0
        for rec in self.env['premium.finish.ps'].search([]):
            if rec.invc_id:
                rec.invc_id.invoice_type = 'premium'
            count += 1
            print(count)

    @api.model
    def cron_oqood_admin_invoice_type(self):
        count = 0
        for rec in self.env['account.move'].search([('move_type', '=', 'out_invoice')]):
            oqood = False
            admin = False
            for line in rec.invoice_line_ids:
                if 'oqood' in line.account_id.name.lower():
                    oqood = True
                if 'admin' in line.account_id.name.lower():
                    admin = True
            if oqood:
                rec.invoice_type = 'oqood'
            if admin:
                rec.invoice_type = 'admin'
            count += 1
            print(count)

    @api.model
    def cron_other_invoice_type(self):
        count = 0
        for rec in self.env['account.move'].search([('move_type', '=', 'out_invoice')]):
            service = False
            handover = False
            deed = False
            dewa = False
            termination = False
            for line in rec.invoice_line_ids:
                if 'service charges' in line.account_id.name.lower():
                    service = True
                if 'handover fee' in line.account_id.name.lower():
                    handover = True
                if 'title deed' in line.account_id.name.lower():
                    deed = True
                if 'dewa' in line.account_id.name.lower():
                    dewa = True
                if 'termination' in line.account_id.name.lower():
                    termination = True
            if service:
                rec.invoice_type = 'service'
            if handover:
                rec.invoice_type = 'handover'
            if deed:
                rec.invoice_type = 'deed'
            if dewa:
                rec.invoice_type = 'dewa'
            if termination:
                rec.invoice_type = 'termination'
            count += 1
            print(count)
