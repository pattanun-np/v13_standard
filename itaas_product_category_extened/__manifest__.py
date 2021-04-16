# -*- coding: utf-8 -*-
# Copyright (C) 2016-Today  ITAAS (<http://www.itaas.co.th/>).
#13.0.1.0 - initial compute amount_untaxed
#13.0.1.1 - add function to get income account from sale journal if income account for product or category does not exist
{
    "name": "Itaas Product Category Extened",
    'version': '13.0.1.0',
    "category": 'itaas',
    'summary': 'Itaas Product Category Extened',
    "description": """
        .
    """,
    "sequence": 1,
    "author": "IT as a Service Co., Ltd.",
    "website": "http://www.itaas.co.th/",
    "version": '1.0',
    "depends": ['base','stock','stock_account','account'],
    "data": [
        # 'views/pos_views.xml',
        'views/product_category_view.xml',
    ],
    'qweb': [],
    "installable": True,
    "application": True,
    "auto_install": False,
}
