from operator import itemgetter
from lxml import etree
from openerp.osv.orm import browse_record, browse_null
from openerp.osv import fields, osv, orm
from openerp.tools.translate import _
from openerp import workflow

class users(osv.Model):
    _name = "res.users"
    _inherit = 'res.users'
    _columns = {
        'seller_code': fields.char('Code vendeur', size=64),
    }

    def get_fiscalyear_search_context(self, cr, uid):
        company_id = self.read(cr, uid, uid, ['company_id'])['company_id'][0]

        fiscalyear_obj = self.pool.get('account.fiscalyear')

        fiscalyear_ids = fiscalyear_obj.search(cr, uid, [('company_id', '=', company_id), ('state', '=', 'draft')])
        if not fiscalyear_ids:
            return {}

        fiscalyear = fiscalyear_obj.read(cr, uid, fiscalyear_ids[0], ['date_start', 'date_stop'])
        return {'search_default_date_from': fiscalyear['date_start'],
                'search_default_date_to'  : fiscalyear['date_stop']}


# ajouter recherche de date a date pour la facture
class account_invoice(osv.Model):
    _name = "account.invoice"
    _inherit = "account.invoice"

    _columns = {
        'date_invoice_from':fields.function(lambda *a, **k:{}, method=True, type='date', string=u"Date d\u00E9but"),
        'date_invoice_to':fields.function(lambda *a, **k:{}, method=True, type='date', string="Date fin"),
    }

    def do_merge(self, cr, uid, ids, context=None):
        """
        To merge similar type of account invoices.
        Invoices will only be merged if:
        * Account Invoices are in draft
        * Account Invoices belong to the same partner
        * Account Invoices are have same journal, adresse facture, position fiscale, compte, type reference, devise
        Lines will only be merged if:
        * Invoice lines are exactly the same except for the quantity and unit

         @param self: The object pointer.
         @param cr: A database cursor
         @param uid: ID of the user currently logged in
         @param ids: the ID or list of IDs
         @param context: A standard dictionary

         @return: new invoice order id
        """
        #TOFIX: merged invoice line should be unlink
        def make_key(br, fields):
            list_key = []
            for field in fields:
                field_val = getattr(br, field)
                if field in ('journal_id', 'partner_id', 'address_invoice_id', 'fiscal_position', 'account_id', 'reference_type', 'currency_id'):
                    if not field_val:
                        field_val = False
                if isinstance(field_val, browse_record):
                    field_val = field_val.id
                elif isinstance(field_val, browse_null):
                    field_val = False
                elif isinstance(field_val, list):
                    field_val = ((6, 0, tuple([v.id for v in field_val])),)
                list_key.append((field, field_val))
            list_key.sort()
            return tuple(list_key)

    # compute what the new invoices should contain

        new_invoices = {}

        for pinvoice in [invoice for invoice in self.browse(cr, uid, ids, context=context) if (invoice.state == 'draft') and (invoice.type == 'in_invoice')]:
            invoice_key = make_key(pinvoice, ('journal_id', 'partner_id', 'address_invoice_id', 'fiscal_position', 'account_id', 'reference_type', \
                                              'currency_id'))
            new_invoice = new_invoices.setdefault(invoice_key, ({}, []))
            new_invoice[1].append(pinvoice.id)
            invoice_infos = new_invoice[0]
            if not invoice_infos:
                invoice_infos.update({
                    'journal_id': pinvoice.journal_id.id,
                    'origin': pinvoice.origin or '',
                    'partner_id': pinvoice.partner_id.id,
                    'address_invoice_id': pinvoice.address_invoice_id.id,
                    'fiscal_position': pinvoice.fiscal_position.id,
                    'date_invoice': pinvoice.date_invoice or False,
                    'account_id': pinvoice.account_id.id,
                    'reference_type': pinvoice.reference_type,
                    'reference': pinvoice.reference or '',
                    'invoice_line': {},
                    'user_id': pinvoice.user_id and pinvoice.user_id.id or False,
                    'partner_bank_id': pinvoice.partner_bank_id and pinvoice.partner_bank_id.id or False,
                    'name': pinvoice.name or '',
                    'address_contact_id': pinvoice.address_contact_id and pinvoice.address_invoice_id.id or False,
                    'comment': pinvoice.comment or '',
                    'currency_id': pinvoice.currency_id.id,
                    'payment_term': pinvoice.payment_term and pinvoice.payment_term.id or False,
                    'state': 'draft',
                    'type': 'in_invoice',
                })
            else:
                if pinvoice.origin:
                    invoice_infos['origin'] = (invoice_infos['origin'] and (invoice_infos['origin'] + ' ') or '') + pinvoice.origin
                if pinvoice.date_invoice:
                    if invoice_infos['date_invoice']:
                        if pinvoice.date_invoice < invoice_infos['date_invoice']:
                            invoice_infos['date_invoice'] = pinvoice.date_invoice
                    else:
                        invoice_infos['date_invoice'] = pinvoice.date_invoice
                if pinvoice.reference:
                    invoice_infos['reference'] = (invoice_infos['reference'] and (invoice_infos['reference'] + ' ') or '') + pinvoice.reference
                if pinvoice.user_id:
                    if not invoice_infos['user_id']:
                        invoice_infos['user_id'] = pinvoice.user_id.id
                if pinvoice.partner_bank_id and invoice_infos['partner_bank_id']:
                    if pinvoice.partner_bank_id.id != invoice_infos['partner_bank_id']:
                        invoice_infos['partner_bank_id'] = False
                else:
                    if invoice_infos['partner_bank_id']:
                        invoice_infos['partner_bank_id'] = False
                if pinvoice.name:
                    invoice_infos['name'] = (invoice_infos['name'] and (invoice_infos['name'] + ' ') or '') + pinvoice.name
                if pinvoice.address_contact_id and invoice_infos['address_contact_id']:
                    if pinvoice.address_contact_id.id != invoice_infos['address_contact_id']:
                        invoice_infos['address_contact_id'] = False
                else:
                    if invoice_infos['address_contact_id']:
                        invoice_infos['address_contact_id'] = False
                if pinvoice.comment:
                    invoice_infos['comment'] = (invoice_infos['comment'] and (invoice_infos['comment'] + '\n') or '') + pinvoice.comment
                if pinvoice.payment_term and invoice_infos['payment_term']:
                    if pinvoice.payment_term.id != invoice_infos['payment_term']:
                        invoice_infos['payment_term'] = False
                else:
                    if invoice_infos['payment_term']:
                        invoice_infos['payment_term'] = False


            for invoice_line in pinvoice.invoice_line:
                line_key = make_key(invoice_line, ('id', 'product_id', 'name', 'price_unit', 'price_unit_ttc', 'discount', 'invoice_line_tax_id', 'account_id'))
                i_line = invoice_infos['invoice_line'].setdefault(line_key, {})
                
                # append a new "standalone" line
                for field in ('quantity', 'uos_id', 'note', 'sale_order_ids'):
                    field_val = getattr(invoice_line, field)
                    if isinstance(field_val, browse_record):
                        field_val = field_val.id
                    elif isinstance(field_val, list):
                        field_val = ((6, 0, tuple([v.id for v in field_val])),)
                    i_line[field] = field_val

                i_line['uos_factor'] = invoice_line.uos_id and invoice_line.uos_id.factor or 1.0

        allinvoices = []
        invoices_info = {}
        for invoice_key, (invoice_data, old_ids) in new_invoices.iteritems():
            # skip merges with only one invoice
            if len(old_ids) < 2:
                allinvoices += (old_ids or [])
                continue

            # cleanup invoice line data
            for key, value in invoice_data['invoice_line'].iteritems():
                del value['uos_factor']
                value.update(dict(key))
                if 'id' in value.keys():
                    del value['id']
            invoice_data['invoice_line'] = [(0, 0, value) for value in invoice_data['invoice_line'].itervalues()]

            # create the new invoice
            newinvoice_id = self.create(cr, uid, invoice_data)
            invoices_info.update({newinvoice_id: old_ids})
            allinvoices.append(newinvoice_id)

            # make triggers pointing to the old invoices point to the new invoice
            for old_id in old_ids:
                workflow.trg_redirect(uid, 'account.invoice', old_id, newinvoice_id, cr)
                workflow.trg_validate(uid, 'account.invoice', old_id, 'invoice_cancel', cr)
        return invoices_info


