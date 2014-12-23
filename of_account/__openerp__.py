# -*- encoding: utf-8 -*-
{
    "name" : "OpenFire / Comptabilité",
    "version" : "0.9",
    "author" : "OpenFire",
    "website" : "www.openfire.fr",
    "category" : "Generic Modules/Sales & Purchases",
    "description": """
Module de comptabilité OpenFire.
======================================

Ce module apporte une personnalisation de la comptabilité:
- Ajout d'un code vendeur dans les parametres des utilisateurs
- Refonte des impressions de journaux
- Recherche Facture de date à date
- Impression Liste Factures
- Fonctions pratiques pour la saisie des écritures comptables et relevés bancaires
- Fusionner les factures fournisseur brouillon sous condition, sans fusionner les lignes
- Vue Tree Journal change selon la configuration de vues journal
- Option facultative d'impression du détail des comptes client dans le rapport Balance des comptes
- Comptabilisation automatique de la pièce comptable à la confirmation du paiement client
- La centralisation des écritures ne se fait qu'en débit ou crédit (valeur positive) lors d'un report à nouveau
- Message d'erreur lors d'une tentative de report à nouveau d'une années avec pièces comptables non comptabilisées
- Message d'avertissement avec checkbox avant de confirmer une clôture d'exercice
- Configuration les préfixes comptes pour les types de compte
- Type de compte: Enlever la traduction du champ Type de compte
- Prendre seulement les périodes normaux pour les paiements
- Utilisation de la sequence pour les codes de taxe

Notes:
- Le champ de recherche des écritures comptables est paramétré avec les dates de l'année fiscale courante à chaque mise à jour du module.
    Il faut donc faire cette mise à jour à chaque début d'année fiscale
""",
    "depends" : ['account', 'account_voucher'],
    "init_xml" : [ ],
    "demo_xml" : [ ],
    'update_xml': [
        'security/ir.model.access.csv',
        'of_account_view.xml',
        'wizard/account_fiscalyear_close_state.xml',
        'wizard/wizard_invoice_group_view.xml',
    ],
    "installable": True,
    'active': False,
}
# vim:expandtab:smartindent:tabstop=4:sorderttabstop=4:shiftwidth=4:
