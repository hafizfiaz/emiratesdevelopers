# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2018-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Muhammed Nishad T K
#
#    This program is free software: you can modify
#    it under the terms of the GNU LGPL-3 as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the LGPL-3
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
##############################################################################
{
    'name': 'SD QR Code Generator',
    'version': '12.0.1.0.0',
    'summary': 'Generate Unique QR Codes for Customers and Products',
    'category': 'Extra Tools',
    'author': 'Muhammad Rashid Mukhtar',
    'maintainer': 'Samana Group',
    'company': 'Samana Group ',
    'website': 'https://www.cybrosys.com',
    'depends': ['base', 'sd_receipts_report'],
    'data': [
        # 'report/paperformat.xml',
        # 'report/report.xml',
        'views/view.xml',
        'views/web_view.xml',
        'report/template.xml',
    ],
    'images': ['static/description/banner.jpg'],
    'installable': True,
    'application': False,
    'auto_install': False,
    # 'license': 'LGPL-3',
    # 'post_init_hook': '_set_qr'
}
