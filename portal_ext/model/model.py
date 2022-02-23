# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import AccessError, UserError
from odoo.tools import float_compare
import time
from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
