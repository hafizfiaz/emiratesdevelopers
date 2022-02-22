# See LICENSE file for full copyright and licensing details

from odoo import http
from odoo.http import request
from odoo.addons.web.controllers.main import Home
from datetime import datetime
import werkzeug

from odoo.addons.payment_paypal.controllers.main import PaypalController

def get_cookie_list():
    account_asset_cookie_ids = []
    if request.uid == request.website.user_id.id:
        product_ids_from_cookies = request.httprequest.cookies.get(
            'property_id')
        product_ids_from_cookies_str = str(product_ids_from_cookies)
        product_ids_from_cookies_list = product_ids_from_cookies_str.split(',')

        if product_ids_from_cookies_list[0] == 'None':
            account_asset_cookie_ids = []
        else:
            for one_prod_cookie_id in product_ids_from_cookies_list:
                if not one_prod_cookie_id:
                    continue
                one_cookie_int_id = int(one_prod_cookie_id)
                account_asset_cookie_ids.append(one_cookie_int_id)
        return account_asset_cookie_ids
    else:
        user = request.env['res.users'].browse(request.uid)
        account_asset_cookie_ids = user.partner_id.sudo().fav_assets_ids.ids
    return account_asset_cookie_ids

def buypage_content():
    account_asset_sold = request.env['account.asset.asset'].sudo().search([('state', '=', 'draft'),('parent_id.name', '=', 'Samana Golf Avenue')], limit=6, order='write_date desc')
    all_payment_schedules = request.env['payment.schedule'].search(
        [('on_website', '=', True)])
    all_menues = request.env['account.asset.asset'].search([('menu_visible', '!=', False)])
    menu_array = {}
    menu_array_id = {}
    menu_list = []
    for m in all_menues:
        menu_list.append(m.menu_name)
        menu_array[m.menu_name] = '/all_asset_lease_golf?id=' + str(m.id)
        menu_array_id[m.menu_name] = m.id
        print(m.menu_url)
    print(menu_list)
    return {
        'all_property_objs': account_asset_sold,
        'all_payment_schedules': all_payment_schedules,
        'product_ids_from_cookies_list': get_cookie_list(),
        'facebook_share': request.env['ir.config_parameter'].get_param('property_share_kay_facebook'),
        'twitter_share': request.env['ir.config_parameter'].get_param('property_share_kay_twitter'),
        'menu_list': menu_list,
        'menu_array': menu_array,
        'menu_array_id': menu_array_id,
    }

def salepage_content():
    account_asset_sold = request.env['account.asset.asset'].search([(
        'state', '=', 'sold')], limit=6, order='write_date desc')
    countries = request.env['res.country'].search([])
    all_payment_schedules = request.env['payment.schedule'].search(
        [('on_website', '=', True)])

    all_menues = request.env['account.asset.asset'].search([('menu_visible', '!=', False)])
    menu_array = {}
    menu_array_id = {}
    menu_list = []
    for m in all_menues:
        menu_list.append(m.menu_name)
        menu_array[m.menu_name] = '/all_asset_lease_golf?id=' + str(m.id)
        menu_array_id[m.menu_name] = m.id
        print(m.menu_url)
    return {
        'countries': countries,
        'all_property_objs': account_asset_sold,
        'all_payment_schedules': all_payment_schedules,
        'product_ids_from_cookies_list': get_cookie_list(),
        'facebook_share': request.env['ir.config_parameter'].get_param('property_share_kay_facebook'),
        'twitter_share': request.env['ir.config_parameter'].get_param('property_share_kay_twitter'),
        'menu_list': menu_list,
        'menu_array': menu_array,
        'menu_array_id': menu_array_id,
    }


class PaypalController(PaypalController):

    def _get_return_url(self, **post):
        """ Extract the return URL from the data coming from paypal. """
        return_url = post.pop('return_url', '')
        if not return_url:
            custom = json.loads(post.pop('custom', False) or '{}')
            if post.get('item_name'):
                return_url = custom.get(
                    'return_url', '/selected_property_page?id=' + str(post.get('custom_values')['property_id']))
            else:
                return_url = custom.get('return_url', '/')
        return return_url

    def paypal_validate_data(self, **post):
        """ Paypal IPN: three steps validation to ensure data correctness
         - step 1: return an empty HTTP 200 response -> will be done at the end
           by returning ''
         - step 2: POST the complete, unaltered message back to Paypal (preceded
           by cmd=_notify-validate), with same encoding
         - step 3: paypal send either VERIFIED or INVALID (single word)

        Once data is validated, process it. """
        res = False
        new_post = dict(post, cmd='_notify-validate')
        reference = post.get('new_transaction_name')
        tx = None
        if reference:
            tx = request.registry['payment.transaction'].search(
                [('reference', '=', reference)])
        paypal_urls = request.registry['payment.acquirer']._get_paypal_urls(
            tx and tx.acquirer_id and tx.acquirer_id.environment or 'prod')
        validate_url = paypal_urls['paypal_form_url']
        resp = requests.post(validate_url, data=werkzeug.url_encode(new_post))
        resp = resp.content
        if resp == 'VERIFIED':
            _logger.info('Paypal: validated data')
            res = request.registry['payment.transaction'].sudo(
            ).form_feedback(post, 'paypal')
            # change state in transaction
            change_state = request.registry['payment.transaction'].sudo().write(int(
                post.get('new_transaction_id')), {'state': 'done'})
            # Create new Move
            create_new_move = request.registry['tenancy.rent.schedule'].sudo(
            ).create_move([int(post.get('custom_values')['payment_id'])])

        elif resp == 'INVALID':
            _logger.warning('Paypal: answered INVALID on data verification')
        else:
            _logger.warning(
                'Paypal: unrecognized paypal answer, received %s instead of VERIFIED or INVALID' % resp.text)
        return res

    @http.route('/payment/paypal/dpn', type='http', auth="none", methods=['POST'])
    def paypal_dpn(self, **post):
        custom_values = ast.literal_eval(post.get('invoice'))
        reference = str(post.get('item_number')) + '_' + \
            str(datetime.now().strftime("%Y-%m-%d_%H:%M:%S"))
        # Create new transaction in odoo
        new_transaction_id = request.env['payment.transaction'].create({
            'acquirer_id': request.env['payment.acquirer'].search([('name', '=', 'Paypal')])[0],
            'type': 'form',
            'amount': float(post.get('mc_gross')),
            'currency_id': request.env['res.currency'].search([('name', '=', str(post.get('mc_currency')))])[0],
            'partner_id': int(custom_values['partner_id']),
            'reference': reference,
        })
        post.update({'new_transaction_id': new_transaction_id,
                     'new_transaction_name': reference, 'custom_values': custom_values})
        return super(PaypalController, self).paypal_dpn(**post)


