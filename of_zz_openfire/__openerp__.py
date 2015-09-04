
{
        "name" : "OpenFire / OpenFire",
        "version" : "1.0",
        "author" : "OpenFire",
        "website" : "www.openfire.fr",
        "category" : "OpenFire",
        "description": """
Module spécifique de la base OpenFire

- Affichage de la description des factures dans la vue liste et supprime le champ origine
- Ventes/Clients/Pistes : remplacement champ courriel par CP et ville
""",
        "depends" : [ "account", "crm"],
        "init_xml" : [ ],
        "demo_xml" : [ ],
        "data" : [ "of_zz_openfire_view.xml" ],
        "installable": True,
        'active': False,
}
