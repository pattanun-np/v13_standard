# -*- coding: utf-8 -*-
# Copyright (C) 2020-today ITAAS

{
    'name' : 'Itaas production stock land cost',
    'version' : '13.0.0.1',
    'price' : 'Free',
    'currency': 'THB',
    'category': 'stock_landed_costs',
    'author' : 'IT as a Service Co., Ltd.',
    'website' : 'www.itaas.co.th',
    'depends' : ['stock_landed_costs'],
    'data' : [
        'views/stock_landed_cost_views.xml',
    ],


    'qweb': [],
    "installable": True,
    "application": True,
    "auto_install": False,
}
