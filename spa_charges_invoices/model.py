# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.tools import safe_eval
from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from odoo.exceptions import UserError, ValidationError


class SPACharges(models.TransientModel):
    _name = "spa.charges.wiz"

    spa_id = fields.Many2one('sale.order','spa')

    handover_chk = fields.Boolean("Handover")
    dewa_fee_chk = fields.Boolean("Dewa Fee")
    title_deed_chk = fields.Boolean("Title Deed")
    service_charges_chk = fields.Boolean("Service Charges")

    handover_vat = fields.Boolean("Include VAT")
    dewa_fee_vat = fields.Boolean("Include VAT")
    title_deed_vat = fields.Boolean("Include VAT")
    service_charges_vat = fields.Boolean("Include VAT")

    handover_amount = fields.Float("Amount")
    dewa_fee_amount = fields.Float("Amount")
    title_deed_amount = fields.Float("Amount")
    service_charges_amount = fields.Float("Amount")

    handover_vat_amount = fields.Float("VAT Amount")
    dewa_fee_vat_amount = fields.Float("VAT Amount")
    title_deed_vat_amount = fields.Float("VAT Amount")
    service_charges_vat_amount = fields.Float("VAT Amount")

    spa_handover_chk = fields.Boolean("SPA Handover")
    spa_dewa_fee_chk = fields.Boolean("SPA Dewa Fee")
    spa_title_deed_chk = fields.Boolean("SPA Title Deed")
    spa_service_charges_chk = fields.Boolean("SPA Service Charges")

    @api.onchange('spa_handover_chk','spa_dewa_fee_chk','spa_title_deed_chk','spa_service_charges_chk')
    def onchange_spa_chk(self):
        if self.spa_id.handover_chk:
            self.spa_handover_chk = True
            self.handover_chk = True
            if self.spa_id.handover_vat:
                self.handover_vat = True
            else:
                self.handover_vat = False
            self.handover_amount = self.spa_id.handover_amount
            self.handover_vat_amount = self.spa_id.handover_vat
        if self.spa_id.dewa_fee_chk:
            self.dewa_fee_chk = True
            self.spa_dewa_fee_chk = True
            if self.spa_id.dewa_fee_vat:
                self.dewa_fee_vat = True
            else:
                self.dewa_fee_vat = False
            self.dewa_fee_amount = self.spa_id.dewa_fee_amount
            self.dewa_fee_vat_amount = self.spa_id.dewa_fee_vat
        if self.spa_id.title_deed_chk:
            self.spa_title_deed_chk = True
            self.title_deed_chk = True
            if self.spa_id.title_deed_vat:
                self.title_deed_vat = True
            else:
                self.title_deed_vat = False
            self.title_deed_amount = self.spa_id.title_deed_amount
            self.title_deed_vat_amount = self.spa_id.title_deed_vat
        if self.spa_id.service_charges_chk:
            self.service_charges_chk = True
            self.spa_service_charges_chk = True
            if self.spa_id.service_charges_vat:
                self.service_charges_vat = True
            else:
                self.service_charges_vat = False
            self.service_charges_amount = self.spa_id.service_charges_amount
            self.service_charges_vat_amount = self.spa_id.service_charges_vat

    @api.onchange('handover_chk','handover_vat')
    def onchange_for_charges1(self):
        if self.handover_chk:
            self.handover_amount = self.spa_id.asset_project_id.handover_fee_amount
        if self.handover_vat:
            self.handover_vat_amount = self.spa_id.asset_project_id.handover_fee_amount * (self.spa_id.asset_project_id.handover_fee_vat_id.amount / 100)

    @api.onchange('dewa_fee_chk','dewa_fee_vat')
    def onchange_for_charges2(self):
        if self.dewa_fee_chk:
            self.dewa_fee_amount = self.spa_id.asset_project_id.dewa_fee_amount
        if self.dewa_fee_vat:
            self.dewa_fee_vat_amount = self.spa_id.asset_project_id.dewa_fee_amount * (self.spa_id.asset_project_id.dewa_fee_vat_id.amount / 100)

    @api.onchange('title_deed_chk','title_deed_vat')
    def onchange_for_charges3(self):
        if self.title_deed_chk:
            self.title_deed_amount = self.spa_id.asset_project_id.title_deed_amount
        if self.title_deed_vat:
            self.title_deed_vat_amount = self.spa_id.asset_project_id.title_deed_amount * (self.spa_id.asset_project_id.title_deed_vat_id.amount / 100)

    @api.onchange('service_charges_chk','service_charges_vat')
    def onchange_for_charges4(self):
        if self.service_charges_chk:
            self.service_charges_amount = (self.spa_id.asset_project_id.service_charges_amount * self.spa_id.property_id.gfa_feet)
        if self.service_charges_vat:
            self.service_charges_vat_amount = (self.spa_id.asset_project_id.service_charges_amount * self.spa_id.property_id.gfa_feet) * (self.spa_id.asset_project_id.service_charges_vat_id.amount / 100)

    def action_apply(self):
        for data in self.spa_id:
            handover_fee_rec = False
            if self.handover_chk and not self.spa_handover_chk:
                if not data.asset_project_id.handover_fee_ledger_id:
                    raise UserError(_("Please select Handover Fee Ledger in selected Project."))
                if self.handover_vat and not data.asset_project_id.handover_fee_vat_id:
                    raise UserError(_("Please select Handover Fee VAT on selected project in selected Project."))

                handover_invoice_line = []
                handover_invoice_line.append((0, 0, {'name': "Handover fee of" + str(data.name),
                                                  'asset_project_id': data.asset_project_id.id,
                                                  'property_id': data.property_id.id,
                                                  'account_id': data.asset_project_id.handover_fee_ledger_id.id,
                                                  'quantity': 1,
                                                   'tax_ids': [(6, 0, data.asset_project_id.handover_fee_vat_id.ids)] if self.handover_vat else [],
                                                  # 'product_uom': 1,
                                                  'price_unit': data.asset_project_id.handover_fee_amount}))
                handover_fee_rec = self.env['account.move'].create({
                    'partner_id': data.partner_id.id,
                    'asset_project_id': data.asset_project_id.id,
                    'property_id': data.property_id.id,
                    'invoice_user_id': data.user_id.id,
                    'team_id': data.team_id.id,
                    'company_id': self.env.user.company_id.id,
                    'move_type': 'out_invoice',
                    'invoice_type': 'handover',
                    # 'account_id': data.partner_id.property_account_receivable_id.id,
                    'invoice_date': datetime.now().strftime('%Y-%m-%d'),
                    'state': 'draft',
                    # 'invoice_line_ids': admin_fee_lines
                    'invoice_line_ids': handover_invoice_line
                })

            dewa_fee_rec = False
            if self.dewa_fee_chk and not self.spa_dewa_fee_chk:
                if not data.asset_project_id.dewa_fee_ledger_id:
                    raise UserError(_("Please select DEWA Fee Ledger in selected Project."))
                if self.dewa_fee_vat and not data.asset_project_id.dewa_fee_vat_id:
                    raise UserError(_("Please select DEWA Fee VAT on selected project in selected Project."))

                dewa_invoice_line = []
                dewa_invoice_line.append((0, 0, {'name': "DEWA Fee of" + str(data.name),
                                                  'asset_project_id': data.asset_project_id.id,
                                                  'property_id': data.property_id.id,
                                                  'account_id': data.asset_project_id.dewa_fee_ledger_id.id,
                                                  'quantity': 1,
                                                  'tax_ids': [(6, 0, data.asset_project_id.dewa_fee_vat_id.ids)] if self.dewa_fee_vat else [],
                                                  # 'product_uom': 1,
                                                  'price_unit': data.asset_project_id.dewa_fee_amount}))
                dewa_fee_rec = self.env['account.move'].create({
                    'partner_id': data.partner_id.id,
                    'asset_project_id': data.asset_project_id.id,
                    'property_id': data.property_id.id,
                    'invoice_user_id': data.user_id.id,
                    'team_id': data.team_id.id,
                    'company_id': self.env.user.company_id.id,
                    'move_type': 'out_invoice',
                    'invoice_type': 'dewa',
                    # 'account_id': data.partner_id.property_account_receivable_id.id,
                    'invoice_date': datetime.now().strftime('%Y-%m-%d'),
                    'state': 'draft',
                    # 'invoice_line_ids': admin_fee_lines
                    'invoice_line_ids': dewa_invoice_line
                })

            title_deed_fee_rec = False
            if self.title_deed_chk and not self.spa_title_deed_chk:
                if not data.asset_project_id.title_deed_ledger_id:
                    raise UserError(_("Please select Title Deed Fee Ledger in selected Project."))
                if self.title_deed_vat and not data.asset_project_id.title_deed_vat_id:
                    raise UserError(_("Please select Title Deed Fee VAT on selected project in selected Project."))

                title_deed_invoice_line = []
                title_deed_invoice_line.append((0, 0, {'name': "Title Deed Fee of" + str(data.name),
                                                  'asset_project_id': data.asset_project_id.id,
                                                  'property_id': data.property_id.id,
                                                  'account_id': data.asset_project_id.title_deed_ledger_id.id,
                                                  'quantity': 1,
                                                  'tax_ids': [(6, 0, data.asset_project_id.title_deed_vat_id.ids)] if self.title_deed_vat else [],
                                                  # 'product_uom': 1,
                                                  'price_unit': data.asset_project_id.title_deed_amount}))
                title_deed_fee_rec = self.env['account.move'].create({
                    'partner_id': data.partner_id.id,
                    'asset_project_id': data.asset_project_id.id,
                    'property_id': data.property_id.id,
                    'invoice_user_id': data.user_id.id,
                    'team_id': data.team_id.id,
                    'company_id': self.env.user.company_id.id,
                    'move_type': 'out_invoice',
                    'invoice_type': 'deed',
                    # 'account_id': data.partner_id.property_account_receivable_id.id,
                    'invoice_date': datetime.now().strftime('%Y-%m-%d'),
                    'state': 'draft',
                    # 'invoice_line_ids': admin_fee_lines
                    'invoice_line_ids': title_deed_invoice_line
                })

            service_charges_fee_rec = False
            if self.service_charges_chk and not self.spa_service_charges_chk:
                if not data.asset_project_id.service_charges_ledger_id:
                    raise UserError(_("Please select Service Charges Ledger in selected Project."))
                if self.service_charges_vat and not data.asset_project_id.service_charges_vat_id:
                    raise UserError(_("Please select Service Charges VAT on selected project in selected Project."))

                sc_invoice_line = []
                sc_invoice_line.append((0, 0, {'name': "Service Charges of" + str(data.name),
                                                  'asset_project_id': data.asset_project_id.id,
                                                  'property_id': data.property_id.id,
                                                  'account_id': data.asset_project_id.service_charges_ledger_id.id,
                                                  'quantity': 1,
                                                  'tax_ids': [(6, 0, data.asset_project_id.service_charges_vat_id.ids)]  if self.service_charges_vat else [],
                                                  # 'product_uom': 1,
                                                  'price_unit': data.asset_project_id.service_charges_amount * data.property_id.gfa_feet}))
                service_charges_fee_rec = self.env['account.move'].create({
                    'partner_id': data.partner_id.id,
                    'asset_project_id': data.asset_project_id.id,
                    'property_id': data.property_id.id,
                    'invoice_user_id': data.user_id.id,
                    'team_id': data.team_id.id,
                    'company_id': self.env.user.company_id.id,
                    'move_type': 'out_invoice',
                    'invoice_type': 'service',
                    # 'account_id': data.partner_id.property_account_receivable_id.id,
                    'invoice_date': datetime.now().strftime('%Y-%m-%d'),
                    'state': 'draft',
                    # 'invoice_line_ids': admin_fee_lines
                    'invoice_line_ids': sc_invoice_line
                })

            inv_ids = []
            if handover_fee_rec:
                data.handover_chk = self.handover_chk
                data.handover_amount = data.asset_project_id.handover_fee_amount
                if self.handover_vat:
                    data.handover_vat = data.asset_project_id.handover_fee_amount * (data.asset_project_id.handover_fee_vat_id.amount / 100)
                handover_fee_rec.action_post()
                inv_ids.append(handover_fee_rec.id)
            if dewa_fee_rec:
                data.dewa_fee_chk = self.dewa_fee_chk
                data.dewa_fee_amount = data.asset_project_id.dewa_fee_amount
                if self.dewa_fee_vat:
                    data.dewa_fee_vat = data.asset_project_id.dewa_fee_amount * (data.asset_project_id.dewa_fee_vat_id.amount / 100)
                dewa_fee_rec.action_post()
                inv_ids.append(dewa_fee_rec.id)
            if title_deed_fee_rec:
                data.title_deed_chk = self.title_deed_chk
                data.title_deed_amount = data.asset_project_id.title_deed_amount
                if self.title_deed_vat:
                    data.title_deed_vat = data.asset_project_id.title_deed_amount * (data.asset_project_id.title_deed_vat_id.amount / 100)
                title_deed_fee_rec.action_post()
                inv_ids.append(title_deed_fee_rec.id)
            if service_charges_fee_rec:
                data.service_charges_chk = self.service_charges_chk
                data.service_charges_amount = data.asset_project_id.service_charges_amount * data.property_id.gfa_feet
                if self.service_charges_vat:
                    data.service_charges_vat = (data.asset_project_id.service_charges_amount * data.property_id.gfa_feet) * (data.asset_project_id.service_charges_vat_id.amount / 100)
                service_charges_fee_rec.action_post()
                inv_ids.append(service_charges_fee_rec.id)
            if data.other_charges_inv_ids:
                for l in data.other_charges_inv_ids:
                    inv_ids.append(l.id)
            if inv_ids:
                data.write({'other_charges_inv_ids': [(6, 0, inv_ids)]})


