# -*- coding: utf-8 -*-
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
        "description": """
        - Extension des modes de paiement aux paiements client ou fournisseur
        - Ajout règlement factures par LCR et prélèvement SEPA par échange de données informatisées (EDI)""",
        "depends" : [ 'account_payment'],
        "init_xml" : [
            'of_init.xml',
        ],
        "demo_xml" : [ ],
        "update_xml" : [
            'security/ir.model.access.csv',
            'of_mode_paiement_view.xml',
            'of_mode_paiement_edi_view.xml',
            'wizard/wizard_edi_view.xml',
        ],
        "installable": True,
        'active': False,
}
# vim:expandtab:smartindent:tabstop=4:sorderttabstop=4:shiftwidth=4:
