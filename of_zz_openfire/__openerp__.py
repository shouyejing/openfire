
{
        "name" : "OpenFire / OpenFire",
        "version" : "1.0",
        "author" : "OpenFire",
        "website" : "www.openfire.fr",
        "category" : "OpenFire",
        "description": """Module specifique de la base OpenFire 
- Affichage de la description des factures dans la vue liste, remplace le champ origine""",
        "depends" : [ "account", "crm"],
        "init_xml" : [ ],
        "demo_xml" : [ ],
        "update_xml" : [ "of_zz_openfire_view.xml" ],
        "installable": True,
        'active': False,
}
