# -*- coding: utf-8 -*-

{
    'name' : 'OpenFire Payment Bank Deposit',
    'version' : '9.0',
    'summary': 'Allow bank deposit',
    'sequence': 30,
    'description': """
OpenFire Payment Bank Deposit
=============================
    """,
    'category': 'Accounting',
    'depends' : ['account'],
    'data': [
        'views/of_account_payment_bank_deposit_view.xml',
        'security/ir.model.access.csv',
    ],
    'demo': [ ],
    'qweb': [ ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