class account_move(osv.Model):
    _name = "account.move"
    _inherit = "account.move"

    def _get_default_line_name(self, cr, uid, ids, *args):
        result = {}
        for move in self.browse(cr, uid, ids):
            result[move.id] = move.line_id and move.line_id[0].name or ""
        return result

    _columns = {
        'default_line_name' : fields.function(_get_default_line_name, method=True, type='char', size=64),
    }

    def onchange_date(self, cr, uid, ids, date):
        cr.execute("SELECT id FROM account_period WHERE date_start<=%s AND date_stop>=%s", (date, date))
        period_id = cr.fetchone()
        if period_id:
            return {'value':{'period_id':period_id[0]}}
        raise osv.except_osv(_('Error !'), _('No period defined for this date: %s !\nPlease create one.') % date)

    def onchange_line_id(self, cr, uid, ids, line_ids, context=None):
        res = super(account_move, self).onchange_line_id(cr, uid, ids, line_ids, context=context)
        for line_id in line_ids:
            if line_id[0] in (0, 1, 4):
                default_line_name = ""
                if line_id[0] == 0:
                    default_line_name = line_id[2].get('name', '')
                elif line_id[0] == 1 and 'name' in line_id[2]:
                    default_line_name = line_id[2]['name']
                else:
                    default_line_name = self.pool.get('account.move.line').read(cr, uid, line_id[1], ['name'])['name']
                res['value']['default_line_name'] = default_line_name
                break
        return res

    def _centralise(self, cr, uid, move, mode, context=None):
        assert mode in ('debit', 'credit'), 'Invalid Mode' #to prevent sql injection
        currency_obj = self.pool.get('res.currency')
        if context is None:
            context = {}

        if mode=='credit':
            account_id = move.journal_id.default_debit_account_id.id
            mode2 = 'debit'
            if not account_id:
                raise osv.except_osv(_('UserError'),
                        _('There is no default default debit account defined \n' \
                                'on journal "%s"') % move.journal_id.name)
        else:
            account_id = move.journal_id.default_credit_account_id.id
            mode2 = 'credit'
            if not account_id:
                raise osv.except_osv(_('UserError'),
                        _('There is no default default credit account defined \n' \
                                'on journal "%s"') % move.journal_id.name)

        # find the first line of this move with the current mode
        # or create it if it doesn't exist
        cr.execute('select id from account_move_line where move_id=%s and centralisation=%s limit 1', (move.id, mode))
        res = cr.fetchone()
        line_id = res and res[0] or 0

        # find the first line of this move with the other mode
        # so that we can exclude it from our calculation
        cr.execute('select id from account_move_line where move_id=%s and centralisation=%s limit 1', (move.id, mode2))
        res = cr.fetchone()
        line_id2 = res and res[0] or 0

        if context.get('fiscalyear_close'):
            cr.execute('SELECT SUM(%s-%s) FROM account_move_line WHERE move_id=%%s AND id NOT IN %%s' % (mode,mode2), (move.id, (line_id,line_id2)))
            result = max(cr.fetchone()[0] or 0.0, 0.0)
        else:
            cr.execute('SELECT SUM(%s) FROM account_move_line WHERE move_id=%%s AND id!=%%s' % (mode,), (move.id, line_id2))
            result = cr.fetchone()[0] or 0.0

        if line_id==0:
            if result==0.0:
                return True
            context.update({'journal_id': move.journal_id.id, 'period_id': move.period_id.id})
            line_id = self.pool.get('account.move.line').create(cr, uid, {
                'name': _(mode.capitalize()+' Centralisation'),
                'centralisation': mode,
                'account_id': account_id,
                'move_id': move.id,
                'journal_id': move.journal_id.id,
                'period_id': move.period_id.id,
                'date': move.period_id.date_stop,
                'debit': 0.0,
                'credit': 0.0,
            }, context)


        cr.execute('update account_move_line set '+mode2+'=%s where id=%s', (result, line_id))

        #adjust also the amount in currency if needed
        cr.execute("select currency_id, sum(amount_currency) as amount_currency from account_move_line where move_id = %s and currency_id is not null group by currency_id", (move.id,))
        for row in cr.dictfetchall():
            currency_id = currency_obj.browse(cr, uid, row['currency_id'], context=context)
            if not currency_obj.is_zero(cr, uid, currency_id, row['amount_currency']):
                amount_currency = row['amount_currency'] * -1
                account_id = amount_currency > 0 and move.journal_id.default_debit_account_id.id or move.journal_id.default_credit_account_id.id
                cr.execute('select id from account_move_line where move_id=%s and centralisation=\'currency\' and currency_id = %slimit 1', (move.id, row['currency_id']))
                res = cr.fetchone()
                if res:
                    cr.execute('update account_move_line set amount_currency=%s , account_id=%s where id=%s', (amount_currency, account_id, res[0]))
                else:
                    context.update({'journal_id': move.journal_id.id, 'period_id': move.period_id.id})
                    line_id = self.pool.get('account.move.line').create(cr, uid, {
                        'name': _('Currency Adjustment'),
                        'centralisation': 'currency',
                        'account_id': account_id,
                        'move_id': move.id,
                        'journal_id': move.journal_id.id,
                        'period_id': move.period_id.id,
                        'date': move.period_id.date_stop,
                        'debit': 0.0,
                        'credit': 0.0,
                        'currency_id': row['currency_id'],
                        'amount_currency': amount_currency,
                    }, context)

        return True