class AccountAssetAsset(models.Model):
    _inherit = 'account.asset.asset'

    dewa_fee_ledger_id = fields.Many2one('account.account','Dewa Fee Ledger', tracking=True)
    title_deed_ledger_id = fields.Many2one('account.account','Title Deed Ledger', tracking=True)
    service_charges_ledger_id = fields.Many2one('account.account','Service Charges Ledger', tracking=True)
    handover_fee_ledger_id = fields.Many2one('account.account','Handover Fee Ledger', tracking=True)

    dewa_fee_amount = fields.Float('Dewa Fee Amount', tracking=True)
    title_deed_amount = fields.Float('Title Deed Amount', tracking=True)
    service_charges_amount = fields.Float('Service Charges Amount', tracking=True)
    handover_fee_amount = fields.Float('Handover Fee Amount', tracking=True)

    dewa_fee_vat_id = fields.Many2one('account.tax','Dewa Fee VAT(%)', tracking=True)
    title_deed_vat_id = fields.Many2one('account.tax','Title Deed VAT(%)', tracking=True)
    service_charges_vat_id = fields.Many2one('account.tax','Service Charges VAT(%)', tracking=True)
    handover_fee_vat_id = fields.Many2one('account.tax','Handover Fee VAT(%)', tracking=True)


