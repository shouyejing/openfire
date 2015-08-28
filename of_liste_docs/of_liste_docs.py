# -*- coding: utf-8 -*-
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

from openerp.osv import fields, osv
import time


class of_liste_docs(osv.Model):
    _name = "of.liste.docs"
    _description = "Liste documents"
    
    _columns = {
        'name': fields.char(u'Nom', size=64),
        'date': fields.date(u'Date document'),
        'categorie': fields.many2one('of.liste.docs.categorie', u'Catégorie', required=False, ondelete='restrict'),
        'file': fields.binary(u'Fichier'),
        'file_name': fields.char(u'Nom du fichier', size=64),
    }
    
    _rec_name = 'name'
    
    _defaults = {
        'date': time.strftime('%Y-%m-%d'),
    }


class of_liste_docs_categorie(osv.Model):
    _name = "of.liste.docs.categorie"
    
    _columns = {
        'name': fields.char(u'Catégorie', size=32),
    }