account_move()

class account_move_line(osv.Model):
    _name = "account.move.line"
    _inherit = "account.move.line"

    def _get_solde(self, cr, uid, ids, *args):
        result = {}
        for line in self.read(cr, uid, ids, ['credit', 'debit']):
            result[line['id']] = line['credit'] - line['debit']
        return result

    _columns = {
        'amount_min':fields.function(lambda *a, **k:{}, method=True, string=u"Montant min"),
        'amount_max':fields.function(lambda *a, **k:{}, method=True, string="Montant max"),
        'date_from' :fields.function(lambda *a, **k:{}, method=True, type='date', string=u"Date d\u00E9but"),
        'date_to'   :fields.function(lambda *a, **k:{}, method=True, type='date', string="Date fin"),
        'solde'     :fields.function(_get_solde, method=True, string="Solde"),
    }

    def create(self, cr, uid, vals, context=None, check=True):
        if not context:
            context = {}
        if 'move_line_name' in context:
            vals['name'] = context['move_line_name']
        else:
            context = context.copy()
            context['move_line_name'] = vals['name']
        result = super(account_move_line, self).create(cr, uid, vals, context=context, check=check)
        return result

    def _remove_move_reconcile(self, cr, uid, move_ids=[], context=None):
        # Function remove move rencocile ids related with moves
        obj_move_line = self.pool.get('account.move.line')
        obj_move_rec = self.pool.get('account.move.reconcile')
        unlink_ids = []
        if not move_ids:
            return True
        recs = obj_move_line.read(cr, uid, move_ids, ['reconcile_id', 'reconcile_partial_id'])

        recs = {rec['id']:rec['reconcile_id'] or rec['reconcile_partial_id'] for rec in recs}
        recs = {key:value[0] for key,value in recs.iteritems() if value}
        if recs:
            rec_ids = list(set(recs.values()))

            lines = obj_move_rec.read(cr, uid, rec_ids, ['line_id', 'line_partial_ids'])
            lines = {line['id']:line['line_id'] or line['line_partial_ids'] for line in lines}

            for move_id,rec_id in recs.iteritems():
                lines[rec_id].remove(move_id)

            unlink_ids = []
            for rec_id,line_ids in lines.iteritems():
                if len(line_ids)<2:
                    unlink_ids.append(rec_id)
                else:
                    obj_move_rec.write(cr, uid, rec_id, {'line_id':[(5,False)], 'line_partial_ids':[(6,False,line_ids)]})

            if unlink_ids:
                obj_move_rec.unlink(cr, uid, unlink_ids)
        return True