class website_property(Home):

    @http.route(['/report/pdf/sale_offer'], type='http', auth='public', website=True, csrf=False)
    def download_catalogue(self, *args, **kw):
        """In this function we are calling the report template
        of the corresponding product and
        downloads the catalogue in pdf format"""
        print("Rashid Rashid")
        if kw.get('button2'):

            # report_1 = request.env['payment.schedule'].search(
            #     [('id', '=', int(kw['paymentlist']))])

            pdf, _ = request.env.ref('property_website.report_website_schedule_new') \
                ._render_qweb_pdf(
                [int(kw['paymentlist']), int(kw['property_id']), 10, kw['contact_name'], kw['contact_mobile'],
                 kw['contact_email']])
        else:
            # report_1 = request.env['payment.schedule'].search(
            #     [('id', '=', int(kw['paymentlist']))])

            # report_2 = request.env['payment.schedule'].search(
            #     [('id', '=', int(kw['paymentlist']))])
            pdf, _ = request.env.ref('property_website.golf_report_website_schedule_new') \
                ._render_qweb_pdf(
                [int(kw['paymentlist']), int(kw['property_id']), 10, kw['contact_name'], kw['contact_mobile'],
                 kw['contact_email']])
        pdfhttpheaders = [('Content-Type', 'application/pdf'), ('Content-Length', len(pdf)),
                          ('Content-Disposition', 'catalogue' + '.pdf;')]
        print("RashidRashid")
        return request.make_response(pdf, headers=pdfhttpheaders)


    def homepagecontent_display(self):
        all_property_objs = request.env[
            'account.asset.asset'].sudo().search([], order='id desc')
        property_types = request.env['property.type'].sudo().search([])
        all_payment_schedules = request.env['payment.schedule'].search(
            [('on_website', '=', True)])

        all_menues = request.env['account.asset.asset'].search([('menu_visible', '!=', False)])
        menu_array = {}
        menu_array_id = {}
        menu_list = []
        for m in all_menues:
            menu_list.append(m.menu_name)
            menu_array[m.menu_name] = '/all_asset_lease_golf?id=' + str(m.id)
            menu_array_id[m.menu_name] = m.id
            print(menu_list)
            print("Rashid")
            print("AAAAAAAAAAA")
        return {
            'product_ids_from_cookies_list': get_cookie_list(),
            'property_types': property_types,
            'all_property_objs': all_property_objs,
            'all_payment_schedules': all_payment_schedules,
            'r':1,
            'menu_list': menu_list,
            'menu_array': menu_array,
            'menu_array_id': menu_array_id,
            # 'facebook_share': request.env['ir.config_parameter'].get_param('property_share_kay_facebook'),
        }

    def savedsellcontent_display(self, post):
        account_asset_all_sale_cookie_ids = get_cookie_list()
        account_asset_all_sale_cookie_obj = request.env['account.asset.asset'].search(
            [('id', 'in', account_asset_all_sale_cookie_ids)], order='id desc')

        all_menues = request.env['account.asset.asset'].search([('menu_visible', '!=', False)])
        menu_array = {}
        menu_array_id = {}
        menu_list = []
        for m in all_menues:
            menu_list.append(m.menu_name)
            menu_array[m.menu_name] = '/all_asset_lease_golf?id=' + str(m.id)
            menu_array_id[m.menu_name] = m.id
            print(m.menu_url)
        return {
            'account_asset_all_sale_cookie_obj': account_asset_all_sale_cookie_obj,
            'product_ids_from_cookies_list': get_cookie_list(),
            'property_type': post.get('property_type'),
            'page_of_saved': 'saved page',
            'facebook_share': request.env['ir.config_parameter'].get_param('property_share_kay_facebook'),
            'twitter_share': request.env['ir.config_parameter'].get_param('property_share_kay_twitter'),
            'menu_list': menu_list,
            'menu_array': menu_array,
            'menu_array_id': menu_array_id,
        }

    # @http.route(['/homepage'], type='json', auth="public", website=True)
    # def homepage(self, **kwargs):
    #     return request.env['ir.ui.view']._render_template(
    #         "property_website.homepage_content", self.homepagecontent_display())

    @http.route(['/', '/page/homepage'], type='http', auth="public", website=True)
    def homepage_http(self, **kwargs):
        return request.env['ir.ui.view']._render_template("property_website.property_homepage",
                                                         self.homepagecontent_display())

    # @http.route(['/min_max_price'], type='json', auth='public', website=True)
    # def min_max_price(self):
    #     # cr, uid, context, pool = request.cr, request.uid, request.context, request.registry
    #     asset_obj = request.env["account.asset.asset"].sudo()
    #     request.cr.execute(
    #         "SELECT MIN(ground_rent) as min_rent, MIN(sale_price) as min_sale, MAX(ground_rent) as max_rent, MAX(sale_price) as max_sale FROM account_asset_asset")
    #     value = request.cr.dictfetchall()[0]
    #     price = {
    #         'min_value': min(value.get('min_rent'), value.get('min_sale')),
    #         'max_value': max(value.get('max_rent'), value.get('max_sale')),
    #     }
    #     return price
