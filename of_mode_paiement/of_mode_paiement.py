from openerp.osv import fields, osv
# import pooler
import time

class of_payment_mode(osv.osv):
    _name= 'payment.mode'
    _inherit = 'payment.mode'

    _columns = {
        'type': fields.related('journal','type',type='selection',store=False,string='Type',
                               selection=[('sale', 'Sale'),('sale_refund','Sale Refund'), ('purchase', 'Purchase'), ('purchase_refund','Purchase Refund'),
                                          ('cash', 'Cash'), ('bank', 'Bank and Checks'), ('general', 'General'), ('situation', 'Opening/Closing Situation')])
    }
of_payment_mode()

class of_account_voucher(osv.osv):
    _name = 'account.voucher'
    _inherit = 'account.voucher'
    _order = "date desc, id desc"


    def __init__(self, pool, cr):
        res = super(of_account_voucher, self).__init__(pool, cr)
        
        cr.execute("SELECT id FROM ir_model_fields WHERE model='account.voucher' AND name='mode_id'")
        if not cr.fetchone():
            cr.execute('ALTER TABLE "account_voucher" ADD COLUMN "mode_id_temp" int4');
            cr.execute('UPDATE account_voucher SET mode_id_temp = mode.id FROM payment_mode AS mode WHERE mode.journal=journal_id')
        
        return res

    def _of_finish_install(self, cr, uid):
        cr.execute("SELECT * FROM information_schema.columns WHERE table_name='account_voucher' AND column_name='mode_id_temp'")
        if cr.fetchone():
            cr.execute('UPDATE account_voucher SET mode_id = mode_id_temp')
            cr.execute('ALTER TABLE "account_voucher" DROP COLUMN "mode_id_temp"');

    _columns = {
#        'name'      : fields.selection(_get_lines, 'Memo', required=True, size=256, readonly=True, states={'draft':[('readonly', False)]}),
        'journal_id': fields.related('mode_id','journal',type='many2one',relation='account.journal', string='Journal', store=False),
        'mode_id'   : fields.many2one('payment.mode', 'Mode de paiement', required=True, readonly=True, states={'draft':[('readonly',False)]}),
    }
    
    def onchange_mode(self, cr, uid, ids, mode_id, journal_id, line_ids, tax_id, partner_id, date, amount, ttype, company_id, context=None):
        res = {}
        new_journal_id = self.pool.get('payment.mode').browse(cr,uid,mode_id).journal.id
        if new_journal_id != journal_id:
            res = self.onchange_journal(cr, uid, ids, new_journal_id, line_ids, tax_id, partner_id, date, amount, ttype, company_id, context=context)
            res['value']['journal_id'] = new_journal_id
        return res
    
of_account_voucher()

class account_statement_from_invoice_lines(osv.osv_memory):
    _inherit = 'account.statement.from.invoice.lines'
    
    def populate_statement(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        statement_id = context.get('statement_id', False)
        if not statement_id:
            return {'type': 'ir.actions.act_window_close'}
        data =  self.read(cr, uid, ids, context=context)[0]
        line_ids = data['line_ids']
        if not line_ids:
            return {'type': 'ir.actions.act_window_close'}

        line_obj = self.pool.get('account.move.line')
        statement_obj = self.pool.get('account.bank.statement')
        statement_line_obj = self.pool.get('account.bank.statement.line')
        currency_obj = self.pool.get('res.currency')
        voucher_obj = self.pool.get('account.voucher')
        voucher_line_obj = self.pool.get('account.voucher.line')
        payment_mode_obj = self.pool.get('payment.mode')
        line_date = time.strftime('%Y-%m-%d')
        statement = statement_obj.browse(cr, uid, statement_id, context=context)

        # for each selected move lines
        for line in line_obj.browse(cr, uid, line_ids, context=context):
            voucher_res = {}
            ctx = context.copy()
            #  take the date for computation of currency => use payment date
            ctx['date'] = line_date
            amount = 0.0

            if line.debit > 0:
                amount = line.debit
            elif line.credit > 0:
                amount = -line.credit

            if line.amount_currency:
                amount = currency_obj.compute(cr, uid, line.currency_id.id,
                    statement.currency.id, line.amount_currency, context=ctx)
            elif (line.invoice and line.invoice.currency_id.id <> statement.currency.id):
                amount = currency_obj.compute(cr, uid, line.invoice.currency_id.id,
                    statement.currency.id, amount, context=ctx)

            context.update({'move_line_ids': [line.id],
                            'invoice_id': line.invoice.id})
            result = voucher_obj.onchange_partner_id(cr, uid, [], partner_id=line.partner_id.id, journal_id=statement.journal_id.id, amount=abs(amount), currency_id= statement.currency.id, ttype=(amount < 0 and 'payment' or 'receipt'), date=line_date, context=context)
            mode_ids = payment_mode_obj.search(cr,uid,[('journal','=',statement.journal_id.id)])
            if not mode_ids:
                raise osv.except_osv(('Pas de mode de paiement !'),(u"L'import de factures n\u00E9cessite que le journal s\u00E9lectionn\u00E9 (%s) ait au moins un mode de paiement associ\u00E9") % (statement.journal_id.name,))
            voucher_res = { 'type':(amount < 0 and 'payment' or 'receipt'),
                            'name': line.name,
                            'partner_id': line.partner_id.id,
                            'mode_id': mode_ids[0],
                            'account_id': result.get('account_id', statement.journal_id.default_credit_account_id.id), # improve me: statement.journal_id.default_credit_account_id.id
                            'company_id':statement.company_id.id,
                            'currency_id':statement.currency.id,
                            'date':line.date,
                            'amount':abs(amount),
                            'payment_rate': result['value']['payment_rate'],
                            'payment_rate_currency_id': result['value']['payment_rate_currency_id'],
                            'period_id':statement.period_id.id}
            voucher_id = voucher_obj.create(cr, uid, voucher_res, context=context)

            voucher_line_dict =  {}
            for line_dict in result['value']['line_cr_ids'] + result['value']['line_dr_ids']:
                move_line = line_obj.browse(cr, uid, line_dict['move_line_id'], context)
                if line.move_id.id == move_line.move_id.id:
                    voucher_line_dict = line_dict

            if voucher_line_dict:
                voucher_line_dict.update({'voucher_id': voucher_id})
                voucher_line_obj.create(cr, uid, voucher_line_dict, context=context)

            #Updated the amount of voucher in case of partially paid invoice
            amount_res = voucher_line_dict.get('amount_unreconciled',amount)
            voucher_obj.write(cr, uid, voucher_id, {'amount':amount_res}, context=context)

            if line.journal_id.type == 'sale':
                type = 'customer'
            elif line.journal_id.type == 'purchase':
                type = 'supplier'
            else:
                type = 'general'
            statement_line_obj.create(cr, uid, {
                'name': line.name or '?',
                'amount': amount_res if amount >= 0 else -amount_res,
                'type': type,
                'partner_id': line.partner_id.id,
                'account_id': line.account_id.id,
                'statement_id': statement_id,
                'ref': line.ref,
                'voucher_id': voucher_id,
                'date': statement.date,
            }, context=context)
        return {'type': 'ir.actions.act_window_close'}


account_statement_from_invoice_lines()