class account_bank_statement(osv.Model):
    _name = "account.bank.statement"
    _inherit = "account.bank.statement"

    def _get_default_line_name(self, cr, uid, ids, *args):
        result = {}
        for statement in self.browse(cr, uid, ids):
            result[statement.id] = statement.line_ids and statement.line_ids[0].name or ""
        return result

    def _end_diff_balance(self, cr, uid, ids, *args):
        result = {}
        for statement in self.browse(cr, uid, ids):
            result[statement.id] = statement.balance_end_real - statement.balance_end
        return result

    _columns = {
        'default_line_name' : fields.function(_get_default_line_name, method=True, type='char', size=64),
        'balance_end_diff': fields.function(_end_diff_balance, string="Ecart de solde", help=u'Diff\u00E9rence entre le solde final et le solde calcul\u00E9'),
    }

    def onchange_line_ids(self, cr, uid, ids, line_ids, context=None):
        for line_id in line_ids:
            if line_id[0] in (0, 1, 4):
                default_line_name = ""
                if line_id[0] == 0:
                    default_line_name = line_id[2].get('name', '')
                elif line_id[0] == 1 and 'name' in line_id[2]:
                    default_line_name = line_id[2]['name']
                else:
                    default_line_name = self.pool.get('account.bank.statement.line').read(cr, uid, line_id[1], ['name'])['name']
                break
        else:
            return {}
        return {'value':{'default_line_name':default_line_name}}

