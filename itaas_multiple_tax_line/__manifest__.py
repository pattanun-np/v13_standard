# -*- coding: utf-8 -*-
# Copyright (C) 2020-today ITAAS
# 13.0.1.0 - original
# 13.0.1.1 - change to display partner both type invoice and journal entry
{
    "name": "Itaas Manage Multiple Tax Line in Invoice/Bill",
    "author": "Manage Multiple Tax Line in Invoice/Bill",
    "version": "13.0.1.1",
    "category": "mrp",
    "website": "www.itaas.co.th",
    "depends": ['account'],
    "data": [

        'views/account_move_view.xml',

    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}
