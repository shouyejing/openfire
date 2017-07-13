# -*- coding: utf-8 -*-

from odoo import api, fields, models
import time
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT

class OFCrmOpportActivityResult(models.TransientModel):
    _name = 'of.crm.opport.activity.result'
    _description = u"Compte rendu d'activité"
    # adapté de crm lead lost

    activity_result = fields.Text('Compte rendu')

    def _get_values(self):
        values = {
            'activity_result': self.activity_result,
            'is_done': True,
            'date_done': time.strftime(DEFAULT_SERVER_DATE_FORMAT),
            }

        return values

    @api.multi
    def action_result_apply(self):
        opport_activity = self.env['of.crm.opport.activity'].browse(self.env.context.get('active_ids'))
        opport_activity.write(self.get_values())
        return opport_activity.add_report_to_opportunity_description()
