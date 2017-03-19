"""Import tasks for the Cambridge Photometric Calibration Server."""
import json
import os
from collections import OrderedDict

from astrocats.catalog.utils import is_number, pbar, round_sig, uniq_cdl

from ..supernova import SUPERNOVA


def do_cpcs(catalog):
    """Import data from CPCS."""
    task_str = catalog.get_current_task_str()
    cpcs_url = ('http://gsaweb.ast.cam.ac.uk/'
                'followup/list_of_alerts?format=json&num=100000&'
                'published=1&observed_only=1'
                '&hashtag=JG_530ad9462a0b8785bfb385614bf178c6')
    jsontxt = catalog.load_url(cpcs_url, os.path.join(
        catalog.get_current_task_repo(), 'CPCS/index.json'))
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
        white_list = [
            'GAIA', 'OGLE', 'ASASSN', 'MASTER', 'OTJ', 'PS1', 'IPTF', 'CSS']
        if True in [xx in name.upper() for xx in white_list]:
            name = name.replace('Verif', '').replace('_', ' ')
            if 'ASASSN' in name and name[6] != '-':
                name = 'ASASSN-' + name[6:].lower()
            if 'MASTEROTJ' in name:
                name = name.replace('MASTEROTJ', 'MASTER OT J')
            if 'OTJ' in name:
                name = name.replace('OTJ', 'MASTER OT J')
            if name.upper().startswith('IPTF'):
                name = 'iPTF' + name[4:].lower()
            if name.upper().startswith('PS1'):
                name = 'PS1' + name[3:].lower()
            # Only add events that are classified as SN.
            if not catalog.entry_exists(name):
                continue
            oldname = name
            name = catalog.add_entry(name)
        else:
            continue

        sec_source = catalog.entries[name].add_source(
            name='Cambridge Photometric Calibration Server',
            url='http://gsaweb.ast.cam.ac.uk/followup/',
            secondary=True)
        catalog.entries[name].add_quantity(SUPERNOVA.ALIAS, oldname,
                                           sec_source)
        unit_deg = 'floatdegrees'
        catalog.entries[name].add_quantity(
            SUPERNOVA.RA,
            str(alertindex[ii][SUPERNOVA.RA]),
            sec_source,
            u_value=unit_deg)
        catalog.entries[name].add_quantity(
            SUPERNOVA.DEC,
            str(alertindex[ii][SUPERNOVA.DEC]),
            sec_source,
            u_value=unit_deg)

        alerturl = ('http://gsaweb.ast.cam.ac.uk/'
                    'followup/get_alert_lc_data?alert_id=' + str(ai))
        source = catalog.entries[name].add_source(
            name='CPCS Alert ' + str(ai), url=alerturl)
        fname = os.path.join(catalog.get_current_task_repo(),
                             'CPCS/alert-') + str(ai).zfill(2) + '.json'

        jsonstr = catalog.load_url(
            alerturl + '&hashtag=JG_530ad9462a0b8785bfb385614bf178c6', fname)

        try:
            cpcsalert = json.loads(jsonstr)
        except Exception:
            catalog.log.warning('Mangled CPCS data for alert {}.'.format(ai))
            continue

        mjds = [round_sig(xx, sig=9) for xx in cpcsalert['mjd']]
        mags = [round_sig(xx, sig=6) for xx in cpcsalert['mag']]
        errs = [round_sig(
            xx, sig=6) if (is_number(xx) and float(xx) > 0.0) else ''
            for xx in cpcsalert['magerr']]
        bnds = cpcsalert['filter']
        obs = cpcsalert['observatory']
        for mi, mjd in enumerate(mjds):
            catalog.entries[name].add_photometry(
                time=mjd,
                u_time='MJD',
                magnitude=mags[mi],
                e_magnitude=errs[mi],
                band=bnds[mi],
                observatory=obs[mi],
                source=uniq_cdl([source, sec_source]))
        if catalog.args.update:
            catalog.journal_entries()
        if catalog.args.travis and ii >= catalog.TRAVIS_QUERY_LIMIT:
            break

    catalog.journal_entries()
    return
