# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
from datetime import datetime
from odoo.addons import decimal_precision as dp
from odoo.tools.translate import _
import time
from lxml import etree
from odoo.exceptions import UserError, ValidationError
from odoo import http


