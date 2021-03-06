# -*- coding: utf-8 -*-

from odoo import api, models, fields
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta
from __builtin__ import False

class OfPlanningTache(models.Model):
    _name = "of.planning.tache"
    _description = u"Planning OpenFire : Tâches"

    name = fields.Char(u'Libellé', size=64, required=True)
    description = fields.Text('Description')
    verr = fields.Boolean(u'Verrouillé')
    product_id = fields.Many2one('product.product', 'Produit')
    active = fields.Boolean('Actif', default=True)
    imp_detail = fields.Boolean(u'Imprimer Détail', help=u"""Impression du détail des tâches dans le planning semaine
Si cette option n'est pas cochée, seule la tâche la plus souvent effectuée dans la journée apparaîtra""", default=True)
    duree = fields.Float(u'Durée par défaut', digits=(12, 5), default=1.0)
    category_id = fields.Many2one('hr.employee.category', string=u"Catégorie d'employés")
    is_crm = fields.Boolean(u'Tâche CRM')
    equipe_ids = fields.Many2many('of.planning.equipe', 'equipe_tache_rel', 'tache_id', 'equipe_id', 'Équipes')

    @api.multi
    def unlink(self):
        if self.search([('id', 'in', self._ids), ('verr', '=', True)]):
            raise ValidationError(u'Vous essayez de supprimer une tâche verrouillée.')
        return super(OfPlanningTache, self).unlink()

class OfPlanningEquipe(models.Model):
    _name = "of.planning.equipe"
    _description = u"Équipe d'intervention"
    _order = "sequence, name"

#     def _get_employee_equipes(self, cr, uid, ids, context=None):
#         result = []
#         for emp in self.read(cr, uid, ids, ['equipe_ids']):
#             result += emp['equipe_ids']
#         return list(set(result))

    name = fields.Char(u'Équipe', size=128, required=True)
    note = fields.Text('Description')
    employee_ids = fields.Many2many('hr.employee', 'of_planning_employee_rel', 'equipe_id', 'employee_id', u'Employés')
    active = fields.Boolean('Actif', default=True)
    category_ids = fields.Many2many('hr.employee.category', 'equipe_category_rel', 'equipe_id', 'category_id', u'Catégories')
    intervention_ids = fields.One2many('of.planning.intervention', 'equipe_id', u'Interventions liées', copy=False)
    tache_ids = fields.Many2many('of.planning.tache', 'equipe_tache_rel', 'equipe_id', 'tache_id', u'Compétences')
    hor_md = fields.Float(u'Matin début', required=True, digits=(12, 5))
    hor_mf = fields.Float('Matin fin', required=True, digits=(12, 5))
    hor_ad = fields.Float(u'Après-midi début', required=True, digits=(12, 5))
    hor_af = fields.Float(u'Après-midi fin', required=True, digits=(12, 5))
    sequence = fields.Integer(u'Séquence', help=u"Ordre d'affichage (plus petit en premier)")

    @api.onchange('employee_ids')
    def onchange_employees(self):
        if not self.category_ids:
            category_ids = []
            for employee in self.employee_ids:
                for category in employee.category_ids:
                    if category.id not in category_ids:
                        category_ids.append(category.id)
            if category_ids:
                self.category_ids = category_ids

    @api.onchange('hor_md', 'hor_mf', 'hor_ad', 'hor_af')
    def onchange_horaires(self):
        hors = (self.hor_md, self.hor_mf, self.hor_ad, self.hor_af)
        if all(hors):
            for hor in hors:
                if hor > 24:
                    raise ValidationError(u"L'heure doit être inférieure ou égale à 24")
            if hors[0] > hors[1] or hors[2] > hors[3]:
                raise ValidationError(u"L'heure de début ne peut pas être supérieure à l'heure de fin")
            if(hors[1] > hors[2]):
                raise ValidationError(u"L'heure de l'après-midi ne peut pas être inférieure à l'heure du matin")

