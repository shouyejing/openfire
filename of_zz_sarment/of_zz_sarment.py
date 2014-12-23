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

from openerp.osv import fields, osv


class of_archive(osv.Model):
    _name = "of.archive"
    _description = "Archive"
    
    _columns = {
        'partner_id': fields.many2one('res.partner', 'Client'),
        'ftype': fields.selection([('Commande', 'Commande'), ('Facture', 'Facture'), ('Avoir', 'Avoir')], u'Type de pi\u00E8ce jointe', size=64),
        'fdate': fields.date(u'Date de pi\u00E8ce jointe'),
        'fnum': fields.char(u'N° pi\u00E8ce jointe', size=15),
        'pvttc': fields.float('Prix Vente TTC', digits=(16, 2)),
        'pvht': fields.float('Prix Vente HT', digits=(16, 2)),
        'tva': fields.float('TVA', digits=(16, 2)),
        'fname': fields.char(u'Libell\u00E9 du pi\u00E8ce jointe', size=64),
        'file': fields.binary('Fichier'),
        'file_name': fields.char('Nom du Fichier', size=64),
    }
    
    _rec_name = 'partner_id'


# class res_partner(osv.osv):
#     _name = "res.partner"
#     _inherit = "res.partner"
#     
#     _columns = {
#         'arv_ids': fields.one2many('of.archive', 'partner_id', 'Archives'),
#     }
