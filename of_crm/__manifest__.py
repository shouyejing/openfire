# -*- coding: utf-8 -*-

{
    'name' : "OpenFire CRM",
    'version' : "10.0.1.0.0",
    'author' : "OpenFire",
    'website' : "http://openfire.fr",
    'category': 'Customer Relationship Management',
    'description': u"""
Module OpenFire pour le CRM Odoo
================================

 - Ajout du champ site web dans les pistes/opportunités.
 - Recherche du code postal par préfixe.
 - Retrait du filtre de recherche par défaut dans la vue "Mon pipeline".
 - changement méthode de calcul du nombre de ventes client -> ne prend plus en compte que les ventes confirmées (et non les devis)
""",
    'depends' : [
        'crm',
        'sale_crm',
        'of_geolocalize',
    ],
    'data' : [
        'views/of_crm_view.xml',
        'data/data.xml',
    ],
    'installable': True,
}
