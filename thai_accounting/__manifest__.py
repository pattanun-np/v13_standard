# -*- coding: utf-8 -*-
# Copyright (C) 2016-Today  ITAAS (<http://www.itaas.co.th/>).
# 13.0.1.4 - fix register invoice and cn with deduction
{
    "name": "Thailand Accounting Enhancement for Odoo Enterprise",
    "category": 'Accounting',
    'summary': 'Thailand Accounting Enhancement.',
    "description": """
        .
    """,
    "sequence": 1,
    "author": "IT as a Service Co., Ltd.",
    "website": "http://www.itaas.co.th/",
    "version": '13.0.1.3',
    "depends": ['account','account_payment','account_asset','account_accountant'],
    "external_dependencies" : {
        'python' : ['bahttext',
                    'num2words',
                    'xlrd'],
    },
    "data": [
        'sequence.xml',
        'views/res_company_view.xml',
        'views/res_partner_view.xml',
        #########################Next View###################
        'views/account_account_view.xml',
        'views/account_journal_view.xml',
        'views/account_tax_view.xml',
        'views/account_move_view.xml',
        'views/account_payment_view.xml',
        'views/customer_billing_view.xml',
        'views/account_cheque_statement_view.xml',

        #wizard or multiple action
        'wizard/check_multiple_confirm_views.xml',

        # data fro preload ###
        'data/account_wht_data.xml',
        # security access and rule
        'security/ir.model.access.csv',


    ],
    'qweb': [],
    "installable": True,
    "application": True,
    "auto_install": False,
}
