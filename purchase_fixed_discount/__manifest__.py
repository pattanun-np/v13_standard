# Copyright 2017-18 Eficent Business and IT Consulting Services S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    "name": "Purchase Fixed Discount",
    "summary": "Allows to apply fixed amount discounts in purchases orders.",
    "version": "13.0.1.0.0",
    "category": "Sales",
    "website": "https://github.com/OCA/sale-workflow",
    "author": "Eficent, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "depends": [
        "purchase", "account_invoice_fixed_discount","purchase_discount",
    ],
    "data": [
        "views/purchase_order_views.xml",
    ],
}
