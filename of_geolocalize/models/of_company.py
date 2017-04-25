# -*- coding: utf-8 -*-

#TODO: change the URL to use a local version of Nominatim 

# requires a gis database

import json
import urllib

from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError

# get the lat and lng out of an address using Nominatim
def addr2LatLng(addr):
    url = 'https://nominatim.openstreetmap.org/search?format=json&q='
    url += urllib.quote(addr.encode('utf8'))
    
    try:
        result = json.load(urllib.urlopen(url))
    except Exception as e:
        raise UserError(_('Cannot contact geolocation servers. Please make sure that your Internet connection is up and running (%s).') % e)

    if result == []:
        return None

    try:
        #json format
        latLng = [result[0]['lat'],result[0]['lon']]
        return latLng
    except (KeyError, ValueError):
        return None
    
def geo_query_addr(street=None, street2=None, zip=None, city=None, state=None, country=None):
    if country and ',' in country and (country.endswith(' of') or country.endswith(' of the')):
        # put country qualifier in front, otherwise GMap gives wrong results,
        # e.g. 'Congo, Democratic Republic of the' => 'Democratic Republic of the Congo'
        country = '{1} {0}'.format(*country.split(',', 1))
    return tools.ustr(', '.join(filter(None, [street,
                                              street2,
                                              ("%s %s" % (zip or '', city or '')).strip(),
                                              state,
                                              country])))

class ResCompany(models.Model):
    _inherit = "res.company"
    
    geo_lat = fields.Float(string='Geo Lat', digits=(16, 5))
    geo_lng = fields.Float(string='Geo Lng', digits=(16, 5))
    date_last_localization = fields.Date(string='Geolocation Date')
    date_last_partner_localization = fields.Date(string='Partner Geolocation Date')

    # localize every partner of current company
    @api.multi
    def geo_code_partners(self):
        partner_obj = self.env["res.partner"] # on récupère tous les partners
        for company_id in self._ids:
            partners = partner_obj.search([('company_id', 'child_of', company_id)]) #critère de selection : cette company est associée
            partners.geo_code()
        self.write({'date_last_partner_localization': fields.Date.context_today(self)})
                
    @api.multi
    def geo_code(self):
        # We need country names in English below
        for company in self.with_context(lang='en_US'):
            result = addr2LatLng(geo_query_addr(street=company.street,
                                                   street2=company.street2,
                                                zip=company.zip,
                                                city=company.city,
                                                state=company.state_id.name,
                                                country=company.country_id.name))
            if result is None:
                result = addr2LatLng(geo_query_addr(
                    city=company.city,
                    state=company.state_id.name,
                    country=company.country_id.name
                ))

            if result:
                company.write({
                    'geo_lat': result[0],
                    'geo_lng': result[1],
                    'date_last_localization': fields.Date.context_today(company)
                })
        return True

    #will compute the lat and lng when a company is created
    #currently geocode even if there is no address whenn the company is created, should not be this way
    @api.model
    def create(self, vals):
        company = super(ResCompany,self).create(vals)
        company.geo_code()
        return company

    #will recompute the lat and lng when a partner's address is modified
    @api.multi
    def write(self, vals):
        super(ResCompany,self).write(vals)
        for key in vals:
            if key in ('street', 'street2', 'city', 'state_id', 'country_id', 'zip'):
                self.geo_code()
                break
        return True