class SaleOrder(models.Model):
    _inherit = "sale.order"

    handover_chk = fields.Boolean("Handover")
    dewa_fee_chk = fields.Boolean("Dewa Fee")
    title_deed_chk = fields.Boolean("Title Deed")
    service_charges_chk = fields.Boolean("Service Charges")

    handover_vat = fields.Float("Handover VAT")
    dewa_fee_vat = fields.Float("Dewa Fee VAT")
    title_deed_vat = fields.Float("Title Deed VAT")
    service_charges_vat = fields.Float("Service Charges VAT")

    handover_amount = fields.Float("Handover Amount")
    dewa_fee_amount = fields.Float("Dewa Fee Amount")
    title_deed_amount = fields.Float("Title Deed Amount")
    service_charges_amount = fields.Float("Service Charges Amount")

    # @api.onchange('asset_project_id','property_id','handover_chk')
    # def onchange_for_charges(self):
    #     self.handover_chk = self.asset_project_id.

    def open_charges_wiz(self):
        ctx = dict(
            default_spa_id=self.id,
        )
        return {
            'name': _('SPA Other Charges'),
            'view_mode': 'form',
            'res_model': 'spa.charges.wiz',
            'view_id': self.env.ref('spa_charges_invoices.spa_charges_wizard_view').id,
            'type': 'ir.actions.act_window',
            'context': ctx,
            'target': 'new'
        }