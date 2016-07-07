"""Import tasks for the Cambridge Photometric Calibration Server.
"""
import json
import os
from collections import OrderedDict

import requests

from astrocats.catalog.utils import is_number, pbar, round_sig, uniq_cdl


def do_cpcs(catalog):
    task_str = catalog.get_current_task_str()
    cpcs_url = ('http://gsaweb.ast.cam.ac.uk/'
                'followup/list_of_alerts?format=json&num=100000&'
                'published=1&observed_only=1'
                '&hashtag=JG_530ad9462a0b8785bfb385614bf178c6')
    jsontxt = catalog.load_cached_url(
        cpcs_url, os.path.join(catalog.get_current_task_repo(),
                               'CPCS/index.json'))
    if not jsontxt:
        return
    alertindex = json.loads(jsontxt, object_pairs_hook=OrderedDict)
    ids = [xx['id'] for xx in alertindex]
    for ii, ai in enumerate(pbar(ids, task_str)):
        name = alertindex[ii]['ivorn'].split('/')[-1].strip()
        # Skip aa few weird entries
        if name == 'ASASSNli':
            continue
        # Just use aa whitelist for now since naming seems inconsistent
        white_list = ['GAIA', 'OGLE', 'ASASSN', 'MASTER', 'OTJ', 'PS1', 'IPTF']
        if True in [xx in name.upper() for xx in white_list]:
            name = name.replace('Verif', '').replace('_', ' ')
            if 'ASASSN' in name and name[6] != '-':
                name = 'ASASSN-' + name[6:]
            if 'MASTEROTJ' in name:
                name = name.replace('MASTEROTJ', 'MASTER OT J')
            if 'OTJ' in name:
                name = name.replace('OTJ', 'MASTER OT J')
            if name.upper().startswith('IPTF'):
                name = 'iPTF' + name[4:]
            # Only add events that are classified as SN.
            if catalog.entry_exists(name):
                continue
            oldname = name
            name = catalog.add_entry(name)
        else:
            continue

        sec_source = catalog.entries[name].add_source(
            name='Cambridge Photometric Calibration Server',
            url='http://gsaweb.ast.cam.ac.uk/followup/', secondary=True)
        catalog.entries[name].add_quantity('alias', oldname, sec_source)
        unit_deg = 'floatdegrees'
        catalog.entries[name].add_quantity(
            'ra', str(alertindex[ii]['ra']), sec_source, unit=unit_deg)
        catalog.entries[name].add_quantity('dec', str(
            alertindex[ii]['dec']), sec_source, unit=unit_deg)

        alerturl = ('http://gsaweb.ast.cam.ac.uk/'
                    'followup/get_alert_lc_data?alert_id=' +
                    str(ai))
        source = catalog.entries[name].add_source(
            name='CPCS Alert ' + str(ai), url=alerturl)
        fname = os.path.join(catalog.get_current_task_repo(),
                             'CPCS/alert-') + str(ai).zfill(2) + '.json'
        if (catalog.current_task.load_archive(catalog.args) and
                os.path.isfile(fname)):
            with open(fname, 'r') as ff:
                jsonstr = ff.read()
        else:
            session = requests.Session()
            response = session.get(
                alerturl + '&hashtag=JG_530ad9462a0b8785bfb385614bf178c6')
            with open(fname, 'w') as ff:
                jsonstr = response.text
                ff.write(jsonstr)

        try:
            cpcsalert = json.loads(jsonstr)
        except:
            continue

        mjds = [round_sig(xx, sig=9) for xx in cpcsalert['mjd']]
        mags = [round_sig(xx, sig=6) for xx in cpcsalert['mag']]
        errs = [round_sig(xx, sig=6) if (is_number(xx) and float(xx) > 0.0)
                else '' for xx in cpcsalert['magerr']]
        bnds = cpcsalert['filter']
        obs = cpcsalert['observatory']
        for mi, mjd in enumerate(mjds):
            catalog.entries[name].add_photometry(
                time=mjd, magnitude=mags[mi], e_magnitude=errs[mi],
                band=bnds[mi], observatory=obs[mi],
                source=uniq_cdl([source, sec_source]))
        if catalog.args.update:
            catalog.journal_entries()

    catalog.journal_entries()
    return
