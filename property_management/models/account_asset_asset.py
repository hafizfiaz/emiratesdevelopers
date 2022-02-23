# See LICENSE file for full copyright and licensing details

from datetime import datetime
from dateutil.relativedelta import relativedelta
import re
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
# from odoo.tools import DEFAULT_SERVER_DATE_FORMAT,image_resize_images,image_resize_image_big,image_resize_image_medium

class UnitType(models.Model):
    _name = 'unit.type'
    _description = 'Unit Type'

    name = fields.Char('Name', required=True)

class PropertyFacing(models.Model):
    _name = 'property.facing'
    _description = 'Facing'

    name = fields.Char('Name')

class PermittedUse(models.Model):
    _name = 'permitted.use'
    _description = 'Permitted Use'

    name = fields.Char('Name', required=True)


class BuildingType(models.Model):
    _name = 'building.type'
    _description = 'Building Type'

    name = fields.Char('Name', required=True)


class SaleTermsConditions(models.Model):
    _name = 'sale.payment.term'
    _description = 'Sale Terms & Condition'

    name = fields.Char('Name')
    asset_project_id = fields.Many2one('account.asset.asset', 'Project', domain="[('project', '=', True)]")
    property_id = fields.Many2one('account.asset.asset',string='Property')
    text = fields.Text('Rich Text')
    english_version_text = fields.Html('English Version Text')
    booking_terms_copy = fields.Html('Terms & Condition')
    active = fields.Boolean('Active', default=True)

    @api.onchange('asset_project_id')
    def onchange_asset_project_id(self):
        property_ids = self.env['account.asset.asset'].search(
            [('state', '=', 'draft'), ('parent_id', '=', self.asset_project_id.id)])
        return {'domain': {'property_id': [('id', 'in', property_ids.ids)]}}


