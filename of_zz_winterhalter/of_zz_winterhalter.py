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
        'name': fields.char("No de série", size=64, required=False),
        'date_service': fields.date('Date vente', required=False),
        'product_id': fields.many2one('product.product', 'Produit', required=True, ondelete='restrict'),
        'client_id': fields.many2one('res.partner', 'Client', required=True, domain="[('parent_id','=',False)]", ondelete='restrict'),
        'site_adresse_id': fields.many2one('res.partner', 'Site installation', required=False, domain="['|',('parent_id','=',client_id),('id','=',client_id)]", ondelete='restrict'),
        'revendeur_id': fields.many2one('res.partner', 'Revendeur', required=False,  domain="[('of_revendeur','=',True)]", ondelete='restrict'),
        'installateur_id': fields.many2one('res.partner', 'Installateur', required=False, domain="[('of_installateur','=',True)]", ondelete='restrict'),
        'installateur_adresse_id': fields.many2one('res.partner', 'Adresse installateur', required=False, domain="['|',('parent_id','=',installateur_id),('id','=',installateur_id)]", ondelete='restrict'),
        'note': fields.text('Note'),
        'tel_site_id': fields.related('site_adresse_id', 'phone', readonly=True, type='char', string=u'Téléphone site installation'),
        'no_piece': fields.char(u'N° pièce', size=64, required=False),
        'chiffre_aff_ht': fields.float('Chiffre d\'affaire HT', help=u"Chiffre d\'affaire HT"),
        'quantite_vendue': fields.float(u'Quantité vendue', help=u"Quantité vendue"),
        'marge': fields.float(u'Marge', help=u"Marge"),
    }
    
    _sql_constraints = [('no_serie_uniq', 'unique(name)', 'Ce numéro de série est déjà utilisé et doit être unique.')]



class crm_helpdesk(osv.Model):
    _name = "crm.helpdesk"
    _inherit = "crm.helpdesk"

    _columns = {
        'of_produit_installe_id': fields.many2one('of.parc.installe', 'Produit installé', readonly=False),
        'of_type': fields.selection([('contacttel',u'Contact téléphonique'), ('di',u'Demande d\'intervention')], 'Type', required=False, help=u"Type de SAV"),
    }
    
    _defaults = {
        'of_type': 'contacttel',
    }
    
    def ouvrir_demande_intervention(self, cr, uid, context={}):
        # Ouvre une demande d'intervenion depuis un SAV (normalement contact téléphonique) en reprenant les renseignements du SAV en cours.
        # Objectif : permettre de déclencher rapidement une demande d'intervention après un contact téléphonique sans à avoir à resaisir les champs
        
        if not context:
            context = {}
        res = {
            'name': 'Demande intervention',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'crm.helpdesk',
            'type': 'ir.actions.act_window',
            'target': 'current',
        }
        
        # On récupère les données du SAV courant
        if 'active_ids' in context.keys():
            active_ids = isinstance(context['active_ids'], (int,long)) and [context['active_ids']] or context['active_ids']
            if active_ids:
                crm_helpdesk = self.browse(cr, uid, active_ids[0])
                if crm_helpdesk.partner_id:
                    res['context'] = {'default_partner_id': crm_helpdesk.partner_id.id,
                        'default_name': crm_helpdesk.name,
                        'default_of_type': 'di',
                        'default_of_produit_installe_id': crm_helpdesk.of_produit_installe_id.id,
                        'default_email_from': crm_helpdesk.email_from,
                        'default_priority': crm_helpdesk.priority,
                        'default_categ_id': crm_helpdesk.categ_id.id,
                        'default_date_deadline': crm_helpdesk.date_deadline,
                        'default_garantie': crm_helpdesk.garantie,
                        'default_payant_client': crm_helpdesk.payant_client,
                        'default_payant_fournisseur': crm_helpdesk.payant_fournisseur,
                        }
                else:
                    return False
        return res


class res_partner(osv.Model):
    _name = "res.partner"
    _inherit = "res.partner"
    
    _columns = {
        'of_revendeur': fields.boolean('Revendeur', help="Cocher cette case si ce partenaire est un revendeur."),
        'of_installateur': fields.boolean('Installateur', help="Cocher cette case si ce partenaire est un installateur."),
        'of_payeur_id': fields.many2one('res.partner', 'Client payeur', required=False,  domain="[('parent_id','=',False)]", ondelete='restrict'),
        'of_ape': fields.char("Code APE", size=16, required=False),
    }
    
    _sql_constraints = [('ref_uniq', 'unique(ref)', 'Le n° de compte client est déjà utilisé et doit être unique.')]


class product_template(osv.Model):
    _name = "product.template"
    _inherit = "product.template"
    
    _columns = {
        'of_est_dangereux': fields.boolean('Produit dangereux', help="Cocher cette case si ce produit est dangereux."),
        'of_poids_adr': fields.float('Poids ADR', help="Poids ADR"),
    }
    
 
