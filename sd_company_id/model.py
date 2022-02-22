from odoo import models, fields, api, _


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    company_id = fields.Many2one('res.company', string='Company', required=True,
                                 default=lambda self: self.env.company.id)


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    company_id = fields.Many2one('res.company', string='Company', required=True,
                                 default=lambda self: self.env.company.id)


class HandOverClearance(models.Model):
    _inherit = 'handover.clearance'

    company_id = fields.Many2one('res.company', string='Company', required=True,
                                 default=lambda self: self.env.company.id)


class TerminationProcess(models.Model):
    _inherit = 'termination.process'

    company_id = fields.Many2one('res.company', string='Company', required=True,
                                 default=lambda self: self.env.company.id)


class EarlySettlement(models.Model):
    _inherit = 'early.settlement'

    company_id = fields.Many2one('res.company', string='Company', required=True,
                                 default=lambda self: self.env.company.id)


class AccountClearance(models.Model):
    _inherit = 'account.clearance'

    company_id = fields.Many2one('res.company', string='Company', required=True,
                                 default=lambda self: self.env.company.id)


class OqoodReg(models.Model):
    _inherit = 'oqood.reg'

    company_id = fields.Many2one('res.company', string='Company', required=True,
                                 default=lambda self: self.env.company.id)


class RefundEoi(models.Model):
    _inherit = 'refund.eoi'

    company_id = fields.Many2one('res.company', string='Company', required=True,
                                 default=lambda self: self.env.company.id)


class AccountType(models.Model):
    _inherit = 'account.account.type'

    company_id = fields.Many2one('res.company', string='Company', required=True,
                                 default=lambda self: self.env.company.id)


class AccountPaymentTerm(models.Model):
    _inherit = 'account.payment.term'

    company_id = fields.Many2one('res.company', string='Company', required=True,
                                 default=lambda self: self.env.company.id)


class AccountPaymentLine(models.Model):
    _inherit = 'account.payment.term.line'

    company_id = fields.Many2one('res.company', string='Company', required=True,
                                 default=lambda self: self.env.company.id)


class AccountGroup(models.Model):
    _inherit = 'account.group.template'

    company_id = fields.Many2one('res.company', string='Company', required=True,
                                 default=lambda self: self.env.company.id)


class SaleReport(models.Model):
    _inherit = 'sale.report'

    company_id = fields.Many2one('res.company', string='Company', required=True,
                                 default=lambda self: self.env.company.id)


class StockInventory(models.Model):
    _inherit = 'stock.inventory'

    company_id = fields.Many2one('res.company', string='Company', required=True,
                                 default=lambda self: self.env.company.id)


class PartnerSms(models.Model):
    _inherit = 'partner.sms.send'

    company_id = fields.Many2one('res.company', string='Company', required=True,
                                 default=lambda self: self.env.company.id)


class AssetAssetReport(models.Model):
    _inherit = 'asset.asset.report'

    company_id = fields.Many2one('res.company', string='Company', required=True,
                                 default=lambda self: self.env.company.id)


class CommissionInvoiceLine(models.Model):
    _inherit = 'commission.invoice.line'

    company_id = fields.Many2one('res.company', string='Company', required=True,
                                 default=lambda self: self.env.company.id)


class PropertyType(models.Model):
    _inherit = 'property.type'

    company_id = fields.Many2one('res.company', string='Company', required=True,
                                 default=lambda self: self.env.company.id)


class RentType(models.Model):
    _inherit = 'rent.type'

    company_id = fields.Many2one('res.company', string='Company', required=True,
                                 default=lambda self: self.env.company.id)


class TenantPartner(models.Model):
    _inherit = 'tenant.partner'

    company_id = fields.Many2one('res.company', string='Company', required=True,
                                 default=lambda self: self.env.company.id)


class DfaAnalysis(models.Model):
    _inherit = 'gfa.analysis.report'

    company_id = fields.Many2one('res.company', string='Company', required=True,
                                 default=lambda self: self.env.company.id)


