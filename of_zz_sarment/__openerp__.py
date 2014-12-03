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
        "name" : "OpenFire / Module Le Sarment",
        "version" : "1.1",
        "author" : "OpenFire",
        "website" : "http://www.openfire.fr",
        "category" : "Generic Modules/Others",
        "description": """ Module spécifique pour Le Sarment
Mise en majuscules des noms, prénoms et adresse des prospects.
Mise en minuscules des email des prospects.
Formatage des numéros de téléphone de la forme avec des espaces blancs.
Affichage des auteurs des prospects et des magasins.
Protection contre la modification du type d'une relance appartenant à un autre utilisateur.
Ajouter les archives.
""",
        "depends" : [ ],
        "init_xml" : [ ],
        "demo_xml" : [ ],
        "update_xml" : [
#            'security/ir.model.access.csv',
            'of_zz_sarment_view.xml'
        ],
        "installable": True,
        'active': False,
}


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: