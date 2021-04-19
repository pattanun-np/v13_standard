# -*- coding: utf-8 -*-
# Copyright (C) 2016-Today  ITAAS (<http://www.itaas.co.th/>).
# fix เรื่อง reverse move ของ V13
{
    "name": "Itaas Cheque Return",
    'version': '13.0.1.1',
    "category": 'itaas',
    'summary': 'Itaas Cheque Return.',
    "description": """
        .
    """,
    "sequence": 1,
    "author": "IT as a Service Co., Ltd.",
    "website": "http://www.itaas.co.th/",
    "version": '1.0',
    "depends": ['base','account','thai_accounting'],
    "data": [
        'views/account_cheque_statment.xml',

    ],
    'qweb': [],
    "installable": True,
    "application": True,
    "auto_install": False,
}