class InvestmentAnalysisReport(models.Model):
    _inherit = 'investment.analysis.report'

    company_id = fields.Many2one('res.company', string='Company', required=True,
                                 default=lambda self: self.env.company.id)


class OccupancyPerform(models.Model):
    _inherit = 'occupancy.performance.report'

    company_id = fields.Many2one('res.company', string='Company', required=True,
                                 default=lambda self: self.env.company.id)


class OperationalCost(models.Model):
    _inherit = 'operational.costs.report'

    company_id = fields.Many2one('res.company', string='Company', required=True,
                                 default=lambda self: self.env.company.id)


class SmsMail(models.Model):
    _inherit = 'sms.mail.server'

    company_id = fields.Many2one('res.company', string='Company', required=True,
                                 default=lambda self: self.env.company.id)


class SmsGroup(models.Model):
    _inherit = 'sms.group'

    company_id = fields.Many2one('res.company', string='Company', required=True,
                                 default=lambda self: self.env.company.id)


class SmsReport(models.Model):
    _inherit = 'sms.report'

    company_id = fields.Many2one('res.company', string='Company', required=True,
                                 default=lambda self: self.env.company.id)


class Sms(models.Model):
    _inherit = 'sms.sms'

    company_id = fields.Many2one('res.company', string='Company', required=True,
                                 default=lambda self: self.env.company.id)


class CommType(models.Model):
    _inherit = 'commission.type'

    company_id = fields.Many2one('res.company', string='Company', required=True,
                                 default=lambda self: self.env.company.id)


class BookingDiscount(models.Model):
    _inherit = 'booking.discount'

    company_id = fields.Many2one('res.company', string='Company', required=True,
                                 default=lambda self: self.env.company.id)


class DldPayment(models.Model):
    _inherit = 'dld.payment.plan'

    company_id = fields.Many2one('res.company', string='Company', required=True,
                                 default=lambda self: self.env.company.id)


class PremiumFinish(models.Model):
    _inherit = 'premium.finish.ps'

    company_id = fields.Many2one('res.company', string='Company', required=True,
                                 default=lambda self: self.env.company.id)


class ProjectCosting(models.Model):
    _inherit = 'project.costing'

    company_id = fields.Many2one('res.company', string='Company', required=True,
                                 default=lambda self: self.env.company.id)


class PaymentCertificate(models.Model):
    _inherit = 'payment.certificate'

    company_id = fields.Many2one('res.company', string='Company', required=True,
                                 default=lambda self: self.env.company.id)


class ConsumedBOQ(models.Model):
    _inherit = 'consume.material.line'

    company_id = fields.Many2one('res.company', string='Company', required=True,
                                 default=lambda self: self.env.company.id)


class PlannedBoq(models.Model):
    _inherit = 'planned.boq'

    company_id = fields.Many2one('res.company', string='Company', required=True,
                                 default=lambda self: self.env.company.id)


class HrAppraisal(models.Model):
    _inherit = 'hr.appraisal.goal'

    company_id = fields.Many2one('res.company', string='Company', required=True,
                                 default=lambda self: self.env.company.id)


class ApprovalApproval(models.Model):
    _inherit = 'approval.approval'

    company_id = fields.Many2one('res.company', string='Company', required=True,
                                 default=lambda self: self.env.company.id)


class ApprovalType(models.Model):
    _inherit = 'approval.type'

    company_id = fields.Many2one('res.company', string='Company', required=True,
                                 default=lambda self: self.env.company.id)


class SaleAmendment(models.Model):
    _inherit = 'sale.amendment'

    company_id = fields.Many2one('res.company', string='Company', required=True,
                                 default=lambda self: self.env.company.id)


class CourierCourier(models.Model):
    _inherit = 'courier.courier'

    company_id = fields.Many2one('res.company', string='Company', required=True,
                                 default=lambda self: self.env.company.id)


class CalendarEvent(models.Model):
    _inherit = 'calendar.event'

    company_id = fields.Many2one('res.company', string='Company', required=True,
                                 default=lambda self: self.env.company.id)