class AccountAssetAsset(models.Model):
    _inherit = 'account.asset.asset'
    _description = 'Account Asset'

    
    @api.depends('property_phase_ids', 'property_phase_ids.lease_price')
    def _compute_sales_rates(self):
        """
        This Method is used to calculate total sales rates.
        @param self: The object pointer
        @return: Calculated Sales Rate.
        """
        for prop_rec in self:
            counter = 0
            les_price = 0
            sal_rate = 0
            for phase in prop_rec.property_phase_ids:
                counter += 1
                les_price += phase.lease_price
            if counter != 0 and les_price != 0:
                sal_rate = les_price / counter
            prop_rec.sales_rates = sal_rate

    
    @api.depends('roi')
    def _compute_ten_year_roi(self):
        """
        This Method is used to Calculate ten years ROI(Return On Investment).
        @param self: The object pointer
        @return: Calculated Return On Investment.
        """
        for rec in self:
            rec.ten_year_roi = 10 * rec.roi

    
    @api.depends('tenancy_property_ids', 'tenancy_property_ids.rent')
    def _compute_roi(self):
        """
        This Method is used to Calculate ROI(Return On Investment).
        @param self: The object pointer
        @return: Calculated Return On Investment.
        """
        for prop_rec in self:
            prop_rec.roi = \
                sum(gain.rent for gain in prop_rec.tenancy_property_ids)

    
    @api.depends('tenancy_property_ids', 'tenancy_property_ids.rent',
                 'property_phase_ids')
    def _compute_operational_costs(self):
        """
        This Method is used to Calculate Operation Cost.
        @param self: The object pointer
        @return: Calculated Operational Cost.
        """
        for prop_rec in self:
            operational_cost = 0
            opr_cst = 0
            gain_from_investment = sum(gain.rent for gain in
                                       prop_rec.tenancy_property_ids)
            for phase in prop_rec.property_phase_ids:
                operational_cost += (phase.lease_price / 100)
            if gain_from_investment != 0 and operational_cost != 0:
                opr_cst = operational_cost / gain_from_investment
            prop_rec.operational_costs = opr_cst

    
    @api.depends('date', 'tenancy_property_ids',
                 'tenancy_property_ids.date',
                 'tenancy_property_ids.date_start')
    def _compute_occupancy_rates(self):
        """
        This Method is used to calculate occupancy rate.
        @param self: The object pointer
        @return: Calculated Occupancy Rate.
        """
        for prop_rec in self:
            diffrnc = 0
            occ_rate = 0
            if prop_rec.date:
                pur_diff = datetime.now().date() - prop_rec.date
                purchase_diff = pur_diff.days
                for tency_rec in prop_rec.tenancy_property_ids:
                    if tency_rec.date and tency_rec.date_start:
                        date_diff = \
                            tency_rec.date - tency_rec.date_start
                        diffrnc += date_diff.days
                if purchase_diff != 0 and diffrnc != 0:
                    occ_rate = (purchase_diff * 100) / diffrnc
                prop_rec.occupancy_rates = occ_rate

    
    @api.depends('value', 'salvage_value', 'depreciation_line_ids')
    def _compute_value_residual(self):
        """
        @param self: The object pointer
        @return: Calculated Residual Amount.
        """
        for rec in self:
            total_residual = 0.0
            if rec.value > 0:
                total_amount = sum(
                    line.amount for line in rec.depreciation_line_ids
                    if line.move_check)
                total_residual = \
                    rec.value - total_amount - rec.salvage_value
            rec.value_residual = total_residual

    
    @api.depends('tenancy_property_ids',
                 'tenancy_property_ids.rent_schedule_ids')
    def _compute_simulation(self):
        """
        This Method is used to calculate simulation
        which is used in Financial Performance Report.
        @param self: The object pointer
        @return: Calculated Simulation Amount.
        """
        for property_data in self:
            property_data.simulation = sum(
                rent_schedule.amount for tenancy_property in
                property_data.tenancy_property_ids for rent_schedule in
                tenancy_property.rent_schedule_ids)

    
    @api.depends('tenancy_property_ids',
                 'tenancy_property_ids.rent_schedule_ids',
                 'tenancy_property_ids.rent_schedule_ids.move_check')
    def _compute_revenue(self):
        """
        This Method is used to calculate revenue
        which is used in Financial Performance Report.
        @param self: The object pointer
        @return: Calculated Revenue Amount.
        """
        for property_data in self:
            property_data.revenue = sum(
                rent_schedule.amount for tenancy_property in
                property_data.tenancy_property_ids for rent_schedule in
                tenancy_property.rent_schedule_ids if
                rent_schedule.move_check)

    
    @api.depends('gfa_feet', 'unit_price')
    def _compute_total_price(self):
        """
        This Method is used to Calculate Total Price.
        @param self: The object pointer
        @return: Calculated Total Price.
        """
        for rec in self:
            rec.total_price = rec.gfa_feet * rec.unit_price

    # image = fields.Binary(
    #     string='Image')
    image = fields.Binary("Logo", attachment=True,
        help="This field holds the image used as logo for the brand, limited to 1024x1024px.")
    image_medium = fields.Binary("Medium-sized image", attachment=True,
        help="Medium-sized logo of the brand. It is automatically "
             "resized as a 128x128px image, with aspect ratio preserved. "
             "Use this field in form views or some kanban views.")
    image_small = fields.Binary("Small-sized image", attachment=True,
        help="Small-sized logo of the brand. It is automatically "
             "resized as a 64x64px image, with aspect ratio preserved. "
             "Use this field anywhere a small image is required.")
    simulation_date = fields.Date(
        string='Simulation Date',
        help='Simulation Date.', tracking=True)
    city = fields.Char(
        string='City', tracking=True)
    street = fields.Char(
        string='Street', tracking=True)
    street2 = fields.Char(
        string='Street2', tracking=True)
    township = fields.Char(
        string='Township', tracking=True)
    simulation_name = fields.Char(
        string='Simulation Name', tracking=True)
    construction_cost = fields.Float(
        string='Construction Cost', tracking=True)
    zip = fields.Char(
        string='Zip',
        change_default=True, tracking=True)
    video_url = fields.Char(
        string='Video URL',
        help="//www.youtube.com/embed/mwuPTI8AT7M?rel=0")
    unit_price = fields.Float(
        string='Unit Price',
        help='Unit Price Per Sqft.', tracking=True)
    ground_rent = fields.Float(
        string='Ground Rent',
        help='Ground rent of Property.', tracking=True)
    gfa_meter = fields.Float(
        string='GFA(m)',
        help='Gross floor area in Meter.', tracking=True)
    sale_price = fields.Float(
        string='Sale Price',
        help='Sale price of the Property.', tracking=True)
    gfa_feet = fields.Float(
        string='GFA(Sqft)',
        help='Gross floor area in Square feet.', tracking=True)
    sales_rates = fields.Float(
        string="Sales Rate",
        compute='_compute_sales_rates',
        help='Average Sale/Lease price from property phase per Month.', tracking=True)
    ten_year_roi = fields.Float(
        string="10 year ROI",
        compute='_compute_ten_year_roi',
        help="10 year Return of Investment.", tracking=True)
    roi = fields.Float(
        string="ROI",
        compute='_compute_roi',
        store=True,
        help='ROI ( Return On Investment ) = ( Total Tenancy rent - Total \
        maintenance cost ) / Total maintenance cost.', tracking=True)
    operational_costs = fields.Float(
        string="Operational Costs(%)",
        store=True,
        compute='_compute_operational_costs',
        help='Average of total operational budget and total rent.', tracking=True)
    occupancy_rates = fields.Float(
        string="Occupancy Rate",
        store=True,
        compute='_compute_occupancy_rates',
        help='Total Occupancy rate of Property.', tracking=True)
    parent_path = fields.Char(index=True, tracking=True)
    value_residual = fields.Float(
        string='Residual Value',
        compute='_compute_value_residual', tracking=True)
    simulation = fields.Float(
        string='Total Amount',
        compute='_compute_simulation',
        store=True, tracking=True)
    revenue = fields.Float(
        string='Revenue',
        compute='_compute_revenue',
        store=True, tracking=True)
    total_price = fields.Float(
        string='Total Price',
        compute='_compute_total_price',
        help='Total Price of Property, \nTotal Price = Unit Price * \
        GFA (Sqft).', tracking=True)
    pur_instl_chck = fields.Boolean(
        string='Purchase Installment Check',
        default=False, tracking=True)
    sale_instl_chck = fields.Boolean(
        string='Sale Installment Check',
        default=False, tracking=True)
    color = fields.Integer(
        string='Color',
        default=4, tracking=True)
    floor = fields.Integer(
        string='Floor',
        help='Number of Floors.', tracking=True)
    no_of_towers = fields.Integer(
        string='No of Towers',
        help='Number of Towers.', tracking=True)
    no_of_property = fields.Integer(
        string='Property Per Floors.',
        help='Number of Properties Per Floor.', tracking=True)
    income_acc_id = fields.Many2one(
        comodel_name='account.account',
        string='Income Account',
        help='Income Account of Property.', tracking=True)
    expense_account_id = fields.Many2one(
        comodel_name='account.account',
        string='Expense Account',
        help='Expense Account of Property.', tracking=True)
    parent_id = fields.Many2one(
        comodel_name='account.asset.asset',
        domain=[('project','=',True)],
        string='Parent Property', tracking=True)
    current_tenant_id = fields.Many2one(
        comodel_name='tenant.partner',
        string='Current Tenant', tracking=True)
    country_id = fields.Many2one(
        comodel_name='res.country',
        string='Country',
        ondelete='restrict', tracking=True)
    state_id = fields.Many2one(
        comodel_name='res.country.state',
        string='Property State',
        ondelete='restrict', tracking=True)
    type_id = fields.Many2one(
        comodel_name='property.type',
        string='Property Type',
        help='Types of property.',
        index=True, tracking=True)
    rent_type_id = fields.Many2one(
        comodel_name='rent.type',
        string='Rent Type',
        help='Type of Rent.', tracking=True)
    contact_id = fields.Many2one(
        comodel_name='tenant.partner',
        string='Contact Name',
        domain="[('tenant', '=', True)]", tracking=True)
    property_manager = fields.Many2one(
        comodel_name='res.partner',
        string='Property Manager', tracking=True)
    room_ids = fields.One2many(
        comodel_name='property.room',
        inverse_name='property_id',
        string='Rooms', tracking=True)
    property_phase_ids = fields.One2many(
        comodel_name='property.phase',
        inverse_name='property_id',
        string='Phase', tracking=True)
    property_photo_ids = fields.One2many(
        comodel_name='property.photo',
        inverse_name='property_id',
        string='Photos', tracking=True)
        
    floor_plans_ids = fields.One2many(
        comodel_name='property.floor.plans',
        inverse_name='property_id',
        string='Floor Plans ', tracking=True)
    utility_ids = fields.One2many(
        comodel_name='property.utility',
        inverse_name='property_id',
        string='Utilities', tracking=True)
    nearby_ids = fields.One2many(
        comodel_name='nearby.property',
        inverse_name='property_id',
        string='Nearest Property', tracking=True)
    # maintenance_ids = fields.One2many(
    #     comodel_name='property.maintenance',
    #     inverse_name='property_id',
    #     string='Maintenance', tracking=True)
    contract_attachment_ids = fields.One2many(
        comodel_name='property.attachment',
        inverse_name='property_id',
        string='Document', tracking=True)
    child_ids = fields.One2many(
        comodel_name='account.asset.asset',
        inverse_name='parent_id',
        string='Children Assets', tracking=True)
    property_insurance_ids = fields.One2many(
        comodel_name='property.insurance',
        inverse_name='property_id',
        string='Insurance', tracking=True)
    tenancy_property_ids = fields.One2many(
        comodel_name='account.analytic.account',
        inverse_name='property_id',
        string='Tenancy Property', tracking=True)
    # crossovered_budget_line_property_ids = fields.One2many(
    #     comodel_name='crossovered.budget.lines',
    #     inverse_name='asset_id',
    #     string='Budget Lines', tracking=True)
    safety_certificate_ids = fields.One2many(
        comodel_name='property.safety.certificate',
        inverse_name='property_id',
        string='Safety Certificate', tracking=True)
    account_move_ids = fields.One2many(
        comodel_name='account.move',
        inverse_name='oe_asset_id',
        string='Entries',
        readonly=True,
        states={'draft': [('readonly', False)]}, tracking=True)
    depreciation_line_ids = fields.One2many(
        comodel_name='account.asset.depreciation.line',
        inverse_name='asset_id',
        string='Depreciation Lines',
        readonly=True,
        states={'draft': [('readonly', False)]}, tracking=True)
    bedroom = fields.Selection(
        [('1', '1'), ('2', '2'),
         ('3', '3'), ('4', '4'),
         ('5', '5+')],
        string='Bedrooms',
        default='1', tracking=True)
    bathroom = fields.Selection(
        [('1', '1'), ('2', '2'),
         ('3', '3'), ('4', '4'),
         ('5', '5+')],
        string='Bathrooms',
        default='1', tracking=True)
    parking = fields.Selection(
        [('1', '1'), ('2', '2'),
         ('3', '3'), ('4', '4'),
         ('5', '5+')],
        string='Parking',
        default='1', tracking=True)
    facing = fields.Selection(
        [('north', 'North'), ('south', 'South'),
         ('east', 'East'), ('west', 'West')],
        string='Facing',
        default='east', tracking=True)
    furnished = fields.Selection(
        [('none', 'None'),
         ('semi_furnished', 'Semi Furnished'),
         ('full_furnished', 'Full Furnished')],
        string='Furnishing',
        default='none',
        help='Furnishing.', tracking=True)
    state = fields.Selection(
        [('new_draft', 'Booking Open'),
         ('draft', 'Available'),
         ('book', 'Booked'),
         ('normal', 'On Lease'),
         ('close', 'Sale'),
         ('sold', 'Sold'),
         ('open', 'Running'),
         ('cancel', 'Cancel')],
        string='State',
        required=True,
        default='draft', tracking=True)
    # rent_type_id = fields.Many2one(
    #     comodel_name='rent.type',
    #     string='Rent Type', tracking=True)
    latitude = fields.Float(
        string='Latitude',
        digits=(16, 8),
        help='Latitude of the place.', tracking=True)
    longitude = fields.Float(
        string='Longitude',
        digits=(16, 8),
        help='Longitude of the place.', tracking=True)
    project = fields.Boolean('Project', default=False, tracking=True)
    booking_expire_days = fields.Integer(string="Booking Expire Days", tracking=True)
    min_received_amount = fields.Float(string="Minimum Received Amount %")
    handover_date = fields.Date(string="Handover Date", tracking=True)
    payment_plan_pre_handover_prec = fields.Float(string="Payment Plan Pre Handover % ", tracking=True)
    handover_date_prec = fields.Float(string="Hanover Date %", tracking=True)
    payment_plan_post_handover_prec = fields.Float(string="Payment Plan Post Handover %", tracking=True)
    installment_date_max = fields.Date(string="Instalment Date Maximum", tracking=True)

    vat_input_ledger_id = fields.Many2one('account.account','VAT Input Ledger', tracking=True)
    other_income_ledger_id = fields.Many2one('account.account','Other Income Ledger', tracking=True)
    admin_fee = fields.Float('Admin Fee', tracking=True)
    admin_fee_ledger_id = fields.Many2one('account.account','Admin Fee Ledger', tracking=True)
    oqood_fee_ledger_id = fields.Many2one('account.account','Oqood Fee Ledger', tracking=True)
    vat_input_amount = fields.Float('Vat Input Amount', tracking=True)
    other_income_amount = fields.Float('Other Income Amount', tracking=True)
    termination_ledger_id = fields.Many2one('account.account','Admin Fee Ledger')
    termination_invoice_fee = fields.Float('Termination Fee')


    unit_type_id = fields.Many2one('unit.type', string="Unit Type", tracking=True)
    permitted_use_id = fields.Many2one('permitted.use', string="Permitted Use", tracking=True)
    building_type_id = fields.Many2one('building.type', string="Building Type", tracking=True)
    # payment_option_ids = fields.Many2many('price.payment.option','property_id', string="Price & Payment Option", tracking=True)
    completion_date = fields.Char('Completion Date', tracking=True)
    estimated_charge = fields.Char('Estimated Service Charge', tracking=True)
    floor_plan_image = fields.Binary('Floor Plan', tracking=True)
    site_plan = fields.Binary('Site Plan', tracking=True)
    unit_layout_image = fields.Binary('Unit Layout', tracking=True)
    # parking = fields.Boolean('Parking', tracking=True)
    facing_id = fields.Many2one('property.facing','Facing', tracking=True)
    # state = fields.Selection(selection_add=[('reserved', 'Reserved')])

    schedule_a = fields.Text('Schedule A')
    schedule_b = fields.Text('Schedule B')
    schedule_c = fields.Text('Schedule C')
    schedule_d = fields.Text('Schedule D')
    schedule_e = fields.Text('Schedule E')
    schedule_f = fields.Text('Schedule F')
    schedule_g = fields.Text('Schedule G')
    schedule_h = fields.Text('Schedule H')
    schedule_i = fields.Text('Schedule I')
    schedule_a_eng = fields.Text('Schedule A Eng')
    schedule_b_eng = fields.Text('Schedule B Eng')
    schedule_c_eng = fields.Text('Schedule C Eng')
    schedule_d_eng = fields.Text('Schedule D Eng')
    schedule_e_eng = fields.Text('Schedule E Eng')
    schedule_f_eng = fields.Text('Schedule F Eng')
    schedule_g_eng = fields.Text('Schedule G Eng')
    schedule_h_eng = fields.Text('Schedule H Eng')
    schedule_i_eng = fields.Text('Schedule I Eng')
    plot_no = fields.Char('Plot no')
    booking_count = fields.Integer('# Bookings', compute='_compute_booking_count')
    spa_count = fields.Integer('# SPA', compute='_compute_spa_count')
    label_id = fields.Many2one(
        comodel_name='property.label',
        string='Label Name',
        help='Name Of Label For Ex. 1-BHK , 2-BHK etc.', tracking=True)
    # terms_and_condition_id = fields.Many2one('terms.condition', string="Booking Terms & Conditions")
    all_payment_bank_id = fields.Many2one('account.journal', 'All Payment Bank', domain="[('type', '=', 'bank')]",
                                          tracking=True)
    sale_term_id = fields.Many2one('sale.payment.term', string="Sales Terms & Conditions", tracking=True)

    min_value = fields.Float('Minimum Price')
    project_completeion_perc = fields.Float(string="Project Completion %")
    arabic_project = fields.Char(string="Arabic Project Name", tracking=True)
    arabic_plot_no = fields.Char(string="Arabic Plot No", tracking=True)

    @api.model
    def get_gross_value_as_min(self):
        prop = self.env['account.asset.asset'].search([])
        for rec in prop:
            # rec.min_value = rec.value
            rec.env.cr.execute('update account_asset_asset set min_value=%s where id = %s', (rec.value, rec.id))

    def button_bookings(self):
        booking_obj = self.env['sale.order'].search([('property_id', '=', self.id)])
        return {
            'name': _('Bookings'),
            # 'view_type': 'form',
            'view_mode': 'tree,form',
            'no_create': True,
            'res_model': 'sale.order',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', booking_obj.ids)],
        }

    def _compute_spa_count(self):
        for data in self:
            data.spa_count = len(data.env['sale.order'].search([('property_id', '=', data.id)]))

    def button_spa(self):
        spa_obj = self.env['sale.order'].search([('property_id', '=', self.id)])
        return {
            'name': _('SPA'),
            # 'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'sale.order',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', spa_obj.ids)],
            'context': {
                'create': False,
                'edit': False
            },
        }

    def _compute_booking_count(self):
        for data in self:
            data.booking_count = len(data.env['sale.order'].search([('property_id', '=', data.id)]))

    def name_get(self):
        res = []

        for field in self:
            if field.parent_id and field.project == False:
                res.append((field.id, '%s (%s)' % (field.name, field.parent_id.name)))
            else:
                res.append((field.id,'%s'%(field.name)))
        return res


    @api.model
    def create(self, vals):
        """
        This Method is used to overrides orm create method.
        @param self: The object pointer
        @param vals: dictionary of fields value.
        """
        if not vals:
            vals = {}
        if 'message_follower_ids' in vals:
            del vals['message_follower_ids']
        vals['code'] = self.env['ir.sequence'].next_by_code('property')
        if vals.get('parent_id'):
            parent_periods = self.browse(vals.get('parent_id'))
            if parent_periods.rent_type_id and parent_periods.rent_type_id.id:
                vals.update({'rent_type_id': parent_periods.rent_type_id.id})
        acc_analytic_id = self.env['account.analytic.account'].sudo()
        acc_analytic_id.create({'name': vals['name']})
        # image_resize_images(vals, sizes={'image': (1024, None)})
        return super(AccountAssetAsset, self).create(vals)

    
    def write(self, vals):
        """
        This Method is used to overrides orm write method.
        @param self: The object pointer
        @param vals: dictionary of fields value.
        """
        if 'state' in vals and vals['state'] == 'new_draft':
            vals.update({'color': 0})
        if 'state' in vals and vals['state'] == 'draft':
            vals.update({'color': 4})
        if 'state' in vals and vals['state'] == 'book':
            vals.update({'color': 2})
        if 'state' in vals and vals['state'] == 'normal':
            vals.update({'color': 7})
        if 'state' in vals and vals['state'] == 'close':
            vals.update({'color': 9})
        if 'state' in vals and vals['state'] == 'sold':
            vals.update({'color': 9})
        if 'state' in vals and vals['state'] == 'cancel':
            vals.update({'color': 1})
        # image_resize_images(vals, sizes={'image': (1024, None)})
        return super(AccountAssetAsset, self).write(vals)

    @api.onchange('parent_id')
    def parent_property_onchange(self):
        """
        when you change Parent Property, this method will change
        address fields values accordingly.
        @param self: The object pointer
        """
        if self.parent_id:
            self.street = self.parent_id.street or ''
            self.street2 = self.parent_id.street2 or ''
            self.township = self.parent_id.township or ''
            self.city = self.parent_id.city or ''
            self.state_id = self.parent_id.state_id.id or False
            self.zip = self.parent_id.zip or ''
            self.country_id = self.parent_id.country_id.id or False

    @api.onchange('gfa_feet')
    def sqft_to_meter(self):
        """
        when you change GFA Feet, this method will change
        GFA Meter field value accordingly.
        @param self: The object pointer
        @return: Calculated GFA Feet.
        """
        meter_val = 0.0
        if self.gfa_feet:
            meter_val = float(self.gfa_feet / 10.7639104)
        self.gfa_meter = meter_val

    @api.onchange('unit_price', 'gfa_feet')
    def unit_price_calc(self):
        """
        when you change Unit Price and GFA Feet fields value,
        this method will change Total Price and Purchase Value
        accordingly.
        @param self: The object pointer
        """
        if self.unit_price and self.gfa_feet:
            self.total_price = float(self.unit_price * self.gfa_feet)
            self.value = float(self.unit_price * self.gfa_feet)
        if self.unit_price and not self.gfa_feet:
            raise ValidationError(_('Please Insert GFA(Sqft).'))

    
    def edit_status(self):
        """
        This method is used to change property state to book.
        @param self: The object pointer
        """
        for rec in self:
            if not rec.property_manager:
                raise ValidationError(_('Please Insert Owner Name!'))
        return self.write({'state': 'book'})

    
    def edit_status_book(self):
        """
        This method will open a wizard.
        @param self: The object pointer
        """
        context = dict(self._context)
        for rec in self:
            context.update({'edit_result': rec.id})
        return {
            'name': ('wizard'),
            'res_model': 'book.available.wiz',
            'type': 'ir.actions.act_window',
            'view_id': False,
            'view_mode': 'form',
            # 'view_type': 'form',
            'target': 'new',
            'context': context,
        }

    
    def open_url(self):
        """
        This Button method is used to open a URL
        according fields values.
        @param self: The object pointer
        """
        for line in self:
            url = "http://maps.google.com/maps?oi=map&q="
            if line.name:
                street_s = re.sub(r'[^\w]', ' ', line.name)
                street_s = re.sub(' +', '+', street_s)
                url += street_s + '+'
            if line.street:
                street_s = re.sub(r'[^\w]', ' ', line.street)
                street_s = re.sub(' +', '+', street_s)
                url += street_s + '+'
            if line.street2:
                street_s = re.sub(r'[^\w]', ' ', line.street2)
                street_s = re.sub(' +', '+', street_s)
                url += street_s + '+'
            if line.township:
                street_s = re.sub(r'[^\w]', ' ', line.township)
                street_s = re.sub(' +', '+', street_s)
                url += street_s + '+'
            if line.city:
                street_s = re.sub(r'[^\w]', ' ', line.city)
                street_s = re.sub(' +', '+', street_s)
                url += street_s + '+'
            if line.state_id:
                street_s = re.sub(r'[^\w]', ' ', line.state_id.name)
                street_s = re.sub(' +', '+', street_s)
                url += street_s + '+'
            if line.country_id:
                street_s = re.sub(r'[^\w]', ' ', line.country_id.name)
                street_s = re.sub(' +', '+', street_s)
                url += street_s + '+'
            if line.latitude:
                street_s = re.sub(r'[^\w]', ' ', str(line.latitude))
                street_s = re.sub(' +', '+', street_s)
                url += street_s + '+'
            if line.street2:
                street_s = re.sub(r'[^\w]', ' ', str(line.longitude))
                street_s = re.sub(' +', '+', street_s)
                url += street_s + '+'

            if line.zip:
                url += line.zip
            return {
                'name': _('Go to website'),
                'res_model': 'ir.actions.act_url',
                'type': 'ir.actions.act_url',
                'target': 'current',
                'url': url
            }

    
    def button_normal(self):
        """
        This Button method is used to change property state to On Lease.
        @param self: The object pointer
        """
        for rec in self:
            rec.write({'state': 'normal'})

    
    def button_sold(self):
        """
        This Button method is used to change property state to Sold.
        @param self: The object pointer
        """
        invoice_obj = self.env['account.move']
        for data in self:
            if not data.expense_account_id:
                raise Warning(_('Please Configure Income \
                                Account from Property!'))
            inv_line_values = {
                'name': data.name or "",
                'origin': 'account.asset.asset',
                'quantity': 1,
                'account_id': data.income_acc_id.id or False,
                'price_unit': data.sale_price or 0.00,
            }

            inv_values = {
                'origin': data.name or "",
                'move_type': 'out_invoice',
                'property_id': data.id,
                'partner_id': data.customer_id.id or False,
                'payment_term_id': data.payment_term.id,
                'invoice_line_ids': [(0, 0, inv_line_values)],
                'invoice_date': datetime.now().strftime(
                    DEFAULT_SERVER_DATE_FORMAT) or False,
                'number': data.code or '',
            }
            invoice_obj.create(inv_values)
            data.write({'state': 'sold'})
            return True

    
    def button_close(self):
        """
        This Button method is used to change property state to Sale.
        @param self: The object pointer
        """
        for rec in self:
            rec.write({'state': 'close'})

    
    def button_cancel(self):
        """
        This Button method is used to change property state to Cancel.
        @param self: The object pointer
        """
        for rec in self:
            rec.write({'state': 'cancel'})

    
    def button_draft(self):
        """
        This Button method is used to change property state to Available.
        @param self: The object pointer
        """
        for rec in self:
            rec.write({'state': 'draft'})

    
    def date_addition(self, starting_date, end_date, period):
        date_list = []
        if period == 'monthly':
            while starting_date < end_date:
                date_list.append(starting_date)
                res = ((
                    starting_date + relativedelta(months=1)))
                starting_date = res
            return date_list
        else:
            while starting_date < end_date:
                date_list.append(starting_date)
                res = ((
                    starting_date + relativedelta(years=1)))
                starting_date = res
            return date_list
