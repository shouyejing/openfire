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

# Migration from osv import fields, osv
from openerp.osv import fields, osv

class of_paiement_edi(osv.Model):
    """
    On effectue un paiement par échange de fichier informatique
    """
    _name = 'of.paiement.edi'
    _description = "Effectuer un paiement par echange de fichier informatique"
    
    _columns={
        'name':fields.char("Nom", size=64, required=False),
        'type_paiement': fields.char('type de paiement par EDI', size=16, required=True),
        'date_creation': fields.date('Date de création fichier EDI', required=True),
        'date_remise': fields.date('Date de remise fichier EDI', required=False),
        'date_echeance': fields.date('Date d\'échéance paiement EDI', required=False),
        'date_valeur': fields.date('Date de valeur paiement EDI', required=False),
        'fichier_edi': fields.text('Fichier EDI')
    }


class res_company(osv.osv):
    _name = "res.company"
    _inherit = "res.company"
    
    _columns = {
        'of_num_nne': fields.char("Numéro national d'émetteur (NNE)", size=6, required=False, help=u"Numéro national d'émetteur pour opérations bancaires par échange de fichiers informatiques"),
        'of_num_ics': fields.char("Identifiant créancier SEPA (ICS)", size=32, required=False, help=u"Identifiant créancier SEPA (ICS) pour opérations bancaires SEPA par échange de fichiers informatiques"),
    }
    

class res_partner(osv.osv):
    _name = "res.partner"
    _inherit = "res.partner"
    
    _columns = {
        'of_sepa_rum': fields.char("Référence unique du mandat (RUM) SEPA", size=35, required=False, help=u"Référence unique du mandat (RUM) SEPA pour opérations bancaires par échange de fichiers informatiques"),
        'of_sepa_date_mandat': fields.date("Date de signature du mandat SEPA", required=False, help=u"Date de signature du mandat SEPA pour opérations bancaires par échange de fichiers informatiques"),
        'of_sepa_type_prev': fields.selection([("FRST","1er prélèvement récurrent à venir"),("RCUR","Prélèvement récurrent en cours")], 'Type de prélèvement (SEPA)', required=True, help=u"Type de prélèvement SEPA.\n- Mettre à 1er prélèvement quand aucun prélèvement n'a été effectué avec ce mandat.\nLors d'un 1er prélèvement, cette option passera automatiquement à prélèvement récurrent en cours.\n\n- Mettre à prélèvement récurrent en cours lorsqu'un prélèvement a déjà été effectué avec ce mandat.\n\n"),
    }
    _defaults = {
        'of_sepa_type_prev': 'FRST'
    }
    
