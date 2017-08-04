# -*- coding: utf-8 -*-

import time
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from odoo import models, fields, api
from odoo.exceptions import ValidationError

class OFCRMProjet(models.Model):
    _name = 'of.crm.projet'
    _description = "Fiche de projet des Opportunités"

    name = fields.Char(string=u"Référence")
    line_ids = fields.One2many('of.crm.projet.entry', 'projet_id', string='Entrées')
    modele_id = fields.Many2one('of.crm.projet.modele', string=u"Modèle")
    lead_id = fields.Many2one('crm.lead', string=u"Opportunité", required=True)

class OFCRMProjetModele(models.Model):
    _name = 'of.crm.projet.modele'

    name = fields.Char(string=u"Libellé", required=True)
    dflt_attr_ids = fields.Many2many('of.crm.projet.attr', 'crm_projet_modele_attr_rel', 'modele_id', 'attr_id', string='Attributs')

class OFCRMProjetLine(models.Model):
    _name = 'of.crm.projet.line'

    projet_id = fields.Many2one('of.crm.projet', string="Projet", required=True)
    attr_id = fields.Many2one('of.crm.projet.attr', string="Attribut", required=True)
    type = fields.Selection([
        ('bool', u'Booléen'),
        ('char', u'Texte court'),
        #('selection', u'Sélection'),
        ], string=u'Type', required=True, default='char')
    val_bool = fields.Boolean(string="Valeur", default=False)
    val_char = fields.Char(string="Valeur")
    #val_selection = fields.One2many('of.crm.projet.attr.select', 'attr_id', string="Valeur")

class OFCRMProjetAttr(models.Model):
    _name = 'of.crm.projet.attr'

    name = fields.Char(string=u"Libellé", required=True)
    type = fields.Selection([
        ('bool', u'Booléen'),
        ('char', u'Texte court'),
        #('selection', u'Sélection'),
        ], string=u'Type', required=True, default='char')
    #selection_ids = fields.One2many('of.crm.projet.attr.select', 'attr_id', string="Valeur")
    modele_ids = fields.Many2many('of.crm.projet.attr', 'crm_projet_modele_attr_rel', 'attr_id', 'modele_id', string='Modèles')


class OFCRMProjetAttrSelect(models.Model):
    _name = 'of.crm.projet.attr.select'

    name = fields.Char(string=u"Libellé", required=True)
    description = fields.Text(string="Description")
    attr_id = fields.Many2one('of.crm.projet.attr', string="Attribut")
