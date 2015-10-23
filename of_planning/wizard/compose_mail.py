# -*- encoding: utf-8 -*-

from openerp.osv import fields, osv
from datetime import datetime

class compose_mail(osv.TransientModel):
    _inherit = 'of.compose.mail'

    def _get_objects(self, cr, uid, o, data, context):
        result = super(compose_mail,self)._get_objects(cr, uid, o, data, context)
        if o._model._name == 'of.planning.pose':
            result.update({
                'poses'   : [o],
                'address' : result['address_pose']
            })
        else:
            # poses_liees ne sera defini que dans of_sales, mais getattr gere l'exception si le module n'est pas installe
            result['poses'] = getattr(o, 'poses_liees', [])
        return result

    def _get_dict_values(self, cr, uid, data, obj, context):
        result = super(compose_mail,self)._get_dict_values(cr, uid, data, obj, context)

        poses = context['objects'].get('poses',[])
        equipes_pose = []
        dates_pose = []

        for pose in poses:
            equipes_pose.append(pose.poseur_id.name)
            date_pose = pose.date
            try:
                if len(date_pose) > 19:
                    date_pose = date_pose[:19]
            except: pass
            date_pose = datetime.strptime(date_pose, '%Y-%m-%d %H:%M:%S')
            timezone_name = self.pool.get('res.users').read(cr, uid, uid, ['context_tz'])['context_tz'] or 'Europe/Paris'
            d_pose_local = str(fields.datetime.context_timestamp(cr, uid, date_pose, context={'tz': timezone_name}))
            a = d_pose_local[0:4]
            m = d_pose_local[5:7]
            j = d_pose_local[8:10]
            h = d_pose_local[11:13]
            n = d_pose_local[14:16]
            dates_pose.append(u"%s/%s/%s à %s:%s" % (j, m, a, h, n))

        tache_product_ttc = ''
        duree_pose = ''
        if poses:
            pose = poses[0]
            h = int(pose.duree)
            m = 60 * (pose.duree - h)
            duree_pose = "%02d:%02d" % (h,m)

            if pose.tache.product_id:
                tache_product_ht = pose.tache.product_id.list_pvht or 0.0
                fpos = False
                partner = context['objects']['partner']
                if partner:
                    fpos = partner.property_account_position or False
                    if not fpos:
                        fpos = partner.company_id and partner.company_id.fiscal_position_sale or False
                if fpos:
                    tache_product_tax = 0.0
                    for tax in fpos.tax_ids:
                        tache_product_tax += tax.tax_src_id.amount

                    lang_obj = self.pool['res.lang']
                    lang_code = context.get('lang', context['objects']['partner'].lang)
                    lang_id = lang_obj.search(cr, uid, [('code','=', lang_code)])[0]
                    tache_product_ttc = lang_obj.formatLang(cr, uid, lang_id, round(tache_product_ht * (1.0 + tache_product_tax), 2))

        result.update({
            'date_pose'        : dates_pose and dates_pose[0] or ' ',
            'date_pose_date'   : dates_pose and dates_pose[0].split()[0] or ' ',
            'equipe_pose'      : equipes_pose and equipes_pose[0] or '',
            'equipe_poses'     : "\n".join(equipes_pose),
            'date_poses'       : "\n".join(dates_pose),
            'duree_pose'       : duree_pose,
            'tache_pose'       : poses and pose.tache and pose.tache.name or '',
            'tache_product_ttc': tache_product_ttc,
        })
        return result

    def _get_model_action_dict(self):
        res = super(compose_mail, self)._get_model_action_dict()
        res['of.planning.pose'] = 'of_planning.courriers_pose'
        return res
