# -*- coding: utf-8 -*-
# Copyright (C) 2016-Today  ITAAS (<http://www.itaas.co.th/>).
# fix perpetual create account entry one by one
# fix perpetual create account entry all
{
    "name": "Itaas Cheque Return",
    'version': '13.0.1.2',
    "category": 'itaas',
    'summary': 'Itaas Cheque Return.',
    "description": """
        .
    """,
    "sequence": 1,
    "author": "IT as a Service Co., Ltd.",
    "website": "http://www.itaas.co.th/",
    "version": '1.0',
    "depends": ['base','account','stock','stock_account'],
    "data": [
        'views/stock_move_view.xml',

    ],
    'qweb': [],
    "installable": True,
    "application": True,
    "auto_install": False,
}
