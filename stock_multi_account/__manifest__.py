# -*- coding: utf-8 -*-
# Copyright (C) 2020-today ITAAS (Dev K.Book)
{
    "name": "Stock Multi Account",
    "author": "ITAAS",
    "version": "13.0.0.1",
    "category": "stock",
    "website": "www.itaas.co.th",
    "depends": ['stock_account',],
    "data": [
        'security/ir.model.access.csv',
        'views/product_category_view.xml',
        'views/account_activity_type_view.xml',
        # 'views/stock_view.xml',
        'views/stock_picking_type_view.xml',
        'views/stock_location_view.xml',
        'views/stock_inventory_view.xml',

    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}
