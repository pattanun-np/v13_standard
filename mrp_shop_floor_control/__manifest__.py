# -*- coding: utf-8 -*-
# Copyright (c) Open Value All Rights Reserved

{
    'name': 'MRP Shop Floor Control',
    'summary': 'MRP Shop Floor Control',
    'version': '13.0.3.3.0',
    'category': 'Manufacturing',
    'website': 'linkedin.com/in/openvalue-consulting-472448176',
    'author': "Open Value",
    'support': 'opentechvalue@gmail.com',
    'license': "Other proprietary",
    'price': 450.00,
    'currency': 'EUR',
    'depends': [
            'mrp',
            'mrp_workcenter_capacity'
    ],
    'demo': [],
    'data': [
        'security/ir.model.access.csv',
        'views/mrp_workcenter_views.xml',
        'views/mrp_routing_views.xml',
        'views/mrp_workorder_views.xml',
        'views/mrp_workcenter_capacity_views.xml',
        'wizards/mrp_confirmation_views.xml',
        'views/mrp_production_views.xml',
        'views/mrp_workcenter_productivity_views.xml',
    ],
    'application': False,
    'installable': True,
    'auto_install': False,
    'images': ['static/description/banner.png'],
}
