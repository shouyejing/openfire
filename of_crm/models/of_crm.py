# -*- coding: utf-8 -*-

import time
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from odoo import models, fields, api

class Lead(models.Model):
    _inherit = 'crm.lead'

    of_website = fields.Char('Site web', help="Website of Lead")
    tag_ids = fields.Many2many('res.partner.category', 'crm_lead_res_partner_category_rel', 'lead_id', 'category_id', string='Tags', help="Classify and analyze your lead/opportunity categories like: Training, Service", oldname="of_tag_ids")
    of_description_projet = fields.Html('Notes de projet')
    of_ref = fields.Char(string=u"Référence",copy=False)
    of_prospecteur = fields.Many2one("res.users",string="Prospecteur")
    of_date_prospection = fields.Date(string="Date de prospection")
    #@TODO: implémenter la maj automatique de la date de cloture en fonction du passage de probabilité à 0 ou 100
    of_date_cloture = fields.Date(string="Date de clôture")
    of_infos_compl = fields.Text(string="Autres infos")
    geo_lat = fields.Float(string='Geo Lat', digits=(8, 8))
    geo_lng = fields.Float(string='Geo Lng', digits=(8, 8))
    stage_probability = fields.Float(related="stage_id.probability",readonly=True)

    #activity_ids = fields.One2many('of.crm.opportunity.activity', 'lead_id', string=u"Activités de cette opportunité")

    # Récupération du site web à la sélection du partenaire
    # Pas de api.onchange parceque crm.lead._onchange_partner_id_values
    def _onchange_partner_id_values(self, partner_id):
        res = super(Lead, self)._onchange_partner_id_values(partner_id)

        if partner_id:
            partner = self.env['res.partner'].browse(partner_id)

            res['of_website'] = partner.website
            res['geo_lat'] = partner.geo_lat
            res['geo_lng'] = partner.geo_lng
        return res

    # Transfert du site web à la création du partenaire
    @api.multi
    def _lead_create_contact(self, name, is_company, parent_id=False):
        """ extract data from lead to create a partner
            :param name : furtur name of the partner
            :param is_company : True if the partner is a company
            :param parent_id : id of the parent partner (False if no parent)
            :returns res.partner record
        """
        partner = super(Lead, self)._lead_create_contact(name, is_company, parent_id=parent_id)
        if self.of_website:
            partner.website = self.of_website
        if self.geo_lat:
            partner.geo_lat = self.geo_lat
        if self.geo_lng:
            partner.geo_lng = self.geo_lng
        return partner

    # Recherche du code postal en mode préfixe
    @api.model
    def search(self, args, offset=0, limit=None, order=None, count=False):
        pos = 0
        while pos < len(args):
            if args[pos][0] == 'zip' and args[pos][1] in ('like', 'ilike') and args[pos][2]:
                args[pos] = ('zip', '=like', args[pos][2]+'%')
            pos += 1
        return super(Lead, self).search(args, offset=offset, limit=limit, order=order, count=count)

    @api.multi
    def action_set_lost(self):
        """ surcharge sans appel à super(), une opportunité perdue n'est pas forcément archivée 
            fonction appelée (au moins) depuis le wizard de motif de perte
        """
        for lead in self:
            stage_id = lead._stage_find(domain=[('probability', '=', 0.0), ('on_change', '=', True)])
            lead.write({'stage_id': stage_id.id,
                        'probability': 0,
                        'of_date_cloture': time.strftime(DEFAULT_SERVER_DATE_FORMAT),
                        })
        return True

    @api.multi
    def action_set_won(self):
        res = super(Lead,self).action_set_won()
        for lead in self:
            lead.of_date_cloture = time.strftime(DEFAULT_SERVER_DATE_FORMAT)
        return res

    """@api.multi
    def write(self,vals):
        res = super(Lead,self).write(vals)
        if len(self) == 1:
            proba = self.probability
            if proba in (0.0,100.0):
                self.write({'of_date_cloture': time.strftime(DEFAULT_SERVER_DATE_FORMAT)})
        elif len(self) >= 1:
            proba = self._ids[0].probability
            if proba in (0.0,100.0):
                self.write({'of_date_cloture': time.strftime(DEFAULT_SERVER_DATE_FORMAT)})
        return res"""

class OFCrmActivity(models.Model):
    _inherit = 'crm.activity'


"""class OFCrmOpportunityActivity(models.Model):
    _name = 'of.crm.opportunity.activity'

    sequence = fields.Integer(string='Sequence', default=10)
    name = fields.Char(string='Libellé', required=True, index=True)
    lead_id = fields.Many2one('crm.lead', string=u"Opportunité", required=True)
    activity_id = fields.Many2one('crm.activity', string=u"Activité", required=True)
    is_late = fields.Boolean(string=u"En retard", compute="_compute_is_late")
    date_action = fields.Date(string=u"Date prévue") # à remplir via un onchange quelque part?
    date_done = fields.Date(string=u"Date faite") # à remplir via un onchange quelque part?
    is_done = fields.Boolean(string=u"Effectuée") # vouée à être retranscrit en bouton qui ouvre un wizard de compte rendu / de prévision de prochaine activité?
    activity_result = fields.Text(string="Compte rendu")

# transformer is_done et is_late en state? (1: 'todo', 2: 'late', 3: 'done') pour un _order = 'state'

    @api.multi
    def _compute_is_late(self):
        for action in self:
            if action.date_action and not action.is_done:
                action.is_late = action.date_action < time.strftime(DEFAULT_SERVER_DATE_FORMAT)
            else: # c'est pas en retard si c'est fait ou que y a pas de date
                action.is_late = False

    def add_report_to_opportunity_description(self):
        "" "
        copie le contenu du rapport dans le champ 'description' de lead_id.
        la personne fait son action co, tape son compte-rendu, valide, et ça s'ajoute automatiquement dans le champs note de l'opportunité quoi 
        "" "
        self.ensure_one()
        self.lead_id.description = self.activity_id + " (" + self.name + u") fait(e) le " + time.strftime(DEFAULT_SERVER_DATE_FORMAT) \
            + u": \n" + self.activity_result + "\n" + self.lead_id.description
"""
class Team(models.Model):
    _inherit = 'crm.team'

    # Retrait des filtres de recherche par défaut dans la vue 'Votre pipeline'
    @api.model
    def action_your_pipeline(self):
        action = super(Team, self).action_your_pipeline()
        action['context'] = {key: val for key, val in action['context'].iteritems() if not key.startswith('search_default_')}
        return action

class OFCRMResPartner(models.Model):
    _inherit = 'res.partner'

    is_prospect = fields.Boolean(string="Est un prospect")
    #prospects_inited = False
    #sale_order_components = self.filtered(lambda move: move.product_id.expense_policy == 'no').mapped('procurement_id.sale_comp_id') # bug mal initialisé sale_comp_id?

    @api.model
    def _init_prospects(self):
        customers = self.search([('customer','=',True)])
        customers._compute_sale_order_count()
        todo = self.search([('customer','=',True),'|',('parent_id','=', False),('company_type','=','company')]) # all customers without parent
        done = self.env['res.partner']
        length = len(customers)
        
        while len(todo) > 0:
            partner = todo[0]
            todo -= todo[0]
            if not partner.parent_id:
                if partner.sale_order_count == 0 and not partner.is_prospect:
                    partner.is_prospect = True
                elif partner.sale_order_count != 0 and partner.is_prospect:
                    partner.is_prospect = False
                done += partner
            else:
                print 'parent name: ', partner.parent_id.name
                partner.is_prospect = partner.parent_id.is_prospect
                done += partner
            if len(partner.child_ids) > 0:
                print 'name: ',partner.name
                print 'children ids: ',partner.child_ids._ids
                todo += partner.child_ids # add children to todo list
        if len(done) == length:
            print 'done!'
        else:
            print 'error!'

    @api.model
    def _init_prospects_old(self):
        partners = self.search([('customer','=',True)])
        partners._compute_sale_order_count()
        todo = self.env['res.partner']
        done = self.env['res.partner']
        length = len(partners)
        while len(done) <= length:
            while len(partners) > 0:
                partner = partners[len(partners)-1]
                partners -= partners[len(partners)-1]
                if not partner.parent_id:
                    if partner.sale_order_count == 0 and not partner.is_prospect:
                        partner.is_prospect = True
                    elif partner.sale_order_count != 0 and partner.is_prospect:
                        partner.is_prospect = False
                    done += partner
                elif partner.parent_id in done:
                    partner.is_prospect = partner.parent_id.is_prospect
                    done += partner
                else:
                    todo += partner
            partners = todo # update partners list
            todo = self.env['res.partner'] # refresh todo list

    def _compute_sale_order_count(self):
        """
surcharge méthode du même nom pour ne pas compter les devis dans les ventes
        """
        #added domain value for states
        sale_data = self.env['sale.order'].read_group(domain=[('partner_id', 'child_of', self.ids),('state','in',['sale','done'])],
                                                      fields=['partner_id'], groupby=['partner_id'])
        # read to keep the child/parent relation while aggregating the read_group result in the loop
        partner_child_ids = self.read(['child_ids'])
        mapped_data = dict([(m['partner_id'][0], m['partner_id_count']) for m in sale_data])
        for partner in self:
            # let's obtain the partner id and all its child ids from the read up there
            partner_ids = filter(lambda r: r['id'] == partner.id, partner_child_ids)[0]
            partner_ids = [partner_ids.get('id')] + partner_ids.get('child_ids')
            # then we can sum for all the partner's child
            #added is_prospect
            sale_order_count = sum(mapped_data.get(child, 0) for child in partner_ids)
            partner.sale_order_count = sale_order_count
            """if sale_order_count == 0:
                partner.is_prospect = True
            else:
                partner.is_prospect = False"""

class OFCRMSaleOrder(models.Model):
    _inherit = 'sale.order'