class account_bank_statement_line(osv.Model):
    _name = "account.bank.statement.line"
    _inherit = "account.bank.statement.line"

    _defaults = {
        'date': None,
    }

    def onchange_date(self, cr, uid, ids, date, period_id, context=None):
        """
        Fonction qui ajuste le mois et l'annee de date pour que le jour corresponde a la periode.
        Le but est de pouvoir ne saisir que le jour dans le champ date
        La date en arrivee est de type YYYY-mm-dd (modification) ou YYYY-mm-dd HH:MM:SS (initialisation de nouvelle ligne)
        """
        if not date:
            return
        period = self.pool.get('account.period').read(cr, uid, period_id, ['date_start', 'date_stop'])

        if date < period['date_start'] or date > period['date_stop']:
            date_d = date[8:10]
            date_d = date.split('-')[2]
            if len(date_d) > 2:
                date_d = date_d.split(' ')[0]
            start_y, start_m, start_d = period['date_start'].split('-')

            int_date_d = int(date_d)
            if int_date_d < int(start_d):
                int_start_m = int(start_m) + 1
                if int_start_m == 13:
                    int_start_m = 1
                    start_y = str(int(start_y) + 1)
                start_m = int_start_m < 10 and "0" or ""
                start_m += str(start_m)
            return {'value':{'date':start_y + "-" + start_m + "-" + date_d}}
        else:
            return {}

class account_voucher(osv.Model):
    _name = 'account.voucher'
    _inherit = 'account.voucher'
    
    def _get_period(self, cr, uid, context=None):
        if context is None: context = {}
        if context.get('period_id', False):
            return context.get('period_id')
        periods = self.pool.get('account.period').find(cr, uid, context={'account_period_prefer_normal': True})
        return periods and periods[0] or False
    
    _columns = {
        'period_id': fields.many2one('account.period', 'Period', required=True, readonly=True, states={'draft':[('readonly',False)]}),
    }
    
    _defaults = {
        'period_id': _get_period,
    }
    
    def proforma_voucher(self, cr, uid, ids, context=None):
        super(account_voucher, self).proforma_voucher(cr, uid, ids, context)
        
        # comptabiliser la piece comptable liee avec ce paiement
        for payment in self.browse(cr, uid, ids):
            if payment.move_id:
                payment.move_id.button_validate(context=context)
        return True
account_voucher()


class account_account_type(osv.Model):
    _name = "account.account.type"
    _inherit = "account.account.type"
    
    _columns = {
        'of_type_ids': fields.one2many('of.account.type', 'account_user_type', u'Pr\u00E9fixes comptes'),
        'name': fields.char('Account Type', size=64, required=True, translate=False),
    }
    


class of_account_type(osv.Model):
    _name = "of.account.type"
    _description = u"Pr\u00E9fixes comptes"
    
    def _get_length_prefixe(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        for account_type in self.browse(cr, uid, ids, context=context):
            res[account_type.id] = len(account_type.prefixe_compte)
        return res
    
    _columns = {
        'prefixe_compte': fields.char(u'Pr\u00E9fixe Compte', required=True, size=32),
        'account_user_type': fields.many2one('account.account.type', 'Type de compte', required=True, ondelete='cascade'),
        'account_type': fields.selection([
            ('other', 'Normal'),
            ('receivable', 'Compte client'),
            ('payable', 'Fournisseur'),
            ('liquidity',u'Liquidit\u00E9s'),
            ('consolidation', 'Consolidation'),
            ('closed', u'Cl\u00F4tur\u00E9'),
        ], 'Type interne', required=True),
        'len_prefixe': fields.function(_get_length_prefixe, string=u'Pr\u00E9fixe longeur',
          store={
            'of.account.type': (lambda self, cr, uid, ids, c={}: ids, ['prefixe_compte'], 10),
          }),
    }
    
    _order = "len_prefixe"
    
    _sql_constraints = [
        ('prefixe_uniq', 'unique (prefixe_compte)', u'Le pr\u00E9fixe compte doit \u00EAtre unique !')
    ]


class account_account(osv.Model):
    _name = "account.account"
    _inherit = "account.account"
    
    def create(self, cr, uid, vals, context=None):
        # verifier type de compte et type interne correspondent le code dans les configurations des types de compte
        obj_type = self.pool.get('of.account.type')
        account_type = vals.get('type', False)
        user_type = vals.get('user_type', False)
        code = vals.get('code', False)
        prefixe_ids = []
        if account_type and user_type and code:
            if account_type != 'view':
                len_code = len(str(code))
                i = 0
                while i < len_code:
                    if i == 0:
                        prefixe_ids = obj_type.search(cr, uid, [('prefixe_compte', '=', code)])
                    else:
                        prefixe_ids = obj_type.search(cr, uid, [('prefixe_compte', '=', code[:-i])])
                    if len(prefixe_ids) != 0:
                        break
                    i += 1
        if len(prefixe_ids) != 0:
            prefixe_id = prefixe_ids[0]
            prefixe_obj = obj_type.browse(cr, uid, prefixe_id)
            pre_type = prefixe_obj.account_type
            pre_user_type = prefixe_obj.account_user_type.id
            if (pre_type != account_type) or (pre_user_type != user_type):
                raise osv.except_osv('Attention', 'Le code du compte ne corresponde pas le type de compte ou le type interne')
        return super(account_account, self).create(cr, uid, vals, context=context)
    
    def write(self, cr, uid, ids, vals, context=None):
        if context is None:
            context = {}
        if not ids:
            return True
        if isinstance(ids, (int, long)):
            ids = [ids]
        obj_type = self.pool.get('of.account.type')
        if ('type' in vals.keys()) or ('user_type' in vals.keys()) or ('code' in vals.keys()):
            for account in self.browse(cr, uid, ids):
                account_type = ('type' in vals.keys()) and vals['type'] or account.type or False
                user_type = ('user_type' in vals.keys()) and vals['user_type'] or (account.user_type and account.user_type.id or False)
                code = ('code' in vals.keys()) and vals['code'] or account.code or False
                if account_type and user_type and code:
                    if account_type != 'view':
                        i = 0
                        while i < len(str(code)):
                            if i == 0:
                                prefixe_ids = obj_type.search(cr, uid, [('prefixe_compte', '=', code)])
                            else:
                                prefixe_ids = obj_type.search(cr, uid, [('prefixe_compte', '=', code[:-i])])
                            if len(prefixe_ids) != 0:
                                break
                            i += 1
                        if len(prefixe_ids) != 0:
                            prefixe_id = prefixe_ids[0]
                            prefixe_obj = obj_type.browse(cr, uid, prefixe_id)
                            pre_type = prefixe_obj.account_type
                            pre_user_type = prefixe_obj.account_user_type.id
                            if (pre_type != account_type) or (pre_user_type != user_type):
                                raise osv.except_osv('Attention', 'Le code du compte ne corresponde pas le type de compte ou le type interne')
            
        return super(account_account, self).write(cr, uid, ids, vals, context=context)

class account_tax_code(osv.Model):
    _inherit = 'account.tax.code'
    _name = 'account.tax.code'
    _order = 'sequence'
