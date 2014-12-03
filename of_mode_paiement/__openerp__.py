# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenFire
#
##############################################################################

{
        "name" : "OpenFire / Modes de paiement",
        "version" : "1.1",
        "author" : "OpenFire",
        "website" : "www.openfire.fr",
        "category" : "Generic Modules/Sales & Purchases",
        "description": """ OpenFire Module d'extension des modes de paiement aux paiements client ou fournisseur """,
        "depends" : [ 'account_payment'],
        "init_xml" : [
            'of_init.xml',
        ],
        "demo_xml" : [ ],
        "update_xml" : [
            'of_mode_paiement_view.xml',
        ],
        "installable": True,
        'active': False,
}
# vim:expandtab:smartindent:tabstop=4:sorderttabstop=4:shiftwidth=4:
