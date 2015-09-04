# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenFire
#
##############################################################################

{
        "name" : "OpenFire / SAV pour Winterhalter",
        "version" : "1.1",
        "author" : "OpenFire",
        "website" : "www.openfire.fr",
        "category" : "OpenFire",
        "description": """
SAV pour Winterhalter
""",
        "depends" : [
            # MG 'of_crm_helpdesk'
            'crm_helpdesk',
        ],
        "demo_xml" : [ ],
        "data" : [
            'security/ir.model.access.csv',
            'of_zz_winterhalter_view.xml',
        ],
        "installable": True,
        'active': False,
}
# vim:expandtab:smartindent:tabstop=4:sorderttabstop=4:shiftwidth=4:
