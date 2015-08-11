# -*- coding: utf-8 -*-
##############################################################################
#
#   OpenERP, Open Source Management Solution
#   Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>). All Rights Reserved
#   $Id$
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp.osv import fields, osv
#from openerp import netsvc
import time


class of_parc_installe(osv.Model):
    """
    Parc installée
    """
    _name = 'of.parc.installe'
    _description = "Parc installé"
    
    _columns={
        'name': fields.char("No de série", size=64, required=True),
        'date_service': fields.date('Date de mise en service', required=False),
        'product_id': fields.many2one('product.product', 'Produit', required=True, ondelete='restrict'),
        'client_id': fields.many2one('res.partner', 'Client', required=True,  domain="[('parent_id','=',False)]", ondelete='restrict'),
        'site_adresse_id': fields.many2one('res.partner', 'Site installation', required=False, domain="['|',('parent_id','=',client_id),('id','=',client_id)]", ondelete='restrict'),
        'revendeur_id': fields.many2one('res.partner', 'Revendeur', required=False,  domain="[('of_revendeur','=',True)]", ondelete='restrict'),
        'installateur_id': fields.many2one('res.partner', 'Installateur', required=False, domain="[('of_installateur','=',True)]", ondelete='restrict'),
        'installateur_adresse_id': fields.many2one('res.partner', 'Adresse installateur', required=False, domain="['|',('parent_id','=',installateur_id),('id','=',installateur_id)]", ondelete='restrict'),
        'note': fields.text('Note'),
        'tel_site_id': fields.related('site_adresse_id', 'phone', readonly=True, type='char', string=u'Téléphone site installation')
    }
    
    _sql_constraints = [('no_serie_uniq', 'unique(name)', 'Ce numéro de série est déjà utilisé et doit être unique.')]



class crm_helpdesk(osv.Model):
    _name = "crm.helpdesk"
    _inherit = "crm.helpdesk"

    _columns = {
        'produit_installe_id': fields.many2one('of.parc.installe', 'Produit installé', readonly=False),
    }


class res_partner(osv.Model):
    _name = "res.partner"
    _inherit = "res.partner"
    
    _columns = {
        'of_revendeur': fields.boolean('Revendeur', help="Cocher cette case si ce partenaire est un revendeur."),
        'of_installateur': fields.boolean('Installateur', help="Cocher cette case si ce partenaire est un installateur."),
    }