class OfPlanningInterventionRaison(models.Model):
    _name = "of.planning.intervention.raison"
    _description = u"Raisons d'intervention reportée"

    name = fields.Char(u'Libellé', size=128, required=True)

class OfPlanningIntervention(models.Model):
    _name = "of.planning.intervention"
    _description = "Planning d'intervention OpenFire"
    _inherit = "of.readgroup"

#     def _get_color(self, cr, uid, ids, *args):
#         result = {}
#         for intervention in self.browse(cr, uid, ids):
#             equipe = intervention.equipe_id
#             cal_color = equipe and equipe.color_id
#             result[intervention.id] = cal_color and (intervention.state == 'draft' and cal_color.color2 or cal_color.color) or ''
#         return result

    @api.depends('date', 'duree', 'hor_md', 'hor_mf', 'hor_ad', 'hor_af', 'hor_sam', 'hor_dim')
    def _get_date_deadline(self):
        for intervention in self:
            if intervention.hor_md > 24 or intervention.hor_mf > 24 or intervention.hor_ad > 24 or intervention.hor_af > 24:
                raise UserError(u"L'heure doit être inferieure ou égale à 24")
            if intervention.hor_mf < intervention.hor_md or intervention.hor_ad < intervention.hor_mf:
                raise UserError(u"L'heure de début ne peut pas être supérieure à l'heure de fin")
            if intervention.hor_ad < intervention.hor_mf:
                raise UserError(u"L'heure de l'après-midi ne peut pas être inférieure à l'heure du matin")

            if not intervention.date:
                return
            if not intervention.duree:
                return

            # Datetime UTC
            dt_utc = datetime.strptime(intervention.date, "%Y-%m-%d %H:%M:%S")
            # Datetime local
            dt_local = fields.Datetime.context_timestamp(intervention, dt_utc)

            weekday = dt_local.weekday()
            if weekday == 5 and not intervention.hor_sam:
                raise UserError(u"L'équipe ne travaille pas le samedi")
            elif weekday == 6 and not intervention.hor_dim:
                raise UserError(u"L'équipe ne travaille pas le dimanche")

            duree_repos = intervention.hor_ad - intervention.hor_mf
            duree_matin = intervention.hor_mf - intervention.hor_md
            duree_apres = intervention.hor_af - intervention.hor_ad
            duree_jour = duree_matin + duree_apres

            dt_heure = dt_local.hour + (dt_local.minute + dt_local.second / 60.0) / 60.0
            # Déplacement de l'horaire de début au début de la journée pour faciliter le calcul
            duree = intervention.duree
            if intervention.hor_md <= dt_heure <= intervention.hor_mf:
                duree += dt_heure - intervention.hor_md
            elif intervention.hor_ad <= dt_heure <= intervention.hor_af:
                duree += duree_matin + dt_heure - intervention.hor_ad
            else:
                # L'horaire de debut des travaux est en dehors des heures de travail
                raise UserError(u"Il faut respecter l'horaire de travail")
            dt_local -= timedelta(hours=dt_heure)

            # Calcul du nombre de jours
            jours, duree = duree // duree_jour, duree % duree_jour
            # Correction erreur d'arrondi
            if duree * 60 < 1: # ça dépasse de moins d'une minute
                # Le travail se termine à la fin de la journée
                duree = duree_jour
                jours -= 1

            if not (intervention.hor_sam and intervention.hor_dim):
                # Deplacement de l'horaire de debut au debut de la semaine pour faciliter le calcul
                # Le debut de la semaine peut eventuellement etre un dimanche matin
                jours_sem = (weekday + intervention.hor_dim) % 6
                dt_local -= timedelta(days=jours_sem)
                jours += jours_sem

                # Ajout des jours de repos a la duree de la tache pour arriver la meme date de fin
                jours += (2 - intervention.hor_sam - intervention.hor_dim) * (jours // (5 + intervention.hor_sam + intervention.hor_dim))

            # Ajout des heures non travaillées de la derniere journée
            duree += intervention.hor_md + (duree > duree_matin and duree_repos)

            # Calcul de la nouvelle date
            dt_local += timedelta(days=jours, hours=duree)
            # Conversion en UTC
            dt_utc = dt_local - dt_local.tzinfo._utcoffset
            date_deadline = dt_utc.strftime("%Y-%m-%d %H:%M:%S")
            intervention.date_deadline = date_deadline

    @api.depends('address_id', 'address_id.parent_id')
    def _get_partner_id(self):
        for intervention in self:
            partner = intervention.address_id or False
            if partner:
                while partner.parent_id:
                    partner = partner.parent_id
            intervention.partner_id = partner and partner.id

    name = fields.Char(string=u'Libellé', required=True)
    date = fields.Datetime(string='Date intervention', required=True)
    date_deadline = fields.Datetime(compute="_get_date_deadline", string='Date Fin', store=True)
    duree = fields.Float(string=u'Durée intervention', required=True, digits=(12, 5))
    user_id = fields.Many2one('res.users', string='Utilisateur', default=lambda self: self.env.uid)
    partner_id = fields.Many2one('res.partner', string='Client', compute='_get_partner_id', store=True)
    address_id = fields.Many2one('res.partner', string='Adresse')
    partner_city = fields.Char(related='address_id.city')
    raison_id = fields.Many2one('of.planning.intervention.raison', string='Raison')
    tache_id = fields.Many2one('of.planning.tache', string='Tâche', required=True)
    equipe_id = fields.Many2one('of.planning.equipe', string=u'Équipe', required=True, oldname='poseur_id')
    employee_ids = fields.Many2many(related='equipe_id.employee_ids', string='Intervenants', readonly=True)
    state = fields.Selection([
        ('draft', 'Brouillon'),
        ('confirm', u'Confirmé'),
        ('done', u'Réalisé'),
        ('cancel', u'Annulé'),
        ('postponed', u'Reporté'),
        ], string=u'État', index=True, readonly=True, default='draft')
#     state = fields.Many2one('of.planning.intervention.state', string=u"État")
    company_id = fields.Many2one('res.company', string='Magasin', default=lambda self: self.env.user.company_id.id)
    description = fields.Text(string='Description')
    hor_md = fields.Float(string=u'Matin début', required=True, digits=(12, 5))
    hor_mf = fields.Float(string='Matin fin', required=True, digits=(12, 5))
    hor_ad = fields.Float(string=u'Après-midi début', required=True, digits=(12, 5))
    hor_af = fields.Float(string=u'Après-midi fin', required=True, digits=(12, 5))
    hor_sam = fields.Boolean(string='Samedi')
    hor_dim = fields.Boolean(string='Dimanche')

    category_id = fields.Many2one(related='tache_id.category_id', string=u"Type de tâche")
    verif_dispo = fields.Boolean(string=u'Vérif', help=u"Vérifier la disponibilité de l'équipe sur ce créneau", default=True)

#    _columns = {
#         'color'                : fields_old.function(_get_color, type='char', help=u"Couleur utilisée pour le planning. Dépend de l'équipe d'intervention et de l'état de l'intervention"),
#         'sidebar_color'        : fields_old.related('equipe_id','color_id','color', type='char', help="Couleur pour le menu droit du planning (couleur de base de l'équipe d'intervention)"),
#    }
    _order = 'date'

    @api.onchange('address_id')
    def _onchange_address_id(self):
        name = False
        if self.address_id:
            name = [self.address_id.name_get()[0][1]]
            for field in ('zip', 'city'):
                val = getattr(self.address_id, field)
                if val:
                    name.append(val)
        self.name = name and " ".join(name) or "Intervention"

    @api.onchange('tache_id')
    def _onchange_tache_id(self):
        if self.tache_id and self.tache_id.duree:
            self.duree = self.tache_id.duree

    @api.onchange('equipe_id')
    def _onchange_equipe_id(self):
        equipe = self.equipe_id
        if equipe.hor_md and equipe.hor_mf and equipe.hor_ad and equipe.hor_af:
            self.hor_md = equipe.hor_md
            self.hor_mf = equipe.hor_mf
            self.hor_ad = equipe.hor_ad
            self.hor_af = equipe.hor_af

    @api.multi
    def button_confirm(self):
        return self.write({'state': 'confirm'})

    @api.multi
    def button_done(self):
        return self.write({'state': 'done'})

    @api.multi
    def button_postponed(self):
        return self.write({'state': 'postponed'})

    @api.multi
    def button_cancel(self):
        return self.write({'state': 'cancel'})

    @api.multi
    def button_draft(self):
        return self.write({'state': 'draft'})

    @api.multi
    def change_state_after(self):
        next_state = {
            'draft'    : 'confirm',
            'confirm'  : 'done',
            'done'     : 'cancel',
            'cancel'   : 'postponed',
            'postponed': 'draft',
        }
        for intervention in self:
            intervention.state = next_state[intervention.state]
        return True

    @api.multi
    def change_state_before(self):
        previous_state = {
            'draft'    : 'postponed',
            'confirm'  : 'draft',
            'done'     : 'confirm',
            'cancel'   : 'done',
            'postponed': 'cancel',
        }
        for intervention in self:
            intervention.state = previous_state[intervention.state]
        return True

    @api.model
    def create(self, vals):
        # Vérification de la disponibilité du créneau
        if vals.get('verif_dispo') and vals.get('date') and vals.get('date_deadline'):
            rdv = self.search([
                ('equipe_id', '=', vals.get('equipe_id')),
                ('date', '<', vals['date_deadline']),
                ('date_deadline', '>', vals['date']),
                ('state', 'not in', ('cancel', 'postponed')),
            ])
            if rdv:
                raise ValidationError('Attention', u'Cette équipe a déjà %s rendez-vous sur ce créneau' % (len(rdv),))
        return super(OfPlanningIntervention, self).create(vals)

    @api.multi
    def write(self, vals):
        super(OfPlanningIntervention, self).write(vals)

        # Vérification de la validité du créneau
        for intervention in self:
            if intervention.verif_dispo:
                rdv = self.search([
                    ('equipe_id', '=', intervention.equipe_id.id),
                    ('date', '<', intervention.date_deadline),
                    ('date_deadline', '>', intervention.date),
                    ('id', '!=', intervention.id),
                    ('state', 'not in', ('cancel', 'postponed')),
                ])
                if rdv:
                    raise ValidationError(u'Cette équipe a déjà %s rendez-vous sur ce créneau' % (len(rdv),))
        return True

    @api.model
    def _read_group_process_groupby(self, gb, query):
        # Ajout de la possibilité de regrouper par employé
        if gb != 'gb_employee_id':
            return super(OfPlanningIntervention, self)._read_group_process_groupby(gb, query)

        alias, _ = query.add_join(
            (self._table, 'of_planning_employee_rel', 'equipe_id', 'equipe_id', 'equipe_id'),
            implicit=False, outer=True,
        )

        return {
            'field': gb,
            'groupby': gb,
            'type': 'many2one',
            'display_format': None,
            'interval': None,
            'tz_convert': False,
            'qualified_field': '"%s".employee_id' % (alias,)
        }

    @api.multi
    def _prepare_invoice(self):
        self.ensure_one()

        msg_succes = u"SUCCES : création de la facture depuis l'intervention %s"
        msg_erreur = u"ÉCHEC : création de la facture depuis l'intervention %s : %s"

        partner = self.partner_id
        err = []
        if not partner:
            err.append("sans partenaire")
        product = self.tache_id.product_id
        if not product:
            err.append(u"pas de produit lié")
        elif product.type != 'service':
            err.append(u"le produit lié doit être de type 'Service'")
        if err:
            return (False,
                    msg_erreur % (self.name, ", ".join(err)))
        fiscal_position_id = self.env['account.fiscal.position'].get_fiscal_position(partner.id, delivery_id=self.address_id.id)
        if not fiscal_position_id:
            return (False,
                    msg_erreur % (self.name, u"pas de position fiscale définie pour le partenaire ni pour la société"))

        # Préparation de la ligne de facture
        taxes = product.taxes_id
        if partner.company_id:
            taxes = taxes.filtered(lambda r: r.company_id == partner.company_id)
        taxes = self.env['account.fiscal.position'].browse(fiscal_position_id).map_tax(taxes, product, partner)

        line_account = product.property_account_income_id or product.categ_id.property_account_income_categ_id
        if not line_account:
            return (False,
                    msg_erreur % (self.name, u'Il faut configurer les comptes de revenus pour la catégorie du produit\n'))

        # Mapping des comptes par taxe induit par le module of_account_tax
        for tax in taxes:
            line_account = tax.map_account(line_account)

        pricelist = partner.property_product_pricelist
        company = partner.company_id
        from_currency = company.currency_id

        if pricelist.discount_policy == 'without_discount':
            from_currency = company.currency_id
            price_unit = from_currency.compute(product.lst_price, pricelist.currency_id)
        else:
            price_unit = product.with_context(pricelist=pricelist.id).price
        price_unit = self.env['account.tax']._fix_tax_included_price(price_unit, product.taxes_id, taxes)

        line_data = {
            'name': product.name_get()[0][1],
            'origin': 'Intervention',
            'account_id': line_account.id,
            'price_unit': price_unit,
            'quantity': 1.0,
            'discount': 0.0,
            'uom_id': product.uom_id.id,
            'product_id': product.id,
            'invoice_line_tax_ids': [(6, 0, taxes._ids)],
        }

        journal_id = self.env['account.invoice'].with_context(company_id=company.id).default_get(['journal_id'])['journal_id']
        if not journal_id:
            raise UserError(u"Vous devez définir un journal des ventes pour cette société (%s)." % company.name)
        invoice_data = {
            'origin': 'Intervention',
            'type': 'out_invoice',
            'account_id': partner.property_account_receivable_id.id,
            'partner_id': partner.id,
            'partner_shipping_id': self.address_id.id,
            'journal_id': journal_id,
            'currency_id': pricelist.currency_id.id,
            'fiscal_position_id': fiscal_position_id,
            'company_id': company.id,
            'user_id': self._uid,
            'invoice_line_ids': [(0, 0, line_data)],
        }

        return (invoice_data,
                msg_succes % (self.name,))

    @api.multi
    def create_invoice(self):
        invoice_obj = self.env['account.invoice']

        msgs = []
        for intervention in self:
            invoice_data, msg = intervention._prepare_invoice()
            msgs.append(msg)
            if invoice_data:
                invoice = invoice_obj.create(invoice_data)
                invoice.compute_taxes()
                invoice.message_post_with_view('mail.message_origin_link',
                                               values={'self': invoice, 'origin': intervention},
                                               subtype_id=self.env.ref('mail.mt_note').id)
        msg = "\n".join(msgs)

        return {
            'name'     : u'Création de la facture',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'of.planning.message.invoice',
            'type'     : 'ir.actions.act_window',
            'target'   : 'new',
            'context'  : {'default_msg': msg}
        }

class ResPartner(models.Model):
    _inherit = "res.partner"

    intervention_partner_ids = fields.One2many('of.planning.intervention', 'partner_id', "Interventions client")
    intervention_address_ids = fields.One2many('of.planning.intervention', 'address_id', "Interventions adresse")
