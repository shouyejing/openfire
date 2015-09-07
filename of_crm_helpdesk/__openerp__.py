# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>). All Rights Reserved
#    $Id$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

{
    "name" : "OpenFire / SAV",
    "version" : "1.0",
    "author" : "OpenFire",
    "website" : "http://www.openfire.co",
    "category" : "Generic Modules/Sales & Purchases",
    "description": """ Modification OpenFire sur le module OpenERP CRM_HelpDesk 
     - Ajout du rapport SAV
     - Ajout des notes client
     - Suppression des secondes dans la date SAV
     - Ajout de l'affichage de la liste des documents (devis/commande client, devis/commande fournisseur, facture client) du client
     - Ajout du code SAV avec séquence associée
     - Ajout du magasin 
     - Ajout de la hiérarchie pour la catégorie du SAV
     - Possibilité de générer un devis ou une demande de prix depuis le SAV (menu droit).
     - Affichage des emails envoyés aux fournisseurs depuis le SAV
    """,
    "depends" : ['crm_helpdesk'], # Migration , 'of_appro', 'of_planning'],

    "init_xml" : [ 
        'of_crm_helpdesk_sequence.xml',
        #'of_init.xml',
    ],
    "demo_xml" : [ ],
    'css' : [
        "static/src/css/of_crm_helpdesk.css",
    ],
    "data" : [
        # MG 'security/ir.model.access.csv',
        'of_crm_helpdesk.xml',
    ],
    "installable": True,
    'active': False,
}
