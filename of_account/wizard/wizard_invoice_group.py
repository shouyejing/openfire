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

from openerp.osv import osv
#import netsvc
from openerp import workflow
# import pooler
from openerp import pooler


class of_invoice_group(osv.osv_memory):
    """
    Ce wizard va fusionner les factures fournisseurs brouillons
    """

    _name = "of.invoice.group"
    _description = "Fusionner les factures fournisseurs brouillons"

    def merge_invoices(self, cr, uid, ids, context=None):
        invoice_obj = self.pool.get('account.invoice')

        mod_obj = self.pool.get('ir.model.data')
        if context is None:
            context = {}
        result = mod_obj._get_id(cr, uid, 'account', 'view_account_invoice_filter')
        id = mod_obj.read(cr, uid, result, ['res_id'])
        allinvoices = invoice_obj.do_merge(cr, uid, context.get('active_ids', []), context)

        # si le module purchase est installe, on mise a jour aussi la table purchase_invoice_rel
        cr.execute("SELECT true FROM pg_tables WHERE tablename = 'purchase_invoice_rel'")
        purchase_exist = cr.fetchone()[0]
        if purchase_exist:

            for new_invoice in allinvoices:
                try:
                    cr.execute('UPDATE purchase_invoice_rel SET invoice_id=%s WHERE invoice_id in %s', (new_invoice, tuple(allinvoices[new_invoice])))
                except:
                    pass

        type = 'in_invoice'
        if len(allinvoices.keys()) != 0:
            inv_id = allinvoices.keys()[0]
            type = invoice_obj.browse(cr, uid, inv_id).type
        context.update({'type': type})
        return {
            'domain': "[('id','in', [" + ','.join(map(str, allinvoices.keys())) + "])]",
            'name': 'Factures Fournisseurs',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'account.invoice',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'search_view_id': id['res_id'],
            'context': context,
        }

of_invoice_group()
