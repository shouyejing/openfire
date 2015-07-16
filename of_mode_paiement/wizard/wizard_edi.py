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
# Migration from osv import fields, osv
from openerp import netsvc
import time
import unicodedata
import re
import base64


class wizard_paiement_edi(osv.TransientModel):
    u"""Ce wizard va effectuer un paiement par échange de fichier informatique"""
    _name = 'wizard.paiement.edi'
    _description = u"Effectuer un paiement par echange de fichier informatique"
    _columns={
        'date_remise': fields.date(u'Date de remise du paiement', required=True),
        'date_valeur': fields.date(u'Date de valeur du paiement (LCR)', required=False),
        'date_echeance': fields.date(u"Date d'échéance du paiement", required=True),
        'type_montant_facture': fields.selection([('solde','solde de la facture'),('echeancier',u"en fonction de l'échéancier")], u'Montant à payer des factures', required=True, help=u"Détermine comment est calculé le montant à payer des factures"),
        'motif': fields.selection([('nofacture','No de facture')], 'Motif opération (SEPA)', required=False, help=u"Texte qui apparaît sur le relevé bancaire du débiteur"),
        'date_creation': fields.text(u'Date de création'),
        'journal_id': fields.related('mode_paiement_id','journal',type='many2one',relation='account.journal', string='Journal', store=False),
        'mode_paiement_id': fields.many2one('payment.mode', 'Mode de paiement', required=True),
        'sortie': fields.text(''),
        'fichier': fields.binary(u'Télécharger le fichier'),
        'nom_fichier': fields.char(u'Nom du Fichier', size=64),
        'aff_bouton_paiement': fields.boolean(),
        'aff_bouton_genere_fich': fields.boolean(),
        'type_paiement': fields.char(u'Type de paiement', size=16)
    }
    _defaults = {
        'date_remise': time.strftime('%Y-%m-%d'),
        'date_valeur': time.strftime('%Y-%m-%d'),
        'date_echeance': time.strftime('%Y-%m-%d'),
        'date_creation': time.strftime('%Y-%m-%d %H:%M:%S'),
        'nom_fichier': "edi_" + time.strftime('%Y-%m-%d') +".txt",
        'motif': 'nofacture',
        'aff_bouton_paiement': False,
        'aff_bouton_genere_fich': True
    }
   
    def action_paiement_sepa_prev(self, cr, uid, ids, context=None):
        self.action_paiement_edi(cr, uid, ids, "sepa_prev", context)
        return {
            'type': 'ir.actions.act_window',
            'res_id': ids[0],
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'wizard.paiement.edi',
            'context' : context,
            'target': 'new',
        }
    
    def action_paiement_lcr(self, cr, uid, ids, context=None):
        self.action_paiement_edi(cr, uid, ids, "lcr", context)
        return {
            'type': 'ir.actions.act_window',
            'res_id': ids[0],
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'wizard.paiement.edi',
            'context' : context,
            'target': 'new',
        }
    
    def action_paiement_edi(self, cr, uid, ids, type_paiement="sepa_prev", context=None):
        u"""Action appelée pour effectuer un paiement EDI en fonction des factures sélectionnées"""
        if not isinstance(ids, list):
            ids = [ids]
        
        # On récupère les factures selectionnées
        invoice_obj = self.pool['account.invoice']
        liste_factures = invoice_obj.browse(cr, uid, context.get('active_ids', []), context)
        
        # Teste si au moins une facturé sélectionnée
        if not liste_factures:
            raise osv.except_osv(('Erreur ! (#ED105)'), u"Vous devez sélectionner au moins une facture.")
             
        # On vérifie qu'il s'agit bien de factures ouvertes non payées 
        for facture in liste_factures:
            if facture.type != "out_invoice" and facture.type != "in_refund":
                raise osv.except_osv(('Erreur ! (#ED110)'), u"Vous avez sélectionné au moins une facture qui n'est pas une facture client ou un avoir fournisseur.\n\nVous ne pouvez demander le règlement par LCR ou prélèvement SEPA que pour une facture client ou un avoir fournisseur.")
            if facture.state != "open" or facture.residual <= 0 or facture.amount_total <= 0:
                raise osv.except_osv(('Erreur ! (#ED115)'), u"Vous avez sélectionné au moins une facture non ouverte, déjà payée ou avec une balance ou un montant total négatif.\n\nVous devez sélectionner que des factures ouvertes, non payées avec une balance et un montant total positif.")
        
        # On récupère le mode de paiement du wizard et génère le fichier EDI
        res = self.browse(cr, uid, ids, context=context)
        if type_paiement == "lcr":
            self.genere_fichier_lcr(cr, uid, ids, res, liste_factures, context)
        else:
            self.genere_fichier_sepa_prev(cr, uid, ids, res, liste_factures, context)
        
        return True

    def genere_fichier_lcr(self, cr, uid, ids, res, liste_factures, context=None):
        u"""Génère le fichier pour lettre de change relevé (LCR)"""
        sortie = ""
        no_ligne = 1 # No de la ligne du fichier  généré
        nb_facture = 0 # Nombre de facture à acquitter (pas celles montant = 0)
        chaine = ""  # Contient la chaine du fichier généré
        montant_total = 0
        self.write(cr, uid, ids, {'date_creation': time.strftime('%Y-%m-%d %H:%M:%S')})
               
        # 1ère ligne : émetteur
        sortie += "Tireur : " + res[0].mode_paiement_id.company_id.name + " ["
        chaine += "0360"
        chaine += str(no_ligne).zfill(8)            # No de la ligne (no enregistrement sur 8 caractères)
        if res[0].mode_paiement_id.company_id.of_num_nne:  # No émetteur
            if len(res[0].mode_paiement_id.company_id.of_num_nne) > 6:
                raise osv.except_osv(('Erreur ! (#ED205)'), u"Le n° national d'émetteur de l'émetteur (" + str(res[0].mode_paiement_id.company_id.name) + u") dépasse 6 caractères.")
            chaine += self.chaine2ascii_taille_fixe_maj(res[0].mode_paiement_id.company_id.of_num_nne, 6)
        else:
            chaine += " " * 6
        chaine += " " * 6                           # Type convention (6 caractères)
        if res[0].date_remise:                      # Date de remise (6 caractères)
            chaine += res[0].date_remise[8:10]+res[0].date_remise[5:7]+res[0].date_remise[2:4]
        else:
            chaine += " " * 6
        chaine += self.chaine2ascii_taille_fixe_maj(res[0].mode_paiement_id.company_id.name, 24)  # Raison sociale de l'émetteur en majuscule sans accent et ponctuation interdite tronquée ou complétée à 24 caractères
        if res[0].mode_paiement_id.bank_id.bank_name:                        # Domiciliation (nom) bancaire du tirant
            chaine += self.chaine2ascii_taille_fixe_maj(res[0].mode_paiement_id.bank_id.bank_name, 24)
            sortie += res[0].mode_paiement_id.bank_id.bank_name
        chaine += "30E"                             # Code entrée, code Daily, code monnaie (euro)
        
        # référence bancaire émetteur - Configuré dans Odoo soit en IBAN soit en RIB
        temp = res[0].mode_paiement_id.bank_id.acc_number
        if temp:
            temp = temp.replace("IBAN", "").replace(" ", "").upper()
        if temp and len(temp) == 27 and temp[0:2] == "FR":  # Si IBAN renseigné et français, on se base dessus                
            chaine += temp[4:9]     # Code banque
            sortie += " Banque : " + temp[4:9]
            chaine += temp[9:14]    # Code guichet
            sortie += " Guichet : " + temp[9:14]
            chaine += temp[14:25]   # No compte
            sortie += " Compte : " + temp[14:25]
        elif res[0].mode_paiement_id.bank_id.bank_code and len(res[0].mode_paiement_id.bank_id.bank_code) == 5 and res[0].mode_paiement_id.bank_id.office and len(res[0].mode_paiement_id.bank_id.office) == 5 and res[0].mode_paiement_id.bank_id.rib_acc_number and len(res[0].mode_paiement_id.bank_id.rib_acc_number) == 11:   # On prend le RIB sinon si renseigné
            chaine += res[0].mode_paiement_id.bank_id.bank_code
            chaine += res[0].mode_paiement_id.bank_id.office
            chaine += res[0].mode_paiement_id.bank_id.rib_acc_number
            sortie += " Banque : " + res[0].mode_paiement_id.bank_id.bank_code + " Guichet : " + res[0].mode_paiement_id.bank_id.office + " Compte : " + res[0].mode_paiement_id.bank_id.rib_acc_number
        else:   # Aucune référence bancaire valide
            raise osv.except_osv(('Erreur ! (#ED210)'), u"Pas de coordonnées bancaires (RIB ou IBAN) valides trouvées pour le mode de paiement " + str(res[0].mode_paiement_id.name) + u".\n\n (codes banque et guichet 5 chiffres, n° compte 11 chiffres et clé 2 chiffres)")
        sortie += "]"
        chaine += " " * 16 # Zone réservée
        if res[0].date_valeur:          # Date de valeur
            chaine += res[0].date_valeur[8:10]+res[0].date_valeur[5:7]+res[0].date_valeur[2:4]
        else:
            chaine += " " * 6
        chaine += " " * 10 # Zone réservée
        
        temp = liste_factures[0].company_id.company_registry    # No SIREN
        if not temp:   
            chaine += " " * 15
        else:
            if len(temp.replace(" ", "")) == 14:   # C'est un n° SIRET. Le SIREN est les 9 premiers chiffres.
                temp = temp.replace(" ", "")[0:9]
            elif len(temp) > 15:
                raise osv.except_osv(('Erreur ! (#ED215)'), u"Le n° SIREN de la société " + liste_factures[0].company_id.name + u" dépasse 15 caractères.")
            chaine += temp.ljust(15, " ")
            sortie += " [No SIREN : " + temp + "]"
        chaine += " " * 11 # Référence remise à faire
        chaine += "\n"
        sortie += "\n"
        
        # 2e ligne : tiré(s)
        rib_obj = self.pool['res.partner.bank']
        for facture in liste_factures:
            if res[0].type_montant_facture == "echeancier":
                montant_du = self.montantapayer_echeancier(cr, uid, res, facture, context)
            else:
                montant_du = facture.residual
            
            # On vérifie que le montant à payer en fonction de l'échéancier n'est pas nul, sinon passe à la facture suivante
            if montant_du == 0:
                sortie += u"Facture non exigible suivant échéancier : " + facture.partner_id.name + u" [Rien à payer suivant échéancier] [Montant total facture : " + str('%.2f' % facture.amount_total).replace('.', ',') + u" euros]\n"
                continue
            elif montant_du < 0:
                raise osv.except_osv(('Erreur ! (#ED217)'), u"La balance de la facture de " + facture.partner_id.name + u" est négative.\n\nVous ne pouvez payer par LCR que des factures avec un solde positif.")
            else:
                nb_facture = nb_facture + 1
            
            sortie += u"Tiré : " + facture.partner_id.name + " ["
            rib = rib_obj.browse(cr, uid, rib_obj.search(cr, uid, [('partner_id', '=' , facture.partner_id.id)], context=context), context=context) 
            if not rib:
                raise osv.except_osv(('Erreur ! (#ED220)'), u"Pas de compte bancaire trouvé pour " + facture.partner_id.name + u".\n\nPour effectuer une LCR, un compte en banque doit être défini pour le client de chaque facture.")
            no_ligne = no_ligne + 1
            chaine += "0660"
            chaine += str(no_ligne).zfill(8)        # No de la ligne (no enregistrement sur 8 caractères)
            chaine += " " * 8                       # Zones réservées
            chaine += " " * 10                      # Référence du tiré
            chaine += self.chaine2ascii_taille_fixe_maj(facture.partner_id.name, 24) # Nom du tiré (24 caractères)
            if rib[0].bank_name:                    # Domiciliation (nom) bancaire du tiré
                chaine += self.chaine2ascii_taille_fixe_maj(rib[0].bank_name, 24)
                sortie += rib[0].bank_name
            else:
                chaine += " " * 24
            chaine += "0"                           # Acceptation
            chaine += " " * 2                       # Zone réservée
            
            # référence bancaire - Configuré dans Odoo soit en IBAN soit en RIB
            temp = rib[0].acc_number
            if temp:
                temp = temp.replace("IBAN", "").replace(" ", "").upper() # Suppression de possibles caractères superflus
            if temp and len(temp) == 27 and temp[0:2] == "FR":  # Si IBAN renseigné et français, on se base dessus                
                chaine += temp[4:9]     # Code banque
                sortie += " Banque : " + temp[4:9]
                chaine += temp[9:14]    # Code guichet
                sortie += " Guichet : " + temp[9:14]
                chaine += temp[14:25]   # No compte
                sortie += " Compte : " + temp[14:25]
            elif rib[0].bank_code and len(rib[0].bank_code) == 5 and rib[0].office and len(rib[0].office) == 5 and rib[0].rib_acc_number and len(rib[0].rib_acc_number) == 11 and rib[0].key and len(rib[0].key) == 2:   # On prend le RIB sinon si renseigné
                chaine += rib[0].bank_code
                chaine += rib[0].office
                chaine += rib[0].rib_acc_number
                sortie += " Banque : " + rib[0].bank_code + " Guichet : " + rib[0].office + " Compte : " + rib[0].rib_acc_number
            else:   # Aucune référence bancaire valide
                raise osv.except_osv(('Erreur ! (#ED225)'), u"Pas de coordonnées bancaires (RIB ou IBAN) valides trouvées pour " + facture.partner_id.name + u".\n\n (codes banque et guichet 5 chiffres, n° compte 11 chiffres et clé 2 chiffres)")
            sortie += "]"
            montant_total = montant_total + montant_du
            sortie += u" [Montant : " + str('%.2f' % montant_du).replace('.', ',') + u" euros]"
            chaine += str('%.2f' % montant_du).replace('.', '').zfill(12) # Montant
            chaine += " " * 4                       # Zone réservée
            chaine += res[0].date_echeance[8:10]+res[0].date_echeance[5:7]+res[0].date_echeance[2:4]    # Date d'échéance
            chaine += res[0].date_creation[8:10]+res[0].date_creation[5:7]+res[0].date_creation[2:4]    # Date de création
            chaine += " " * 4                       # Zone réservée
            chaine += " "                           # Type
            chaine += " " * 3                       # Nature
            chaine += " " * 3                       # Pays
            temp = facture.partner_id.company_registry    # No SIREN
            if not temp:
                chaine += " " * 9
            else:
                if len(temp.replace(" ", "")) == 14:   # C'est un n° SIRET. Le SIREN est les 9 premiers chiffres.
                    temp = temp.replace(" ", "")[0:9]
                elif len(temp) > 9:
                    raise osv.except_osv(('Erreur ! (#ED230)'), u"Le n° SIREN de " + facture.partner_id.name + u" dépasse 9 caractères.")
                chaine += temp.ljust(9, " ")
                sortie += u" [No SIREN : " + temp + "]"
            chaine += " " * 10                       # Référence tireur
            chaine += "\n"
            sortie += "\n"
        
        # Dernière ligne : total
        no_ligne = no_ligne + 1
        chaine += "0860"
        chaine += str(no_ligne).zfill(8)            # No de la ligne (no enregistrement sur 8 caractères)
        chaine += " " * 90                          # Zones réservées
        sortie += u">> Montant total : " + str('%.2f' % montant_total).replace('.', ',') + u" euros"
        chaine += str('%.2f' % montant_total).replace('.', '').zfill(12) # Montant total
        chaine += " " * 46                          # Zones réservées
        chaine += "\n"
        
        if nb_facture: # Si des factures sont à payer, on génère le fichier
            sortie = u"Pour enregistrer l'opération, vous devez valider le paiement des factures.\n\nLe fichier lettre change relevé (LCR) a été généré avec les éléments suivants :\n\n" + sortie
            chaine = base64.encodestring(chaine.encode('utf-8'))
            self.write(cr, uid, ids, {'fichier': chaine})
            self.write(cr, uid, ids, {'nom_fichier': u"lcr_" + time.strftime('%Y-%m-%d') + u".txt"})
            self.write(cr, uid, ids, {'type_paiement': u'lcr'})
            self.write(cr, uid, ids, {'aff_bouton_paiement': True})
        else:
            sortie = u"Aucune facture à payer. Le fichier n'a pas été généré.\n\n" + sortie
            self.write(cr, uid, ids, {'aff_bouton_paiement': False})
        
        self.write(cr, uid, ids, {'sortie': sortie})
        return True

    
    def genere_fichier_sepa_prev(self, cr, uid, ids, res, liste_factures, context=None):
        u"""Génère le fichier pour le prélèvement SEPA"""
        sortie = ""
        chaine_transaction = ""  # Contient la chaine du fichier généré
        chaine_entete = ""
        chaine_lot = ""
        montant_total = 0
        montant_total_lot = 0
        nb_transaction = 0
        nb_transaction_lot = 0
        index = 1 # Pour générer des identifiants uniques
        
        self.write(cr, uid, ids, {'date_creation': time.strftime('%Y-%m-%d %H:%M:%S')})
        
        rib_obj = self.pool['res.partner.bank']
       
        # On doit faire un lot par type de prélèvement (frst, rcur, ...)
        # On classe la liste des factures par type de prélèvement
        factures_par_type = {}
        for facture in liste_factures:
            if not facture.partner_id.of_sepa_type_prev:
                raise osv.except_osv(('Erreur ! (#ED431)'), u"Le champ \"Type de prélèvement SEPA\" n'a pas été configuré pour " + facture.partner_id.name + u".\n\nCe champ est obligatoire pour effectuer un prélèvement SEPA et se configure dans l'onglet Achats-Ventes du client.")
            if facture.partner_id.of_sepa_type_prev not in ('FRST','RCUR'):
                raise osv.except_osv(('Erreur ! (#ED432)'), u"Le champ \"Type de prélèvement SEPA\" contient une valeur incorrecte pour " + facture.partner_id.name + u".\n\nVeuillez configurer ce champ à nouveau. Il se configure dans l'onglet Achats-Ventes du client.")
            if facture.partner_id.of_sepa_type_prev not in factures_par_type:
                factures_par_type[facture.partner_id.of_sepa_type_prev] = []
            factures_par_type[facture.partner_id.of_sepa_type_prev].append(facture)
        
        # On parcourt la liste des factures
        # par type de prélèvement
        for type_prev in factures_par_type:
            # sur chaque facture d'un type
            for facture in factures_par_type[type_prev]:
                if res[0].type_montant_facture == "echeancier":
                    montant_du = self.montantapayer_echeancier(cr, uid, res, facture, context)
                else:
                    montant_du = facture.residual
                
                # On vérifie que le montant à payer en fonction de l'échéancier n'est pas nul, sinon passe à la facture suivante 
                if montant_du == 0:
                    sortie += u"Facture non exigible suivant échéancier : " + facture.partner_id.name + u" [Rien à payer suivant échéancier] [Montant total facture : " + str('%.2f' % facture.amount_total).replace('.', ',') + u" euros]\n"
                    continue
                elif montant_du < 0:
                    raise osv.except_osv(('Erreur ! (#ED434)'), u"La balance de la facture de " + facture.partner_id.name + u" est négative.\n\nVous ne pouvez payer par prélèvement SEPA que des factures avec un solde positif.")

                # On récupère les coordonnées bancaires
                rib = rib_obj.browse(cr, uid, rib_obj.search(cr, uid, [('partner_id', '=' , facture.partner_id.id)], context=context), context=context)
                if not rib:
                    raise osv.except_osv(('Erreur ! (#ED436)'), u"Pas de compte bancaire trouvé pour " + facture.partner_id.name + u".\n\nPour effectuer une opération SEPA, un compte en banque doit être défini pour le client de chaque facture.")
                chaine_transaction += u"""
                        <!-- Niveau transaction -->
                        <DrctDbtTxInf> <!-- Débit à effectuer (plusieurs possible) -->
                            <PmtId>
                                <EndToEndId>PREV""" + time.strftime('%S%M%H%d%m%Y') + str(index) + u"""</EndToEndId> <!-- Identifiant de transaction envoyé au débiteur obligatoire -->
                            </PmtId>
                            <InstdAmt Ccy="EUR">""" + str('%.2f' % montant_du)
                index = index + 1
                chaine_transaction += u"""</InstdAmt> <!-- Montant de la transaction obligatoire -->
                            <DrctDbtTx>
                                <MndtRltdInf> <!-- Informations relatives au mandat -->
                                    <MndtId>"""
                if facture.partner_id.of_sepa_rum:
                    chaine_transaction += str(facture.partner_id.of_sepa_rum)
                else:
                    raise osv.except_osv(('Erreur ! (#ED438)'), u"Pas de référence unique du mandat (RUM) trouvé pour " + facture.partner_id.name + u".\n\nLe RUM est obligatoire pour effectuer un prélèvement SEPA et se configure dans l'onglet Achats-Ventes du client.")
                chaine_transaction += u"""</MndtId> <!-- Code RUM -->
                                    <DtOfSgntr>"""
                if facture.partner_id.of_sepa_date_mandat:
                    chaine_transaction += str(facture.partner_id.of_sepa_date_mandat)
                else:
                    raise osv.except_osv(('Erreur ! (#ED440)'), u"Pas de date de signature du mandat SEPA trouvé pour " + facture.partner_id.name + u".\n\nCette date est obligatoire pour effectuer un prélèvement SEPA et se configure dans l'onglet Achats-Ventes du client.")
                chaine_transaction += u"""</DtOfSgntr> <!-- Date de signature du mandat -->
                                    <AmdmntInd>false</AmdmntInd> <!-- facultatif Indicateur permettant de signaler une modification d'une ou plusieurs données du mandat. Valeurs : "true" (si il y a des modifications) "false" (pas de modification). Valeur par défaut : "false" -->
                                </MndtRltdInf>
                            </DrctDbtTx>
                            <DbtrAgt> <!-- Référence banque débiteur -->
                                <FinInstnId>
                                    <BIC>"""
                if rib[0].bank_bic:
                    chaine_transaction += str(rib[0].bank_bic)
                else:
                    raise osv.except_osv(('Erreur ! (#ED445)'), u"Pas de code BIC (SWIFT) de la banque trouvé pour " + facture.partner_id.name + u".\n\nIl est nécessaire de fournir ce code pour effectuer une opération SEPA.")
                chaine_transaction += u"""</BIC> <!-- Code SWIFT banque débiteur -->
                                </FinInstnId>
                            </DbtrAgt>
                            <Dbtr> <!-- Information sur le débiteur obligatoire mais balises filles facultatives-->
                                <Nm>""" + self.chaine2ascii_taillemax(facture.partner_id.name, 70) + u"""</Nm> <!-- Nom débiteur -->
                            </Dbtr>
                            <DbtrAcct> <!-- Informations sur le compte à débiter obligatoire -->
                                <Id>
                                    <IBAN>"""
                if rib[0].acc_number:
                    chaine_transaction += str(rib[0].acc_number).replace("IBAN", "").replace(" ", "").upper()
                else:
                    raise osv.except_osv(('Erreur ! (#ED450)'), u"Pas d'IBAN valide trouvé pour " +  facture.partner_id.name + u".\n\nIl est nécessaire d'avoir des coordonnées bancaires sous forme d'IBAN pour effectuer une opération SEPA.")
                chaine_transaction += u"""</IBAN>
                                </Id>
                            </DbtrAcct>"""
                if res[0].motif:    # On insère le motif
                    if res[0].motif == 'nofacture' and facture.number:
                        chaine_transaction += u"""
                            <RmtInf> <!-- Information sur la remise de la transaction obligatoire -->
                                <Ustrd>Facture """ + self.chaine2ascii_taillemax(facture.number, 140) + u"""</Ustrd> <!-- Libellé apparaissant sur le relevé du débiteur -->
                            </RmtInf>"""
                chaine_transaction += u"""
                        </DrctDbtTxInf>
                        <!-- Fin niveau transaction -->"""
                nb_transaction = nb_transaction + 1
                nb_transaction_lot = nb_transaction_lot + 1
                montant_total = montant_total + montant_du
                montant_total_lot = montant_total_lot + montant_du
                sortie += u"Tiré : " + facture.partner_id.name + " ["
                if rib[0].bank_name:
                    sortie += rib[0].bank_name + " "
                sortie += u"BIC : " + rib[0].bank_bic + u" IBAN : " + str(rib[0].acc_number).upper() + u"] [Montant : " + str('%.2f' % montant_du).replace('.', ',') + u" euros]\n"
                # Fin parcours chaque facture d'un type
            
            # Si pas de facture à payer en fonction de l'échéancier dans ce lot, on passe au lot suivant
            if nb_transaction_lot == 0:
                continue
            
            # On génére le lot
            chaine_lot += u"""
                <!-- Lot de transaction -->
                <PmtInf> <!-- Instructions de prélèvements obligatoire au moins une fois-->
                    <PmtInfId>LOT""" + time.strftime('%S%M%H%d%m%Y') + str(index) + u"""</PmtInfId> <!-- Identifiant du lot de transactions Peut être la même valeur que GrpHdr si un seul lot de transaction obligatoire -->
                    <PmtMtd>DD</PmtMtd> <!-- Méthode de paiement obligatoire -->
                    <NbOfTxs>""" + str(nb_transaction_lot) + u"""</NbOfTxs> <!-- Nb de transaction du lot facultatif -->
                    <CtrlSum>""" + str('%.2f' % montant_total_lot) + u"""</CtrlSum> <!-- Cumul des sommes des transactions du lot facultatif -->
                    <PmtTpInf> <!-- Information sur le type de paiement Normalement facultatif mais certaines banques attendent cet élément -->
                        <SvcLvl> <!-- Niveau de service -->
                            <Cd>SEPA</Cd> <!-- Contient la valeur SEPA -->
                        </SvcLvl>
                        <LclInstrm>
                            <Cd>CORE</Cd> <!-- CORE pour les débits avec une personne physique, B2B pour les débits entre entreprises -->
                        </LclInstrm>
                        <SeqTp>""" + str(type_prev) + u"""</SeqTp> <!-- Type de séquence : OOFF pour un débit ponctuel, FIRST pour un 1er débit régulier, RCUR pour un débit régulier récurrent, FINAL pour un dernier débit récurrent -->
                    </PmtTpInf>
                    <ReqdColltnDt>""" + res[0].date_echeance + u"""</ReqdColltnDt> <!-- Date d'échéance -->
                    <Cdtr> <!-- Information sur le créancier -->
                        <Nm>""" + self.chaine2ascii_taillemax(res[0].mode_paiement_id.company_id.name, 70) + u"""</Nm> <!-- Nom du créancier facultatif -->
                    </Cdtr>
                    <CdtrAcct> <!-- Information du compte du créditeur -->
                        <Id> <!-- Peut aussi contenir balise CCy pour monnaie au format ISO -->
                            <IBAN>"""
            index = index + 1
            if res[0].mode_paiement_id.bank_id.acc_number:
                chaine_lot += str(res[0].mode_paiement_id.bank_id.acc_number).replace("IBAN", "").replace(" ", "").upper()
            else:
                raise osv.except_osv(('Erreur ! (#ED420)'), u"Pas d'IBAN valide trouvé pour le mode de paiement " + res[0].mode_paiement_id.name + u".\n\nIl est nécessaire d'avoir des coordonnées bancaires sous forme d'IBAN pour effectuer une opération SEPA.")
            chaine_lot += u"""</IBAN>
                        </Id>
                    </CdtrAcct>
                    <CdtrAgt> <!-- Banque du créancier -->
                        <FinInstnId>
                            <BIC>"""
            if res[0].mode_paiement_id.bank_id.bank_bic:
                chaine_lot += str(res[0].mode_paiement_id.bank_id.bank_bic)
            else:
                raise osv.except_osv(('Erreur ! (#ED425)'), u"Pas de code BIC (SWIFT) de la banque attachée au mode de paiement " + res[0].mode_paiement_id.name + u".\n\nIl est nécessaire de fournir ce code pour effectuer une opération SEPA.")
            chaine_lot += u"""</BIC> <!-- Code SWIFT de la banque facultatif -->
                        </FinInstnId>
                    </CdtrAgt>
                    <ChrgBr>SLEV</ChrgBr> <!-- Valeur fixe SLEV -->
                    <CdtrSchmeId> <!-- Identification du créancier -->
                        <Id>
                            <PrvtId>
                                <Othr>
                                    <Id>"""
            if res[0].mode_paiement_id.company_id.of_num_ics:
                chaine_lot += str(res[0].mode_paiement_id.company_id.of_num_ics)
            else:
                raise osv.except_osv(('Erreur ! (#ED430)'), u"Pas d'identifiant créancier SEPA (ICS) trouvé pour l'émetteur (" + res[0].mode_paiement_id.company_id.name + u").\n\nCet identifiant est obligatoire pour effectuer un prélèvement SEPA et se configure dans configuration/société/" + res[0].mode_paiement_id.company_id.name + ".")
            chaine_lot += u"""</Id> <!-- Identifiant du créancier ICS -->
                                    <SchmeNm>
                                        <Prtry>SEPA</Prtry> <!-- De valeur fixe SEPA -->
                                    </SchmeNm>
                                </Othr>
                            </PrvtId>
                        </Id>
                    </CdtrSchmeId>"""
            # On ajoute les transactions
            chaine_lot = chaine_lot + chaine_transaction + u"""
                </PmtInf>
                <!-- Fin lot de transaction -->
            """
            montant_total_lot = 0
            nb_transaction_lot = 0
            chaine_transaction = ""
            # Fin parcours par type
        
        # Fin parcourt de toutes les factures 
        # On ajoute l'en-tête
        chaine_entete += u"""<?xml version="1.0" encoding="utf-8"?>
        <Document xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns="urn:iso:std:iso:20022:tech:xsd:pain.008.001.02">
            <CstmrDrctDbtInitn>
                <GrpHdr> <!-- En tête -->
                    <MsgId>MES""" + time.strftime('%S%M%H%d%m%Y') + str(index) + u"""</MsgId> <!-- Identifiant unique du message M -->
                    <CreDtTm>""" + str(res[0].date_creation).replace(' ', 'T') + u"""</CreDtTm>    <!-- Date de création au format ISO M -->
                    <NbOfTxs>""" + str(nb_transaction) + """</NbOfTxs>    <!-- Nb total de transactions dans le fichier M -->
                    <CtrlSum>""" + str('%.2f' % montant_total) + u"""</CtrlSum> <!-- somme totale des transactions point pour décimale -->
                    <InitgPty>    <!-- élément de type Partyidentification32 Partie initiatrice de la transaction peut contenir nom créancier adresse Obligatoire mais peut être vide -->
                        <Nm>""" + self.chaine2ascii_taillemax(res[0].mode_paiement_id.company_id.name, 70) + u"""</Nm>
                    </InitgPty>
                </GrpHdr>
                <!-- Fin en-tête -->
                """
        index = index + 1
        # On met l'en-tête de début et les balises de fin 
        chaine = chaine_entete + chaine_lot + u"""
            </CstmrDrctDbtInitn>
        </Document>"""
        
        sortie += u">> Montant total : " + str('%.2f' % montant_total).replace('.', ',') + u" euros"
        sortie = "BIC : " + str(res[0].mode_paiement_id.bank_id.bank_bic) + u" IBAN : "+ str(res[0].mode_paiement_id.bank_id.acc_number).upper() + u"]\n" + sortie
        if res[0].mode_paiement_id.bank_id.bank_name:
            sortie = res[0].mode_paiement_id.bank_id.bank_name + " " + sortie
        
        sortie = u"Tireur : " + res[0].mode_paiement_id.company_id.name + u" [" + sortie
         
        if nb_transaction: # Si des factures sont à payer, on génère le fichier
            sortie = u"Pour enregistrer l'opération, vous devez valider le paiement des factures.\n\nLe fichier prélèvement SEPA a été généré avec les éléments suivants :\n\n" + sortie 
            chaine = base64.encodestring(chaine.encode('utf-8'))
            self.write(cr, uid, ids, {'fichier': chaine})
            self.write(cr, uid, ids, {'nom_fichier': "prelevement_sepa_" + time.strftime('%Y-%m-%d') +".txt"})
            self.write(cr, uid, ids, {'type_paiement': 'prev_sepa'})
            self.write(cr, uid, ids, {'aff_bouton_paiement': True})
        else:
            sortie = u"Aucune facture à payer. Le fichier n'a pas été généré.\n\n" + sortie
            self.write(cr, uid, ids, {'aff_bouton_paiement': False})
            self.write(cr, uid, ids, {'fichier': ''})
        
        self.write(cr, uid, ids, {'sortie': sortie})
        
        return True

    
    def montantapayer_echeancier(self, cr, uid, res, facture, context=None):
        u"""calcule le montant à payer en fonction de l'échéancier de la facture"""
        
        # L'échéancier est installé par le module of_sales. On bloque le paiement en fonction des l'échéances si ce module n'est pas installé.
        if not 'acompte_line_ids' in facture._columns:
            raise osv.except_osv(('Erreur ! (#ED500)'), u"L'échéancier des factures est mis en place par le module of_sales qui n'est pas installé.\nVous devez installé ce module si vous désirez effectuer le paiement en fonction de l'échéancier.")
        
        result = 0
        date_aujourdhui = res[0].date_creation[0:10]
        
        if facture.residual: # montant acquitté = montant déjà payé d'après balance (total facture moins ce qui reste à payer)
            montant_acquitte = facture.amount_total - facture.residual
        else:
            montant_acquitte = 0
                
        # Si pas de ligne dans l'échéancier, on considère que la facture est à payer au comptant (échéance = date facture)
        if not facture.acompte_line_ids:
            if facture.date_invoice and date_aujourdhui >= facture.date_invoice: # Si date de facture existe et est avant la date d'échéance on doit payer le montant total
                if facture.residual:
                    result = facture.residual
                else:
                    result = facture.amount_total
            else: # La date de la facture est après aujourd'hui, rien à payer
                result = 0
        else:
            cumul_montant_echeance = 0
            # On parcourt les lignes de l'échéancier jusqu'à la date d'aujourd'hui pour déterminer le montant cumulé des échéances à ce jour.
            for echeance in facture.acompte_line_ids:
                if date_aujourdhui < echeance.date:
                    break
                cumul_montant_echeance = cumul_montant_echeance + echeance.montant
            
            result = cumul_montant_echeance - montant_acquitte
        
        if result < 0:
                result = 0
        return result
    
    
    def action_enregistre_paiements(self, cr, uid, ids, context=None):
        u"""Enregistre les paiements des factures suite à un paiement EDI"""
        if not isinstance(ids, list):
            ids = [ids]
        sortie = ""
        if not context:
            raise osv.except_osv(('Erreur ! (#ED303)'), u"Le serveur a été arrêté depuis que vous avez généré le fichier.\n\nAppuyer une nouvelle fois sur le bouton générer le fichier avant d'effectuer une nouvelle validation des paiements.")
        
        voucher_obj = self.pool.get('account.voucher')
        voucher_line_obj = self.pool.get('account.voucher.line')
        account_move_line_obj = self.pool['account.move.line']
        partner_obj = self.pool.get('res.partner')
        wf_service = netsvc.LocalService('workflow')
        res = self.browse(cr, uid, ids, context=context) # Données du wizard
        
        # On récupère les factures selectionnées
        invoice_obj = self.pool['account.invoice']
        liste_factures = invoice_obj.browse(cr, uid, context.get('active_ids', []), context)
        
        # On vérifie qu'il s'agit bien de factures ouvertes non payées 
        for facture in liste_factures:
            
            if res[0].type_montant_facture == "echeancier":
                montant_du = self.montantapayer_echeancier(cr, uid, res, facture, context)
            else:
                montant_du = facture.residual
            
            # On vérifie que le montant à payer en fonction de l'échéancier n'est pas nul, sinon passe à la facture suivante 
            if montant_du == 0:
                continue
            
            # On récupère la ligne d'écriture comptable liée à la facture
            move_line_id = account_move_line_obj.search(cr, uid, [('move_id', '=' , facture.move_id.id),('account_id', '=' , facture.account_id.id)], context=context)
            if not move_line_id:
                raise osv.except_osv(('Erreur ! (#ED305)'), u"Erreur pour récupérer la ligne d'écriture comptable liée à la facture du " + facture.date_invoice + u", client : " + facture.partner_id.name + u", montant restant à payer : " + str('%.2f' % montant_du).replace('.', ',') + u" euros.\n\nAucun paiement n'a été en conséquence validé.")
            # On enregistre le paiement (voucher)
            voucher_res = {
                'type': 'receipt',
                'partner_id': facture.partner_id.id,
                'account_id': res[0].mode_paiement_id.journal.default_debit_account_id.id,
                'company_id': res[0].mode_paiement_id.company_id.id,
                'currency_id': facture.currency_id.id,
                'date': res[0].date_remise,
                'amount': montant_du,
                'period_id': voucher_obj._get_period(cr, uid, context),
                'mode_id': res[0].mode_paiement_id.id
            }
            voucher_id = voucher_obj.create(cr, uid, voucher_res, context)
            
            if not voucher_id:
                raise osv.except_osv(('Erreur ! (#ED310)'), u"Erreur création du paiement pour la facture du " + facture.date_invoice + u", client : " + facture.partner_id.name + u", montant restant à payer : " + str('%.2f' % montant_du).replace('.', ',') + u" euros.\n\nAucun paiement n'a été en conséquence validé.")
            # On enregistre la ligne du paiement (voucher_line)
            voucher_line_res = {
                'voucher_id': voucher_id,
                'account_id': facture.account_id.id,
                'amount': montant_du,
                'amount_original': facture.amount_total,
                'name': facture.internal_number,
                'type': 'cr',
                'move_line_id': move_line_id[0],
                'reconcile': True
            }
            if not voucher_line_obj.create(cr, uid, voucher_line_res, context):
                raise osv.except_osv(('Erreur ! (#ED315)'), u"Erreur création du paiement pour la facture du " + facture.date_invoice + u", client : " + facture.partner_id.name + u", montant à payer : " + str('%.2f' % montant_du).replace('.', ',') + u" euros.\n\nAucun paiement n'a été en conséquence validé.")
            
            # On met le champ type de prélèvement SEPA de chaque client à récurent en cours si était à 1er prélèvement à venir
            if facture.partner_id.of_sepa_type_prev == "FRST":
                if not partner_obj.write(cr, uid, facture.partner_id.id, {'of_sepa_type_prev': 'RCUR'}):
                    raise osv.except_osv(('Erreur ! (#ED320)'), u"Erreur dans l'enregistrement du type de prélèvement SEPA pour : " + facture.partner_id.name + u".\n\nAucun paiement n'a été en conséquence validé.")
                
            # On valide la paiement
            wf_service.trg_validate(uid, 'account.voucher', voucher_id, 'proforma_voucher', cr)
        
        sortie = u"Le paiement des factures a été effectué.\nIl vous reste à transmettre le fichier à votre banque.\n\n-----------------------------------------------\n\n" + sortie
        temp = {'type_paiement': res[0].type_paiement,
                'date_creation': res[0].date_creation,
                'date_remise': res[0].date_remise,
                'date_echeance': res[0].date_echeance,
                'fichier_edi': base64.decodestring(res[0].fichier)
                }
        # On ajoute la date de valeur si renseignée dans le formulaire
        if res[0].date_valeur:
            temp['date_valeur'] = res[0].date_valeur
        
        # On enregistre les caractéristiques du paiement EDI (date, fichier généré, ...) objet of.paiement.edi 
        if not self.pool['of.paiement.edi'].create(cr, uid, temp, context):
            raise osv.except_osv(('Erreur ! (#ED325)'), u"Erreur lors de l'enregistrement du paiement pour la facture du " + facture.date_invoice + u", client : " + facture.partner_id.name + u", montant à payer : " + str('%.2f' % montant_du).replace('.', ',') + u" euros.\n\nAucun paiement n'a été en conséquence validé.")
        if res[0].sortie:   # On récupère la sortie d'avant si elle existe
            sortie = sortie + res[0].sortie
        self.write(cr, uid, ids, {'sortie': sortie})
        self.write(cr, uid, ids, {'aff_bouton_paiement': False})
        self.write(cr, uid, ids, {'aff_bouton_genere_fich': False})
        return {
            'type': 'ir.actions.act_window',
            'res_id': ids[0],
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'wizard.paiement.edi',
            'context' : context,
            'target': 'new',
        }
    
    def chaine2ascii_taille_fixe_maj(self, chaine, longueur):
        u""" (pour LCR) Retourne une chaine en majuscule sans accent et ponctuation autre que ().,/+-:*espace et tronquée ou complétée à (longueur) caractères"""
        if not chaine or not longueur or longueur < 1:
            return False
        chaine = unicodedata.normalize('NFKD', chaine).encode('ascii','ignore')
        #chaine = chaine.replace("'", " ")   # apostrophe par espace
        chaine = re.sub(r'[^0-9A-Za-z\(\)\ \.\,\/\+\-\:\*]', ' ', chaine)
        chaine = chaine[:longueur]
        return chaine.upper().ljust(longueur)

    def chaine2ascii_taillemax(self, chaine, longueur):
        u""" (pour SEPA) Retourne une chaine sans accent et ponctuation autre que /-?:().,‟espace et tronquée à (longueur) caractères"""
        if not chaine or not longueur or longueur < 1:
            return False
        chaine = unicodedata.normalize('NFKD', chaine).encode('ascii','ignore')
        chaine = re.sub(r'[^0-9A-Za-z\(\)\ \.\,\/\?\-\:]', ' ', chaine)
        return chaine[:longueur]