# class website_property(http.Controller):
    _post_per_page = 16

    def common_content_lease_sale(self, post):
        if post.get('page'):
            page = post.get('page')
        else:
            page = 0
        domain = []
        values = {}
        dropdown_furnished = post.get('dropdown_furnish')
        if dropdown_furnished == 'full_furnished':
            domain += [('furnished', '=', 'full_furnished')]
            values.update({'dropdown_furnish': 'full_furnished'})
        elif dropdown_furnished == 'semi_furnished':
            domain += [('furnished', '=', 'semi_furnished')]
            values.update({'dropdown_furnish': 'semi_furnished'})
        elif dropdown_furnished == 'none':
            domain += [('furnished', '=', 'none')]
            values.update({'dropdown_furnish': 'none'})
        elif dropdown_furnished == 'all':
            values.update({'dropdown_furnish': 'all'})

        dropdown_facing = post.get('dropdown_facing')
        if dropdown_facing == 'east':
            domain += [('facing', '=', 'east')]
            values.update({'dropdown_facing': 'east'})
        elif dropdown_facing == 'west':
            domain += [('facing', '=', 'west')]
            values.update({'dropdown_facing': 'west'})
        elif dropdown_facing == 'north':
            domain += [('facing', '=', 'north')]
            values.update({'dropdown_facing': 'north'})
        elif dropdown_facing == 'south':
            domain += [('facing', '=', 'south')]
            values.update({'dropdown_facing': 'south'})
        elif dropdown_facing == 'all':
            values.update({'dropdown_facing': 'all'})

        if post.get('postcode'):
            domain += [('zip', 'ilike', post.get('postcode'))]
            values.update({'postcode': post.get('postcode')})

        if post.get('city') and post.get('area'):
            if post.get('city') == post.get('area'):
                values.update({'city': post.get('city')})
                values.update({'area': ''})
                domain += [('city', 'ilike', post.get('city'))]
            else:
                values.update({'area': post.get('area')})
                values.update({'city': post.get('city')})
                domain += ['|',
                           ('street', 'ilike', post.get('area')), '|',
                           ('name', 'ilike', post.get('area')),
                           ('street2', 'ilike', post.get('area')), '|',
                           ('city', 'ilike', post.get('city'))]
        else:
            values.update({'area': post.get('area')})
            if post.get('area'):
                # domain += [('street','ilike',post.get('area'))]
                domain += ['|', ('street', 'ilike', post.get('area')),
                           '|', ('name', 'ilike', post.get('area'))]
            values.update({'city': post.get('city')})
            if post.get('city'):
                domain += [('city', 'ilike', post.get('city'))]
            domain += [('street2', 'ilike', post.get('area'))]

        if post.get('state'):
            values.update({'state': post.get('state')})
            country_state_ids = request.env['res.country.state'].search(
                [('code', 'ilike', post.get('state'))])
            domain += [('state_id', 'in', country_state_ids.ids)]

        if post.get('country'):
            values.update({'country': post.get('country')})
            country_ids = res_country = request.env['res.country'].search(
                [('name', 'ilike', post.get('country'))])
            domain += [('country_id', 'in', country_ids.ids)]
        if post.get('min_range') and post.get('min_range'):
            domain += [('sale_price', '>=', post.get('min_range')),
                       ('sale_price', '<=', post.get('max_range'))]
            values.update(
                {'min_range': post.get('min_range'), 'max_range': post.get('max_range')})

        # bedroom slider domain
        values.update({'min_bead': 1, 'max_bead': 5})
        if post.get('min_bead') and post.get('max_bead'):
            values.update(
                {'min_bead': post.get('min_bead'), 'max_bead': post.get('max_bead')})
            domain += [('bedroom', '>=', post.get('min_bead')),
                       ('bedroom', '<=', post.get('max_bead'))]

        # bathroom slider domain
        values.update({'min_bath': 1, 'max_bath': 5})
        if post.get('min_bath') and post.get('max_bath'):
            values.update(
                {'min_bath': post.get('min_bath'), 'max_bath': post.get('max_bath')})
            domain += [('bathroom', '>=', post.get('min_bath')),
                       ('bathroom', '<=', post.get('max_bath'))]

        if post.get('total_selected_property_type_ids'):
            domain += [('type_id', 'in',
                        post.get('total_selected_property_type_ids'))]

        values.update({'facebook_share': request.env['ir.config_parameter'].get_param('property_share_kay_facebook'),
                       'twitter_share': request.env['ir.config_parameter'].get_param('property_share_kay_twitter')})

        return {'domain': domain, 'values': values}

    def allleasecontent_display_golf(self, post):

        if post.get('page'):
            page = post.get('page')
        else:
            page = 0
        domain = []
        values = {}
        account_asset_asset_obj = request.env['account.asset.asset']

        common = self.common_content_lease_sale(post)
        if common.get('domain'):
            domain = common.get('domain')
        if common.get('values'):
            values = common.get('values')

        property_types = request.env['property.type'].sudo().search([])

        total_selected_property_type_ids = []
        if post.get('total_selected_property_type_ids'):
            print("ifififif")
            total_selected_property_type_ids = post.get(
                'total_selected_property_type_ids')

        # if post.get('click_value') == 'rent':
        #     dropdown_price = post.get('dropdown_price')
        #     if dropdown_price == 'lowest':
        #         order = 'ground_rent asc'
        #         values.update({'dropdown_price': 'lowest'})
        #     elif dropdown_price == 'highest':
        #         order = 'ground_rent desc'
        #         values.update({'dropdown_price': 'highest'})
        #     elif dropdown_price == 'newest':
        #         order = 'create_date desc'
        #         values.update({'dropdown_price': 'newest'})
        #     elif dropdown_price == 'all':
        #         order = None
        #         values.update({'dropdown_price': 'all'})

            domain = [('web_state', 'in', ['draft','sold']),('parent_id.name', '=', 'Samana Golf Avenue')]
            if post.get('id'):
                domain = [('web_state', 'in', ['draft', 'sold']), ('parent_id', '=', int(post.get('id')))]
            if post.get('unittype'):
                domain += [('unit_type_id','=',post.get('unittype'))]
            if post.get('viewlist'):
                domain += [('facing_id','=',post.get('viewlist'))]
            if post.get('number'):
                domain += [('name','=',post.get('number'))]
            if post.get('status'):
                domain += [('web_state','=',post.get('status'))]
            # account_asset_lease_all_ids = account_asset_asset_obj.search(
            #     domain, order='id desc')
            #
            # total = len(account_asset_lease_all_ids.ids)
            # pageUrl = '/all_asset_lease_golf'
            # pager = request.website.pager(
            #     url=pageUrl,
            #     total=total,
            #     page=page,
            #     step=self._post_per_page,
            #     url_args=post
            # )

            available_account_asset_lease = len(request.env['account.asset.asset'].search(
                [('web_state','=','draft'),('parent_id.name', '=', 'Samana Golf Avenue')]))
            sold_account_asset_lease = len(request.env['account.asset.asset'].search(
                [('web_state','=','sold'),('parent_id.name', '=', 'Samana Golf Avenue')]))
            account_asset_lease = request.env['account.asset.asset'].search(
                domain, order='name asc')
            if post.get('id'):
                all_payment_schedules = request.env['payment.schedule'].search(
                    [('on_website', '=', True),('asset_project_id', '=', int(post.get('id')))])
            else:
                all_payment_schedules = request.env['payment.schedule'].search(
                    [('on_website', '=', True)])


            if post.get('id'):
                available_account_asset_lease = len(request.env['account.asset.asset'].search(
                    [('web_state', '=', 'draft'), ('parent_id', '=', int(post.get('id')))]))

                sold_account_asset_lease = len(request.env['account.asset.asset'].search(
                    [('web_state', '=', 'sold'), ('parent_id', '=', int(post.get('id')))]))
            all_menues = request.env['account.asset.asset'].search([('menu_visible', '!=', False)])
            menu_array = {}
            menu_array_id = {}
            menu_list = []
            for m in all_menues:
                menu_list.append(m.menu_name)
                menu_array[m.menu_name] = '/all_asset_lease_golf?id=' + str(m.id)
                menu_array_id[m.menu_name] = m.id
                print(menu_list)
            all_unit_type = request.env['unit.type'].search([])
            all_views = request.env['property.facing'].search([])
            values.update({
                # 'pager': pager,
                'product_ids_from_cookies_list': get_cookie_list(),
                'property_type': 'alllease',
                'property_types': property_types,
                'total_selected_property_type_ids': total_selected_property_type_ids,
                'all_property_objs': account_asset_lease,
                'all_payment_schedules': all_payment_schedules,
                'all_unit_type': all_unit_type,
                'all_views': all_views,
                'available_account_asset_lease': available_account_asset_lease,
                'sold_account_asset_lease': sold_account_asset_lease,
                'menu_list': menu_list,
                'menu_array': menu_array,
                'menu_array_id': menu_array_id,
            })
            return values

        else:
            print("Else")
            # if post.get('viewlist'):
            #     account_asset_lease_all_ids = account_asset_asset_obj.search(
            #         [('state', '=', 'draft'),('parent_id.name', '=', 'Samana Golf Avenue'),('facing_id', '=', post.get('viewlist'))], order='id desc')
            domain = [('web_state', 'in', ['draft','sold']),('parent_id.name', '=', 'Samana Golf Avenue')]
            if post.get('id'):
                domain = [('web_state', 'in', ['draft', 'sold']), ('parent_id.id', '=', int(post.get('id')))]
            if post.get('unittype'):
                domain += [('unit_type_id', '=', int(post.get('unittype')))]
            if post.get('viewlist'):
                domain += [('facing_id', '=', int(post.get('viewlist')))]
            if post.get('number'):
                if post.get('number') != '':
                    domain += [('name', '=', post.get('number'))]
            if post.get('status'):
                if post.get('status') != '':
                    domain += [('web_state', '=', post.get('status'))]
            # account_asset_lease_all_ids = account_asset_asset_obj.search(
            #         domain, order='id desc')
            #
            # total = len(account_asset_lease_all_ids.ids)
            # pageUrl = '/all_asset_lease_golf'
            # pager = request.website.pager(
            #     url=pageUrl,
            #     total=total,
            #     page=page,
            #     step=self._post_per_page,
            #     url_args=post
            # )

            # if post.get('viewlist'):
            #     account_asset_lease = account_asset_asset_obj.search(
            #         [('state', '=', 'draft'),('parent_id.name', '=', 'Samana Golf Avenue'),('facing_id', '=', post.get('viewlist'))], limit=self._post_per_page, order='id d', offset=pager['offset'])


            # if post.get('unittype'):
            #     account_asset_lease = account_asset_asset_obj.search(
            #         [('state', '=', 'draft'),('parent_id.name', '=', 'Samana Golf Avenue'),('unit_type_id', '=', post.get('unittype'))], limit=self._post_per_page, order='id desc', offset=pager['offset'])
            #
            # else:
            available_account_asset_lease = len(request.env['account.asset.asset'].search(
                [('web_state', '=', 'draft'),('parent_id.name', '=', 'Samana Golf Avenue')]))

            sold_account_asset_lease = len(request.env['account.asset.asset'].search(
                [('web_state', '=', 'sold'),('parent_id.name', '=', 'Samana Golf Avenue')]))
            account_asset_lease = account_asset_asset_obj.search(
                domain, order='name asc')
            if post.get('id'):

                all_payment_schedules = request.env['payment.schedule'].search(
                    [('on_website', '=', True), ('asset_project_id', '=', int(post.get('id')))])
            else:
                all_payment_schedules = request.env['payment.schedule'].search(
                    [('on_website', '=', True)])
            if post.get('id'):
                available_account_asset_lease = len(request.env['account.asset.asset'].search(
                    [('web_state', '=', 'draft'), ('parent_id', '=', int(post.get('id')))]))

                sold_account_asset_lease = len(request.env['account.asset.asset'].search(
                    [('web_state', '=', 'sold'), ('parent_id.id', '=', int(post.get('id')))]))
            all_unit_type = request.env['unit.type'].search([])
            all_views = []
            # all_views = request.env['property.facing'].search([])
            all_menues = request.env['account.asset.asset'].search([('menu_visible', '!=', False)])
            menu_array = {}
            menu_array_id = {}
            menu_list = []
            for m in all_menues:
                menu = request.env['website.menu'].sudo().search([('name','=',m.menu_name)])
                parent_menu = request.env['website.menu'].sudo().search([('parent_id', '=', False)])
                if not menu:
                    request.env['website.menu'].sudo().create({
                        'name': m.menu_name,
                        'url': '/all_asset_lease_golf?id=' + str(m.id),
                        'parent_id': 1,
                        'sequence': 100,
                    })
                menu_list.append(m.menu_name)
                menu_array[m.menu_name] = '/all_asset_lease_golf?id=' + str(m.id)
                menu_array_id[m.menu_name] = m.id
            print(menu_list)
            print(menu_array)
            return {
                # 'pager': pager,
                'product_ids_from_cookies_list': get_cookie_list(),
                'property_type': 'alllease',
                'property_types': property_types,
                'total_selected_property_type_ids': total_selected_property_type_ids,
                'all_property_objs': account_asset_lease,
                'all_payment_schedules': all_payment_schedules,
                'all_unit_type': all_unit_type or [],
                'all_views': all_views or [],
                'available_account_asset_lease': available_account_asset_lease,
                'sold_account_asset_lease': sold_account_asset_lease,
                'menu_list': menu_list,
                'menu_array': menu_array,
                'menu_array_id': menu_array_id,
            }

    def allleasecontent_display(self, post):
        if post.get('page'):
            page = post.get('page')
        else:
            page = 0
        domain = []
        values = {}
        account_asset_asset_obj = request.env['account.asset.asset']

        common = self.common_content_lease_sale(post)
        if common.get('domain'):
            domain = common.get('domain')
        if common.get('values'):
            values = common.get('values')

        property_types = request.env['property.type'].sudo().search([])

        total_selected_property_type_ids = []
        if post.get('total_selected_property_type_ids'):
            total_selected_property_type_ids = post.get(
                'total_selected_property_type_ids')

        if post.get('click_value') == 'rent':
            dropdown_price = post.get('dropdown_price')
            if dropdown_price == 'lowest':
                order = 'ground_rent asc'
                values.update({'dropdown_price': 'lowest'})
            elif dropdown_price == 'highest':
                order = 'ground_rent desc'
                values.update({'dropdown_price': 'highest'})
            elif dropdown_price == 'newest':
                order = 'create_date desc'
                values.update({'dropdown_price': 'newest'})
            elif dropdown_price == 'all':
                order = None
                values.update({'dropdown_price': 'all'})

            domain += [('state', '=', 'draft')]
            account_asset_lease_all_ids = account_asset_asset_obj.search(
                domain, order='id desc')

            total = len(account_asset_lease_all_ids.ids)
            pageUrl = '/all_asset_lease_golf'
            pager = request.website.pager(
                url=pageUrl,
                total=total,
                page=page,
                step=self._post_per_page,
                url_args=post
            )

            account_asset_lease = request.env['account.asset.asset'].search(
                domain, limit=self._post_per_page, order='id desc', offset=pager['offset'])
            if post.get('id'):
                all_payment_schedules = request.env['payment.schedule'].search(
                    [('on_website', '=', True), ('asset_project_id', '=', int(post.get('id')))])
            else:
                all_payment_schedules = request.env['payment.schedule'].search(
                    [('on_website', '=', True)])
            all_menues = request.env['account.asset.asset'].search([('menu_visible', '!=', False)])
            menu_array = {}
            menu_array_id = {}
            menu_list = []
            for m in all_menues:
                menu_list.append(m.menu_name)
                menu_array[m.menu_name] = '/all_asset_lease_golf?id=' + str(m.id)
                menu_array_id[m.menu_name] = m.id
                print(m.menu_url)
            values.update({
                'pager': pager,
                'product_ids_from_cookies_list': get_cookie_list(),
                'property_type': 'alllease',
                'property_types': property_types,
                'total_selected_property_type_ids': total_selected_property_type_ids,
                'all_property_objs': account_asset_lease,
                'all_payment_schedules': all_payment_schedules,
                'menu_list': menu_list,
                'menu_array': menu_array,
                'menu_array_id': menu_array_id,
            })
            return values

        else:
            account_asset_lease_all_ids = account_asset_asset_obj.search(
                [('state', '=', 'draft')], order='id desc')

            total = len(account_asset_lease_all_ids.ids)
            pageUrl = '/all_asset_lease_golf'
            pager = request.website.pager(
                url=pageUrl,
                total=total,
                page=page,
                step=self._post_per_page,
                url_args=post
            )

            account_asset_lease = account_asset_asset_obj.search(
                [('state', '=', 'draft')], limit=self._post_per_page, order='id desc', offset=pager['offset'])
            if post.get('id'):
                all_payment_schedules = request.env['payment.schedule'].search(
                    [('on_website', '=', True), ('asset_project_id', '=', int(post.get('id')))])
            else:
                all_payment_schedules = request.env['payment.schedule'].search(
                    [('on_website', '=', True)])
            all_menues = request.env['account.asset.asset'].search([('menu_visible', '!=', False)])
            menu_array = {}
            menu_array_id = {}
            menu_list = []
            for m in all_menues:
                menu_list.append(m.menu_name)
                menu_array[m.menu_name] = '/all_asset_lease_golf?id=' + str(m.id)
                menu_array_id[m.menu_name] = m.id
                print(m.menu_url)
            return {
                'pager': pager,
                'product_ids_from_cookies_list': get_cookie_list(),
                'property_type': 'alllease',
                'property_types': property_types,
                'total_selected_property_type_ids': total_selected_property_type_ids,
                'all_property_objs': account_asset_lease,
                'all_payment_schedules': all_payment_schedules,
                'menu_list': menu_list,
                'menu_array': menu_array,
                'menu_array_id': menu_array_id,
            }

    def allpastleasecontent_display(self, post):
        if post.get('page'):
            page = post.get('page')
        else:
            page = 0

        account_asset_asset_obj = request.env['account.asset.asset']
        account_asset_sold_ids = account_asset_asset_obj.search(
            [('state', 'in', ['book', 'normal'])], order='write_date desc')

        total = len(account_asset_sold_ids.ids)
        pageUrl = '/all_past_lease'
        pager = request.website.pager(
            url=pageUrl,
            total=total,
            page=page,
            step=self._post_per_page,
            url_args=post
        )

        all_property_objs = account_asset_asset_obj.search(
            [('state', 'in', ['book', 'normal'])], limit=self._post_per_page, order='write_date desc',
            offset=pager['offset'])
        if post.get('id'):
            all_payment_schedules = request.env['payment.schedule'].search(
                [('on_website', '=', True), ('asset_project_id', '=', int(post.get('id')))])
        else:
            all_payment_schedules = request.env['payment.schedule'].search(
                [('on_website', '=', True)])
        all_menues = request.env['account.asset.asset'].search([('menu_visible', '!=', False)])
        menu_array = {}
        menu_array_id = {}
        menu_list = []
        for m in all_menues:
            menu_list.append(m.menu_name)
            menu_array[m.menu_name] ='/all_asset_lease_golf?id=' + str(m.id)
            menu_array_id[m.menu_name] = m.id
            print(m.menu_url)
        return {
            # 'account_asset_sold': account_asset_sold,
            'pager': pager,
            'product_ids_from_cookies_list': get_cookie_list(),
            'property_type': 'allpastlease',
            'all_property_objs': all_property_objs,
            'all_payment_schedules': all_payment_schedules,
            'facebook_share': request.env['ir.config_parameter'].get_param('property_share_kay_facebook'),
            'twitter_share': request.env['ir.config_parameter'].get_param('property_share_kay_twitter'),
            'menu_list': menu_list,
            'menu_array': menu_array,
            'menu_array_id': menu_array_id,
        }


    def selected_property_function(self, selected_id):
        selected_property_id = selected_id
        account_asset_asset_obj = request.env['account.asset.asset'].sudo()
        account_asset_property_rec = account_asset_asset_obj.browse(
            selected_id)

        suggested_properties_ids = \
            account_asset_property_rec.suggested_property_ids
        suggested_properties_ids_list = [
            one_id.other_property_id.id for one_id in suggested_properties_ids]
        # for one_id in suggested_properties_ids:
        #     suggested_properties_ids_list.append(one_id.other_property_id.id)
        # set_value = set(suggested_properties_ids_list)
        suggested_properties_ids_list = \
            list(set(suggested_properties_ids_list))

        suggeste_properties_obj = account_asset_asset_obj.browse(
            suggested_properties_ids_list)

        values = {
            'account_asset_property_obj': account_asset_property_rec,
            'suggeste_properties_obj': suggeste_properties_obj,
            'product_ids_from_cookies_list': get_cookie_list(),
        }

        date_today = datetime.now().date()
        # date_today = datetime.strftime(date_today, DEFAULT_SERVER_DATE_FORMAT)
        tenant_obj = request.env['account.analytic.account'].sudo()
        tenant_browse = tenant_obj.search(
            [('date_start', '<=', date_today), ('date', '>=', date_today)])
        my_property_list = [
            one_tenant.property_id and one_tenant.property_id.id for one_tenant in tenant_browse]
        # for one_tenant in tenant_browse:
        #     my_property_list.append(one_tenant.property_id.id)
        if selected_id in my_property_list:
            values.update({'already_booked': 'Property already Booked'})

        account_asset_sold_ids = account_asset_asset_obj.search(
            [('state', '=', 'sold')], order='write_date desc').ids
        if selected_id in account_asset_sold_ids:
            values.update({'already_booked': 'Property already Sold'})

        res_user_browse = request.env.user
        if res_user_browse.tenant_id:
            tenant_browse = tenant_obj.search(
                [('tenant_id', '=', res_user_browse.tenant_id.id)])
            my_property_list = [
                one_tenant.property_id.id for one_tenant in tenant_browse]
            # for one_tenant in tenant_browse:
            #     my_property_list.append(one_tenant.property_id.id)
            if my_property_list:
                if selected_property_id in my_property_list:
                    selected_tenant = tenant_obj.search([
                        ('tenant_id', '=', res_user_browse.tenant_id.id),
                        ('property_id', '=', selected_property_id),
                        ('date_start', '<=', date_today),
                        ('date', '>=', date_today)])
                    # code for paypal payment button
                    payment_acquirer_obj = request.env['payment.acquirer']
                    base_url = payment_acquirer_obj.env[
                        'ir.config_parameter'].get_param('web.base.url')
                    acquirer_id = payment_acquirer_obj.search(
                        [('name', '=', 'Paypal')])
                    acquirer = payment_acquirer_obj.browse(acquirer_id.id)
                    tx_url = acquirer.get_form_action_url(),
                    values.update({
                        'tx_url': tx_url[0],
                        'business': acquirer.paypal_email_account,
                        'cmd': '_xclick',
                        'item_name': acquirer.company_id.name + ':' +
                        account_asset_property_rec.name,
                        'item_number': selected_tenant.name,
                        'partner': res_user_browse.partner_id,
                        # 'return_url': '%s' % urlparse.urljoin(
                        #     base_url, PaypalController._return_url),
                        # 'notify_url': '%s' % urlparse.urljoin(
                        #     base_url, PaypalController._notify_url),
                        # 'cancel_return': '%s' % urlparse.urljoin(
                        #     base_url, PaypalController._cancel_url),
                        'return_url': '%s' % str.join(base_url, PaypalController._return_url),
                        'notify_url': '%s' % str.join(base_url, PaypalController._notify_url),
                        'cancel_return': '%s' % str.join(base_url, PaypalController._cancel_url),
                        'selected_tenant': selected_tenant,
                    })
                    maintenance_types = \
                        request.env['maintenance.team'].search([])
                    values.update({
                        'maintenance_types': maintenance_types,
                        'my_propery': 'true',
                    })
        return values

    # @http.route('/samana-<int:channel_id>', type='http', auth='public')
    # def support_page(self, channel_id, **kwargs):
    #     channel = request.env['im_livechat.channel'].sudo().browse(channel_id)
    #     return request.render('im_livechat.support_page', {'channel': channel})

    @http.route('/samana_golf', type='http', auth='user', website=True)
    def show_custom_webpage(self, **kw):
        return request.render('property_website.samana_golf_onload', buypage_content())

    @http.route(['/samana_golf'], type='http', auth="public", website=True)
    def buy_properties_onloads(self, **kwargs):
        return request.env['ir.ui.view']._render_template("property_website.samana_golf_onload",
                                                         buypage_content())

    @http.route(['/selected_property_page'], type='http', auth="public", website=True)
    def selected_property_page(self, **kwargs):
        selected_property_id = int(kwargs.get('id'))
        return request.env['ir.ui.view']._render_template("property_website.selected_property_onload",
                              self.selected_property_function(selected_property_id))

    # @http.route(['/selected_property'], type='json', auth="public", website=True)
    # def selected_property(self, **kwargs):
    #     selected_property_id = int(kwargs.get('selected_property_id'))
    #     return request.env['ir.ui.view']._render_template("property_website.selected_property",
    #                                                      self.selected_property_function(selected_property_id))

    @http.route(['/rent'], type='http', auth="public", website=True)
    def buy_properties_onloads(self, **kwargs):
        return request.env['ir.ui.view']._render_template("property_website.rent_properties_onload", buypage_content())

    @http.route(['/all_asset_sale_saved'], type='http', auth="public", website=True)
    def allassetlease(self, **post):
        return request.env['ir.ui.view']._render_template("property_website.allassetlease_onload", self.allleasecontent_display(post))

    @http.route(['/all_asset_lease'], type='http', auth="public", website=True)
    def allassetlease_onload(self, **post):
        return request.env['ir.ui.view']._render_template("property_website.allassetlease_onload", self.allleasecontent_display(post))


    @http.route(['/all_asset_lease_golf'], type='http', auth="public", website=True)
    def allassetlease_onload(self, **post):
        print('data')
        print(post.get('id'))
        return request.env['ir.ui.view']._render_template("property_website.allassetlease_onload", self.allleasecontent_display_golf(post))

    # @http.route(['/samana-<string:data-value>'], type='http', auth="public", website=True)
    # def allassetlease_onloadsss(self, **post):
    #     print('MYPage')
    #     return request.env['ir.ui.view']._render_template("property_website.allassetlease_onload", self.allleasecontent_display_golf(post))

    @http.route(['/allassetlease_display'], type='json', auth="public", website=True)
    def allassetlease_display(self, **post):
        return request.env['ir.ui.view']._render_template("property_website.allassetlease_content",
                                                         self.allleasecontent_display_golf(post))

    @http.route(['/allassetlease_display_golf'], type='json', auth="public", website=True)
    def allassetlease_display_golf(self, **post):
        print(post.get('id'))
        print("fhladsjflkajdslk")
        return request.env['ir.ui.view']._render_template("property_website.featured_lease_content",
                                                         self.allleasecontent_display_golf(post))

    # @http.route(['/all_asset_lease_golf'], type='http', auth="public", website=True)
    # def samana_project(self, **kwargs):
    #     print("My Project")
    #     print(int(kwargs.get('id')))
    #
    #     return request.env['ir.ui.view']._render_template("property_website.allassetlease_content",
    #                                                      self.allleasecontent_display_golf(kwargs))

    @http.route(['/selected_property'], type='json', auth="public", website=True)
    def selected_property(self, **kwargs):
        selected_property_id = int(kwargs.get('selected_property_id'))
        return request.env['ir.ui.view']._render_template("property_website.selected_property",
                                                         self.selected_property_function(selected_property_id))

    @http.route(['/sell'], type='http', auth="public", website=True)
    def sell_properties_onload(self, **kwargs):
        return request.render("property_website.sell_properties_onload", salepage_content())

    @http.route(['/sell_properties'], type='json', auth="public", website=True)
    def sell_properties(self, **kwargs):
        return request.env['ir.ui.view']._render_template("property_website.sell_properties",
                                                         salepage_content())

    @http.route(['/all_past_lease'], type='http', auth="public", website=True)
    def allassetpastlease(self, **post):
        return request.render("property_website.allpastlease_onload", self.allpastleasecontent_display(post))

    @http.route(['/allassetpastlease_display'], type='json', auth="public", website=True)
    def allassetpastlease_display(self, **post):
        return request.env['ir.ui.view']._render_template("property_website.allpastlease_content",
                                                         self.allpastleasecontent_display(post))


    @http.route(['/contactus/create_lead'], type='json', auth="public", website=True)
    def crmcontactus(self, **kwargs):
        if kwargs.get('value_from') == 'Contactus page':
            return request.env['crm.lead'].create({
                'name': kwargs.get('name'),
                'phone': kwargs.get('phone'),
                'email_from': kwargs.get('email_from'),
                'contact_name': kwargs.get('contact_name'),
                'description': kwargs.get('description'),
                'partner_name': kwargs.get('partner_name'),
                'user_id': False,
            }).id
        if kwargs.get('value_from') == 'Sales page':
            return request.env['crm.lead'].create({
                'name': 'Request for property sell',
                'contact_name': kwargs.get('contact_name'),
                'phone': kwargs.get('phone'),
                'email_from': kwargs.get('email_from'),
                'street': kwargs.get('address'),
                'city': kwargs.get('city'),
                'zip': kwargs.get('zip'),
                'country_id': kwargs.get('country_id'),
                'user_id': False,
            }).id

        if kwargs.get('value_from') == 'Property page':
            inquiry = ' '
            property = request.env['account.asset.asset'].browse(
                int(kwargs.get('asset')))
            if kwargs.get('asset'):
                val = ''
                if str(property.state) == 'draft':
                    val = 'Available'
                elif str(property.state) == 'normal':
                    val = 'On Lease'
                elif str(property.state) == 'close':
                    val = 'Sale'
                elif str(property.state) == 'sold':
                    val = 'Sold'
                inquiry = 'Inquiry of ' + str(property.name) + ' for ' + val
            return request.env['crm.lead'].create({
                'name': inquiry or ' ',
                'contact_name': kwargs.get('contact_name'),
                'email_from': kwargs.get('email_from'),
                'phone': kwargs.get('phone'),
                'phone_type': kwargs.get('telType'),
                'when_to_call': kwargs.get('telTime'),
                'description': kwargs.get('msg'),
                'property_id': kwargs.get('asset'),
            }).id

    @http.route(['/saved_sell'], type='http', auth="public", website=True)
    def all_asset_sale_saved(self, **post):
        return request.env['ir.ui.view']._render_template("property_website.allsavedsales_onload", self.savedsellcontent_display(post))


    @http.route(['/saved_sell_properties_display'], type='json', auth="public", website=True)
    def saved_sell_properties_display(self, **post):
        return request.env['ir.ui.view']._render_template("property_website.allasset_saved_sale_content",
                                                         self.savedsellcontent_display(post))

    @http.route(['/search_total_fav_property_when_looged_in'], type='json', auth="public", website=True)
    def total_favorite_properties(self, **post):
        return len(get_cookie_list())

    def myproperty_page_content(self, post):
        res_user_browse = request.env['res.users'].browse(request.uid)
        if res_user_browse.tenant_id:
            date_today = datetime.now().date()
            date_today = datetime.strftime(date_today, '%m/%d/%Y')
            tenant_browse = request.env['account.analytic.account'].sudo().search(
                [('tenant_id', '=', res_user_browse.tenant_id.id), ('date_start', '<=', date_today),
                 ('date', '>=', date_today)])
            my_property_list = []
            for one_tenant in tenant_browse:
                my_property_list.append(one_tenant.property_id.id)
            all_property_objs = request.env[
                'account.asset.asset'].sudo().browse(my_property_list)
            if post.get('id'):
                all_payment_schedules = request.env['payment.schedule'].search(
                    [('on_website', '=', True), ('asset_project_id', '=', int(post.get('id')))])
            else:
                all_payment_schedules = request.env['payment.schedule'].search(
                    [('on_website', '=', True)])
            return {
                'all_property_objs': all_property_objs,
                'all_payment_schedules': all_payment_schedules,
                'product_ids_from_cookies_list': get_cookie_list(),
                'facebook_share': request.env['ir.config_parameter'].get_param('property_share_kay_facebook'),
                'twitter_share': request.env['ir.config_parameter'].get_param('property_share_kay_twitter'),
            }
        return False

    @http.route(['/my_properties'], type='http', auth="user", website=True)
    def my_properties_http(self, **post):
        return request.env['ir.ui.view']._render_template("property_website.my_properties_onload",
                                                         self.myproperty_page_content(post))

    @http.route(['/my_properties_json'], type='json', auth="public", website=True)
    def my_properties_json(self, **post):
        return request.env['ir.ui.view']._render_template("property_website.my_properties_content",
                                                         self.myproperty_page_content(post))
    @http.route(['/create_maintanance'], type='json', auth="public", website=True)
    def create_maintanance(self, **post):

        return request.env['maintenance.request'].create({
            'name': post.get('maint_req'),
            'property_id': post.get('property_id'),
            # 'scheduled_date	': post.get('date'),
            'maintenance_team_id': int(post.get('type_id')),
            'description': post.get('description'),
            'renters_fault': post.get('renters_fault'),
            # 'stage_id':int(1),

        })
    @http.route(['/advance_search'], type='json', auth="public", website=True)
    def advance_search(self, **kwargs):
        return request.env['ir.ui.view']._render_template("property_website.advance_search", {})

    # @http.route(['/page/website.contactus', '/page/contactus', '/contactus'], type='http', auth="public", website=True)
    # def contact(self, **kwargs):
    #     return request.render("property_website.contactus_onload", {})

    # @http.route(['/contactus_display'], type='json', auth="public", website=True)
    # def contactus(self, **kwargs):
    #     return request.env['ir.ui.view']._render_template("property_website.contactus_content", {})
