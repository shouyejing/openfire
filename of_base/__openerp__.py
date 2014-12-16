# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

{
    "name" : "OpenFire Base",
    "version" : "1.1",
    "author" : "OpenFire",
    'complexity': "easy",
    "description" : """
Personnalisations des fonctions de base OpenERP
- Retrait du recalcul automatique du pied de page de la société à la modification d'un des champs d'adresse.
- Modification du pied de page des comptes bancaires calculé automatiquement en pied de page secondaire à saisir.
- Autorisation de générer les boutons d'action d'envoi d'emails depuis les modèles d'emails pour les administrateurs.
- Ajout des colonnes destinataire et partenaire dans la vue liste des emails.
    """
,
    "website" : "www.openfire.fr",
    "depends" : ["base","mail"],
    "category" : "OpenFire",
    "sequence": 100,
    "init_xml" : [
        'of_base_init.yml',
    ],
    "update_xml" : [
        'of_base_view.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
