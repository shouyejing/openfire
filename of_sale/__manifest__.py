# -*- coding: utf-8 -*-

{
    "name": "OpenFire Sale",
    "version": "10.0.1.0.0",
    "author": "OpenFire",
    'license': 'AGPL-3',
    "description": """
Personnalisation des ventes OpenFire
====================================

Modification de l'affichage du formulaire de devis/commande client.

Ajout d'un filtre de recherche pour les commandes à facturer entièrement.
""",
    "website": "www.openfire.fr",
    "depends": ["sale"],
    "category": "OpenFire",
    "data": [
        'views/of_sale_view.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
