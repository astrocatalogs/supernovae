"""
"""
import statistics
import warnings
from math import hypot, log10, pi, sqrt

from astropy import units as un
from astropy.coordinates import SkyCoord as coord
from astropy.cosmology import Planck15 as cosmo
from astropy.cosmology import z_at_value

from astrocats.catalog.utils import (get_sig_digits, is_number, pbar,
                                     pretty_num, tprint, uniq_cdl)
from astrocats.supernovae.constants import CLIGHT, KM, PREF_KINDS
from cdecimal import Decimal


def do_derivations(catalog):
    task_str = catalog.get_current_task_str()
    # Calculate some columns based on imported data, sanitize some fields
    for oname in pbar(catalog.entries, task_str):
        name = catalog.add_entry(oname)

        aliases = catalog.entries[name].get_aliases()
        catalog.entries[name].set_first_max_light()

        if 'discoverdate' not in catalog.entries[name]:
            prefixes = ['MLS', 'SSS', 'CSS', 'GRB ']
            for alias in aliases:
                for prefix in prefixes:
                    if (alias.startswith(prefix) and
                            is_number(alias.replace(prefix, '')[:2])):
                        discoverdate = ('/'.
                                        join(['20' +
                                              alias.replace(prefix, '')[:2],
                                              alias.replace(prefix, '')[2:4],
                                              alias.replace(prefix, '')[4:6]]))
                        if catalog.args.verbose:
                            tprint(
                                'Added discoverdate from name [' +
                                alias + ']: ' + discoverdate)
                        source = catalog.entries[name].add_self_source()
                        catalog.entries[name].add_quantity(
                            'discoverdate', discoverdate, source, derived=True)
                        break
                if 'discoverdate' in catalog.entries[name]:
                    break
        if 'discoverdate' not in catalog.entries[name]:
            prefixes = ['ASASSN-', 'PS1-', 'PS1', 'PS', 'iPTF', 'PTF', 'SCP-',
                        'SNLS-', 'SPIRITS', 'LSQ', 'DES', 'SNHiTS', 'Gaia',
                        'GND', 'GNW', 'GSD', 'GSW', 'EGS', 'COS', 'OGLE',
                        'HST']
            for alias in aliases:
                for prefix in prefixes:
                    if (alias.startswith(prefix) and
                            is_number(alias.replace(prefix, '')[:2]) and
                            is_number(alias.replace(prefix, '')[:1])):
                        discoverdate = '20' + alias.replace(prefix, '')[:2]
                        if catalog.args.verbose:
                            tprint(
                                'Added discoverdate from name [' +
                                alias + ']: ' + discoverdate)
                        source = catalog.entries[name].add_self_source()
                        catalog.entries[name].add_quantity(
                            'discoverdate', discoverdate, source, derived=True)
                        break
                if 'discoverdate' in catalog.entries[name]:
                    break
        if 'discoverdate' not in catalog.entries[name]:
            prefixes = ['SNF']
            for alias in aliases:
                for prefix in prefixes:
                    if (alias.startswith(prefix) and
                            is_number(alias.replace(prefix, '')[:4])):
                        discoverdate = ('/'
                                        .join(
                                            [alias.replace(prefix, '')[:4],
                                             alias.replace(prefix, '')[4:6],
                                             alias.replace(prefix, '')[6:8]]))
                        if catalog.args.verbose:
                            tprint(
                                'Added discoverdate from name [' +
                                alias + ']: ' + discoverdate)
                        source = catalog.entries[name].add_self_source()
                        catalog.entries[name].add_quantity(
                            'discoverdate', discoverdate, source, derived=True)
                        break
                if 'discoverdate' in catalog.entries[name]:
                    break
        if 'discoverdate' not in catalog.entries[name]:
            prefixes = ['PTFS', 'SNSDF']
            for alias in aliases:
                for prefix in prefixes:
                    if (alias.startswith(prefix) and
                            is_number(alias.replace(prefix, '')[:2])):
                        discoverdate = ('/'
                                        .join(
                                            ['20' +
                                             alias.replace(prefix, '')[:2],
                                             alias.replace(prefix, '')[2:4]]))
                        if catalog.args.verbose:
                            tprint(
                                'Added discoverdate from name [' +
                                alias + ']: ' + discoverdate)
                        source = catalog.entries[name].add_self_source()
                        catalog.entries[name].add_quantity(
                            'discoverdate', discoverdate, source, derived=True)
                        break
                if 'discoverdate' in catalog.entries[name]:
                    break
        if 'discoverdate' not in catalog.entries[name]:
            prefixes = ['AT', 'SN', 'OGLE-', 'SM ', 'KSN-']
            for alias in aliases:
                for prefix in prefixes:
                    if (alias.startswith(prefix) and
                            is_number(alias.replace(prefix, '')[:4]) and
                            '.' not in alias.replace(prefix, '')[:4]):
                        discoverdate = alias.replace(prefix, '')[:4]
                        if catalog.args.verbose:
                            tprint(
                                'Added discoverdate from name [' +
                                alias + ']: ' + discoverdate)
                        source = catalog.entries[name].add_self_source()
                        catalog.entries[name].add_quantity(
                            'discoverdate', discoverdate, source, derived=True)
                        break
                if 'discoverdate' in catalog.entries[name]:
                    break

        if ('ra' not in catalog.entries[name] or
                'dec' not in catalog.entries[name]):
            prefixes = ['PSN J', 'MASJ', 'CSS', 'SSS', 'MASTER OT J', 'HST J',
                        'TCP J', 'MACS J', '2MASS J', 'EQ J', 'CRTS J',
                        'SMT J']
            for alias in aliases:
                for prefix in prefixes:
                    if (alias.startswith(prefix) and
                            is_number(alias.replace(prefix, '')[:6])):
                        noprefix = alias.split(
                            ':')[-1].replace(prefix, '').replace('.', '')
                        decsign = '+' if '+' in noprefix else '-'
                        noprefix = noprefix.replace('+', '|').replace('-', '|')
                        nops = noprefix.split('|')
                        if len(nops) < 2:
                            continue
                        rastr = nops[0]
                        decstr = nops[1]
                        ra = ':'.join([rastr[:2], rastr[2:4], rastr[4:6]]) + \
                            ('.' + rastr[6:] if len(rastr) > 6 else '')
                        dec = (decsign + ':'
                               .join([decstr[:2], decstr[2:4], decstr[4:6]]) +
                               ('.' + decstr[6:] if len(decstr) > 6 else ''))
                        if catalog.args.verbose:
                            tprint('Added ra/dec from name: ' + ra + ' ' + dec)
                        source = catalog.entries[name].add_self_source()
                        catalog.entries[name].add_quantity(
                            'ra', ra, source, derived=True)
                        catalog.entries[name].add_quantity(
                            'dec', dec, source, derived=True)
                        break
                if 'ra' in catalog.entries[name]:
                    break

        no_host = ('host' not in catalog.entries[name] or
                   not any([x['value'] == 'Milky Way' for x in
                            catalog.entries[name]['host']]))
        if ('ra' in catalog.entries[name] and
                'dec' in catalog.entries[name] and no_host):
            from astroquery.irsa_dust import IrsaDust
            if name not in catalog.extinctions_dict:
                try:
                    ra_dec = catalog.entries[name]['ra'][0]['value'] + \
                        " " + catalog.entries[name]['dec'][0]['value']
                    result = IrsaDust.get_query_table(ra_dec, section='ebv')
                except (KeyboardInterrupt, SystemExit):
                    raise
                except:
                    warnings.warn("Coordinate lookup for " +
                                  name + " failed in IRSA.")
                else:
                    ebv = result['ext SandF mean'][0]
                    ebverr = result['ext SandF std'][0]
                    catalog.extinctions_dict[name] = [ebv, ebverr]
            if name in catalog.extinctions_dict:
                sources = uniq_cdl(
                    [catalog.entries[name].add_self_source(),
                     catalog.entries[name]
                     .add_source(bibcode='2011ApJ...737..103S')])
                (catalog.entries[name]
                 .add_quantity('ebv',
                               str(catalog
                                   .extinctions_dict[name][0]),
                               sources,
                               error=str(catalog
                                         .extinctions_dict[name][1]),
                               derived=True))
        if (('host' in catalog.entries[name] and
             ('hostra' not in catalog.entries[name] or
              'hostdec' not in catalog.entries[name]))):
            for host in catalog.entries[name]['host']:
                alias = host['value']
                if ' J' in alias and is_number(alias.split(' J')[-1][:6]):
                    noprefix = alias.split(
                        ' J')[-1].split(':')[-1].replace('.', '')
                    decsign = '+' if '+' in noprefix else '-'
                    noprefix = noprefix.replace('+', '|').replace('-', '|')
                    nops = noprefix.split('|')
                    if len(nops) < 2:
                        continue
                    rastr = nops[0]
                    decstr = nops[1]
                    hostra = (':'.join([rastr[:2], rastr[2:4], rastr[4:6]]) +
                              ('.' + rastr[6:] if len(rastr) > 6 else ''))
                    hostdec = decsign + ':'.join([decstr[:2], decstr[2:4],
                                                  decstr[4:6]]) + (
                        '.' + decstr[6:] if len(decstr) > 6 else '')
                    if catalog.args.verbose:
                        tprint('Added hostra/hostdec from name: ' +
                               hostra + ' ' + hostdec)
                    source = catalog.entries[name].add_self_source()
                    catalog.entries[name].add_quantity(
                        'hostra', hostra, source, derived=True)
                    catalog.entries[name].add_quantity(
                        'hostdec', hostdec, source, derived=True)
                    break
                if 'hostra' in catalog.entries[name]:
                    break

        if ('redshift' not in catalog.entries[name] and
                'velocity' in catalog.entries[name]):
            # Find the "best" velocity to use for this
            bestsig = 0
            for hv in catalog.entries[name]['velocity']:
                sig = get_sig_digits(hv['value'])
                if sig > bestsig:
                    besthv = hv['value']
                    bestsrc = hv['source']
                    bestsig = sig
            if bestsig > 0 and is_number(besthv):
                voc = float(besthv) * 1.e5 / CLIGHT
                source = catalog.entries[name].add_self_source()
                sources = uniq_cdl([source] + bestsrc.split(','))
                (catalog.entries[name]
                 .add_quantity('redshift',
                               pretty_num(sqrt((1. + voc) / (1. - voc)) - 1.,
                                          sig=bestsig),
                               sources, kind='heliocentric',
                               derived=True))
        if ('redshift' not in catalog.entries[name] and
                len(catalog.nedd_dict) > 0 and
                'host' in catalog.entries[name]):
            reference = "NED-D"
            refurl = "http://ned.ipac.caltech.edu/Library/Distances/"
            for host in catalog.entries[name]['host']:
                if host['value'] in catalog.nedd_dict:
                    source = catalog.entries[name].add_source(
                        bibcode='2015arXiv150201589P')
                    secondarysource = catalog.entries[name].add_source(
                        name=reference, url=refurl, secondary=True)
                    meddist = statistics.median(
                        catalog.nedd_dict[host['value']])
                    redz = z_at_value(
                        cosmo.comoving_distance, float(meddist) * un.Mpc)
                    redshift = pretty_num(
                        redz, sig=get_sig_digits(str(meddist)))
                    catalog.entries[name].add_quantity(
                        name, 'redshift', redshift,
                        uniq_cdl([source, secondarysource]),
                        kind='host', derived=True)
        if ('maxabsmag' not in catalog.entries[name] and
                'maxappmag' in catalog.entries[name] and
                'lumdist' in catalog.entries[name]):
            # Find the "best" distance to use for this
            bestsig = 0
            for ld in catalog.entries[name]['lumdist']:
                sig = get_sig_digits(ld['value'])
                if sig > bestsig:
                    bestld = ld['value']
                    bestsrc = ld['source']
                    bestsig = sig
            if bestsig > 0 and is_number(bestld) and float(bestld) > 0.:
                source = catalog.entries[name].add_self_source()
                sources = uniq_cdl([source] + bestsrc.split(','))
                # FIX: what's happening here?!
                pnum = (float(catalog.entries[name]['maxappmag'][0]['value']) -
                        5.0 * (log10(float(bestld) * 1.0e6) - 1.0))
                pnum = pretty_num(pnum, sig=bestsig)
                catalog.entries[name].add_quantity(
                    'maxabsmag', pnum, sources, derived=True)
        if 'redshift' in catalog.entries[name]:
            # Find the "best" redshift to use for this
            bestz, bestkind, bestsig, bestsrc = catalog.entries[
                name].get_best_redshift()
            if bestsig > 0:
                bestz = float(bestz)
                if 'velocity' not in catalog.entries[name]:
                    source = catalog.entries[name].add_self_source()
                    # FIX: what's happening here?!
                    pnum = CLIGHT / KM * \
                        ((bestz + 1.)**2. - 1.) / ((bestz + 1.)**2. + 1.)
                    pnum = pretty_num(pnum, sig=bestsig)
                    catalog.entries[name].add_quantity(
                        'velocity', pnum, source, kind=PREF_KINDS[bestkind])
                if bestz > 0.:
                    from astropy.cosmology import Planck15 as cosmo
                    if 'lumdist' not in catalog.entries[name]:
                        dl = cosmo.luminosity_distance(bestz)
                        sources = [
                            catalog.entries[name].add_self_source(),
                            catalog.entries[name]
                            .add_source(bibcode='2015arXiv150201589P')]
                        sources = uniq_cdl(sources + bestsrc.split(','))
                        catalog.entries[name].add_quantity(
                            'lumdist', pretty_num(dl.value, sig=bestsig),
                            sources, kind=PREF_KINDS[bestkind],
                            derived=True)
                        if ('maxabsmag' not in catalog.entries[name] and
                                'maxappmag' in catalog.entries[name]):
                            source = catalog.entries[name].add_self_source()
                            pnum = pretty_num(
                                float(catalog.entries[name]['maxappmag'][0][
                                    'value']) -
                                5.0 * (log10(dl.to('pc').value) - 1.0),
                                sig=bestsig)
                            catalog.entries[name].add_quantity(
                                'maxabsmag', pnum, sources, derived=True)
                    if 'comovingdist' not in catalog.entries[name]:
                        cd = cosmo.comoving_distance(bestz)
                        sources = [
                            catalog.entries[name].add_self_source(),
                            catalog.entries[name]
                            .add_source(bibcode='2015arXiv150201589P')]
                        sources = uniq_cdl(sources + bestsrc.split(','))
                        catalog.entries[name].add_quantity(
                            'comovingdist', pretty_num(cd.value, sig=bestsig),
                            sources, derived=True)
        if all([x in catalog.entries[name] for x in
                ['ra', 'dec', 'hostra', 'hostdec']]):
            # For now just using first coordinates that appear in entry
            try:
                c1 = coord(
                    ra=catalog.entries[name]['ra'][0][
                        'value'], dec=catalog.entries[name]['dec'][0]['value'],
                    unit=(un.hourangle, un.deg))
                c2 = coord(
                    ra=catalog.entries[name]['hostra'][0]['value'],
                    dec=catalog.entries[name]['hostdec'][0]['value'],
                    unit=(un.hourangle, un.deg))
            except (KeyboardInterrupt, SystemExit):
                raise
            except:
                pass
            else:
                sources = uniq_cdl(
                    [catalog.entries[name].add_self_source()] +
                    catalog.entries[name]['ra'][0]['source'].split(',') +
                    catalog.entries[name]['dec'][0]['source'].split(',') +
                    catalog.entries[name]['hostra'][0]['source'].split(',') +
                    catalog.entries[name]['hostdec'][0]['source'].split(','))
                if 'hostoffsetang' not in catalog.entries[name]:
                    hosa = Decimal(hypot(c1.ra.degree - c2.ra.degree,
                                         c1.dec.degree - c2.dec.degree))
                    hosa = pretty_num(hosa * Decimal(3600.))
                    catalog.entries[name].add_quantity(
                        'hostoffsetang', hosa, sources,
                        derived=True, unit='arcseconds')
                if ('comovingdist' in catalog.entries[name] and
                        'redshift' in catalog.entries[name] and
                        'hostoffsetdist' not in catalog.entries[name]):
                    offsetsig = get_sig_digits(
                        catalog.entries[name]['hostoffsetang'][0]['value'])
                    sources = uniq_cdl(sources.split(',') +
                                       (catalog.entries[name]['comovingdist']
                                        [0]['source']).split(',') +
                                       (catalog.entries[name]['redshift']
                                        [0]['source']).split(','))
                    (catalog.entries[name]
                     .add_quantity('hostoffsetdist',
                                   pretty_num(
                                       float(catalog.entries[name][
                                           'hostoffsetang']
                                           [0]['value']) /
                                       3600. * (pi / 180.) *
                                       float(catalog.entries[name][
                                           'comovingdist']
                                           [0]['value']) *
                                       1000. / (1.0 +
                                                float(catalog.entries[name][
                                                    'redshift']
                                                    [0]['value'])),
                                       sig=offsetsig), sources))

        catalog.journal_entries()

    return
