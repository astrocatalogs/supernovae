"""Cleanup catalog before final write to disk."""
import re
import statistics
import warnings
from decimal import Decimal
from math import log10, pi, sqrt

from astrocats.catalog.quantity import QUANTITY
from astrocats.catalog.utils import (get_sig_digits, is_number, pbar,
                                     pretty_num, tprint, uniq_cdl)
from astropy import units as un
from astropy.coordinates import SkyCoord as coord
from astropy.cosmology import Planck15 as cosmo
from astropy.cosmology import z_at_value

from ..constants import CLIGHT, KM
from ..supernova import SUPERNOVA


def do_cleanup(catalog):
    """Cleanup catalog after importing all data."""
    task_str = catalog.get_current_task_str()

    # Set preferred names, calculate some columns based on imported data,
    # sanitize some fields
    keys = list(catalog.entries.keys())

    cleanupcnt = 0
    for oname in pbar(keys, task_str):
        # Some events may be merged in cleanup process, skip them if
        # non-existent.
        try:
            name = catalog.add_entry(oname)
        except Exception:
            catalog.log.warning(
                '"{}" was not found, suggests merge occurred in cleanup '
                'process.'.format(oname))
            continue

        # Set the preferred name, switching to that name if name changed.
        name = catalog.entries[name].set_preferred_name()

        aliases = catalog.entries[name].get_aliases()
        catalog.entries[name].purge_bandless_photometry()
        catalog.entries[name].set_first_max_light()

        if SUPERNOVA.DISCOVER_DATE not in catalog.entries[name]:
            prefixes = ['MLS', 'SSS', 'CSS', 'GRB ']
            for alias in aliases:
                for prefix in prefixes:
                    if (alias.startswith(prefix) and
                            is_number(alias.replace(prefix, '')[:2])):
                        discoverdate = ('/'.join([
                            '20' + alias.replace(prefix, '')[:2],
                            alias.replace(prefix, '')[2:4],
                            alias.replace(prefix, '')[4:6]
                        ]))
                        if catalog.args.verbose:
                            tprint('Added discoverdate from name [' + alias +
                                   ']: ' + discoverdate)
                        source = catalog.entries[name].add_self_source()
                        catalog.entries[name].add_quantity(
                            SUPERNOVA.DISCOVER_DATE,
                            discoverdate,
                            source,
                            derived=True)
                        break
                if SUPERNOVA.DISCOVER_DATE in catalog.entries[name]:
                    break
        if SUPERNOVA.DISCOVER_DATE not in catalog.entries[name]:
            prefixes = [
                'ASASSN-', 'PS1-', 'PS1', 'PS', 'iPTF', 'PTF', 'SCP-', 'SNLS-',
                'SPIRITS', 'LSQ', 'DES', 'SNHiTS', 'Gaia', 'GND', 'GNW', 'GSD',
                'GSW', 'EGS', 'COS', 'OGLE', 'HST'
            ]
            for alias in aliases:
                for prefix in prefixes:
                    if (alias.startswith(prefix) and
                            is_number(alias.replace(prefix, '')[:2]) and
                            is_number(alias.replace(prefix, '')[:1])):
                        discoverdate = '20' + alias.replace(prefix, '')[:2]
                        if catalog.args.verbose:
                            tprint('Added discoverdate from name [' + alias +
                                   ']: ' + discoverdate)
                        source = catalog.entries[name].add_self_source()
                        catalog.entries[name].add_quantity(
                            SUPERNOVA.DISCOVER_DATE,
                            discoverdate,
                            source,
                            derived=True)
                        break
                if SUPERNOVA.DISCOVER_DATE in catalog.entries[name]:
                    break
        if SUPERNOVA.DISCOVER_DATE not in catalog.entries[name]:
            prefixes = ['SNF']
            for alias in aliases:
                for prefix in prefixes:
                    if (alias.startswith(prefix) and
                            is_number(alias.replace(prefix, '')[:4])):
                        discoverdate = ('/'.join([
                            alias.replace(prefix, '')[:4],
                            alias.replace(prefix, '')[4:6],
                            alias.replace(prefix, '')[6:8]
                        ]))
                        if catalog.args.verbose:
                            tprint('Added discoverdate from name [' + alias +
                                   ']: ' + discoverdate)
                        source = catalog.entries[name].add_self_source()
                        catalog.entries[name].add_quantity(
                            SUPERNOVA.DISCOVER_DATE,
                            discoverdate,
                            source,
                            derived=True)
                        break
                if SUPERNOVA.DISCOVER_DATE in catalog.entries[name]:
                    break
        if SUPERNOVA.DISCOVER_DATE not in catalog.entries[name]:
            prefixes = ['PTFS', 'SNSDF']
            for alias in aliases:
                for prefix in prefixes:
                    if (alias.startswith(prefix) and
                            is_number(alias.replace(prefix, '')[:2])):
                        discoverdate = ('/'.join([
                            '20' + alias.replace(prefix, '')[:2],
                            alias.replace(prefix, '')[2:4]
                        ]))
                        if catalog.args.verbose:
                            tprint('Added discoverdate from name [' + alias +
                                   ']: ' + discoverdate)
                        source = catalog.entries[name].add_self_source()
                        catalog.entries[name].add_quantity(
                            SUPERNOVA.DISCOVER_DATE,
                            discoverdate,
                            source,
                            derived=True)
                        break
                if SUPERNOVA.DISCOVER_DATE in catalog.entries[name]:
                    break
        if SUPERNOVA.DISCOVER_DATE not in catalog.entries[name]:
            prefixes = ['AT', 'SN', 'OGLE-', 'SM ', 'KSN']
            for alias in aliases:
                for prefix in prefixes:
                    if alias.startswith(prefix):
                        year = re.findall(r'\d+', alias)
                        if len(year) == 1:
                            year = year[0]
                        else:
                            continue
                        if alias.replace(prefix, '').index(year) != 0:
                            continue
                        if (year and is_number(year) and '.' not in year and
                                len(year) <= 4):
                            discoverdate = year
                            if catalog.args.verbose:
                                tprint('Added discoverdate from name [' +
                                       alias + ']: ' + discoverdate)
                            source = catalog.entries[name].add_self_source()
                            catalog.entries[name].add_quantity(
                                SUPERNOVA.DISCOVER_DATE,
                                discoverdate,
                                source,
                                derived=True)
                            break
                if SUPERNOVA.DISCOVER_DATE in catalog.entries[name]:
                    break

        if (SUPERNOVA.RA not in catalog.entries[name] or
                SUPERNOVA.DEC not in catalog.entries[name]):
            prefixes = [
                'PSN J', 'MASJ', 'CSS', 'SSS', 'MASTER OT J', 'HST J', 'TCP J',
                'MACS J', '2MASS J', 'EQ J', 'CRTS J', 'SMT J'
            ]
            for alias in aliases:
                for prefix in prefixes:
                    if (alias.startswith(prefix) and
                            is_number(alias.replace(prefix, '')[:6])):
                        noprefix = alias.split(':')[-1].replace(
                            prefix, '').replace('.', '')
                        decsign = '+' if '+' in noprefix else '-'
                        noprefix = noprefix.replace('+', '|').replace('-', '|')
                        nops = noprefix.split('|')
                        if len(nops) < 2:
                            continue
                        rastr = nops[0]
                        decstr = nops[1]
                        ra = ':'.join([rastr[:2], rastr[2:4], rastr[4:6]]) + \
                            ('.' + rastr[6:] if len(rastr) > 6 else '')
                        dec = (
                            decsign + ':'.join(
                                [decstr[:2], decstr[2:4], decstr[4:6]]) +
                            ('.' + decstr[6:] if len(decstr) > 6 else ''))
                        if catalog.args.verbose:
                            tprint('Added ra/dec from name: ' + ra + ' ' + dec)
                        source = catalog.entries[name].add_self_source()
                        catalog.entries[name].add_quantity(
                            SUPERNOVA.RA, ra, source, derived=True)
                        catalog.entries[name].add_quantity(
                            SUPERNOVA.DEC, dec, source, derived=True)
                        break
                if SUPERNOVA.RA in catalog.entries[name]:
                    break

        no_host = (SUPERNOVA.HOST not in catalog.entries[name] or not any([
            x[QUANTITY.VALUE] == 'Milky Way'
            for x in catalog.entries[name][SUPERNOVA.HOST]
        ]))
        if (SUPERNOVA.RA in catalog.entries[name] and
                SUPERNOVA.DEC in catalog.entries[name] and no_host):
            from astroquery.irsa_dust import IrsaDust
            if name not in catalog.extinctions_dict:
                try:
                    ra_dec = catalog.entries[name][
                        SUPERNOVA.RA][0][QUANTITY.VALUE] + \
                        " " + \
                        catalog.entries[name][SUPERNOVA.DEC][0][QUANTITY.VALUE]
                    result = IrsaDust.get_query_table(ra_dec, section='ebv')
                except (KeyboardInterrupt, SystemExit):
                    raise
                except Exception:
                    warnings.warn("Coordinate lookup for " + name +
                                  " failed in IRSA.")
                else:
                    ebv = result['ext SandF mean'][0]
                    ebverr = result['ext SandF std'][0]
                    catalog.extinctions_dict[name] = [ebv, ebverr]
            if name in catalog.extinctions_dict:
                sources = uniq_cdl([
                    catalog.entries[name].add_self_source(),
                    catalog.entries[name]
                    .add_source(bibcode='2011ApJ...737..103S')
                ])
                (catalog.entries[name].add_quantity(
                    SUPERNOVA.EBV,
                    str(catalog.extinctions_dict[name][0]),
                    sources,
                    e_value=str(catalog.extinctions_dict[name][1]),
                    derived=True))
        if ((SUPERNOVA.HOST in catalog.entries[name] and
             (SUPERNOVA.HOST_RA not in catalog.entries[name] or
              SUPERNOVA.HOST_DEC not in catalog.entries[name]))):
            for host in catalog.entries[name][SUPERNOVA.HOST]:
                alias = host[QUANTITY.VALUE]
                if ' J' in alias and is_number(alias.split(' J')[-1][:6]):
                    noprefix = alias.split(' J')[-1].split(':')[-1].replace(
                        '.', '')
                    decsign = '+' if '+' in noprefix else '-'
                    noprefix = noprefix.replace('+', '|').replace('-', '|')
                    nops = noprefix.split('|')
                    if len(nops) < 2:
                        continue
                    rastr = nops[0]
                    decstr = nops[1]
                    hostra = (':'.join([rastr[:2], rastr[2:4], rastr[4:6]]) +
                              ('.' + rastr[6:] if len(rastr) > 6 else ''))
                    hostdec = decsign + ':'.join([
                        decstr[:2], decstr[2:4], decstr[4:6]
                    ]) + ('.' + decstr[6:] if len(decstr) > 6 else '')
                    if catalog.args.verbose:
                        tprint('Added hostra/hostdec from name: ' + hostra +
                               ' ' + hostdec)
                    source = catalog.entries[name].add_self_source()
                    catalog.entries[name].add_quantity(
                        SUPERNOVA.HOST_RA, hostra, source, derived=True)
                    catalog.entries[name].add_quantity(
                        SUPERNOVA.HOST_DEC, hostdec, source, derived=True)
                    break
                if SUPERNOVA.HOST_RA in catalog.entries[name]:
                    break

        if (SUPERNOVA.REDSHIFT not in catalog.entries[name] and
                SUPERNOVA.VELOCITY in catalog.entries[name]):
            # Find the "best" velocity to use for this
            bestsig = 0
            for hv in catalog.entries[name][SUPERNOVA.VELOCITY]:
                sig = get_sig_digits(hv[QUANTITY.VALUE])
                if sig > bestsig:
                    besthv = hv[QUANTITY.VALUE]
                    bestsrc = hv['source']
                    bestsig = sig
            if bestsig > 0 and is_number(besthv):
                voc = float(besthv) * 1.e5 / CLIGHT
                source = catalog.entries[name].add_self_source()
                sources = uniq_cdl([source] + bestsrc.split(','))
                (catalog.entries[name].add_quantity(
                    SUPERNOVA.REDSHIFT,
                    pretty_num(
                        sqrt((1. + voc) / (1. - voc)) - 1., sig=bestsig),
                    sources,
                    kind='heliocentric',
                    derived=True))
        if (SUPERNOVA.REDSHIFT not in catalog.entries[name] and
                len(catalog.nedd_dict) > 0 and
                SUPERNOVA.HOST in catalog.entries[name]):
            reference = "NED-D"
            refurl = "http://ned.ipac.caltech.edu/Library/Distances/"
            refbib = "1991ASSL..171...89H"
            for host in catalog.entries[name][SUPERNOVA.HOST]:
                if host[QUANTITY.VALUE] in catalog.nedd_dict:
                    source = catalog.entries[name].add_source(
                        bibcode='2016A&A...594A..13P')
                    secondarysource = catalog.entries[name].add_source(
                        name=reference, url=refurl, bibcode=refbib,
                        secondary=True)
                    meddist = statistics.median(catalog.nedd_dict[host[
                        QUANTITY.VALUE]])
                    redz = z_at_value(cosmo.comoving_distance,
                                      float(meddist) * un.Mpc)
                    redshift = pretty_num(
                        redz, sig=get_sig_digits(str(meddist)))
                    catalog.entries[name].add_quantity(
                        [SUPERNOVA.REDSHIFT, SUPERNOVA.HOST_REDSHIFT],
                        redshift,
                        uniq_cdl([source, secondarysource]),
                        kind='host',
                        derived=True)
        if (SUPERNOVA.MAX_ABS_MAG not in catalog.entries[name] and
                SUPERNOVA.MAX_APP_MAG in catalog.entries[name] and
                SUPERNOVA.LUM_DIST in catalog.entries[name]):
            # Find the "best" distance to use for this
            bestsig = 0
            for ld in catalog.entries[name][SUPERNOVA.LUM_DIST]:
                sig = get_sig_digits(ld[QUANTITY.VALUE])
                if sig > bestsig:
                    bestld = ld[QUANTITY.VALUE]
                    bestsrc = ld[QUANTITY.SOURCE]
                    bestsig = sig
            if bestsig > 0 and is_number(bestld) and float(bestld) > 0.:
                source = catalog.entries[name].add_self_source()
                sources = uniq_cdl([source] + bestsrc.split(','))
                bestldz = z_at_value(cosmo.luminosity_distance,
                                     float(bestld) * un.Mpc)
                pnum = (
                    float(catalog.entries[name][SUPERNOVA.MAX_APP_MAG][0][
                        QUANTITY.VALUE]) - 5.0 *
                    (log10(float(bestld) * 1.0e6) - 1.0
                     ) + 2.5 * log10(1.0 + bestldz))
                pnum = pretty_num(pnum, sig=bestsig + 1)
                catalog.entries[name].add_quantity(
                    SUPERNOVA.MAX_ABS_MAG, pnum, sources, derived=True)
        if (SUPERNOVA.MAX_VISUAL_ABS_MAG not in catalog.entries[name] and
                SUPERNOVA.MAX_VISUAL_APP_MAG in catalog.entries[name] and
                SUPERNOVA.LUM_DIST in catalog.entries[name]):
            # Find the "best" distance to use for this
            bestsig = 0
            for ld in catalog.entries[name][SUPERNOVA.LUM_DIST]:
                sig = get_sig_digits(ld[QUANTITY.VALUE])
                if sig > bestsig:
                    bestld = ld[QUANTITY.VALUE]
                    bestsrc = ld[QUANTITY.SOURCE]
                    bestsig = sig
            if bestsig > 0 and is_number(bestld) and float(bestld) > 0.:
                source = catalog.entries[name].add_self_source()
                sources = uniq_cdl([source] + bestsrc.split(','))
                # FIX: what's happening here?!
                pnum = (
                    float(catalog.entries[name][
                        SUPERNOVA.MAX_VISUAL_APP_MAG][0][QUANTITY.VALUE]) -
                    5.0 * (log10(float(bestld) * 1.0e6) - 1.0))
                pnum = pretty_num(pnum, sig=bestsig + 1)
                catalog.entries[name].add_quantity(
                    SUPERNOVA.MAX_VISUAL_ABS_MAG, pnum, sources, derived=True)
        if SUPERNOVA.REDSHIFT in catalog.entries[name]:
            # Find the "best" redshift to use for this
            bestz, bestkind, bestsig, bestsrc = catalog.entries[
                name].get_best_redshift()
            if bestsig > 0:
                try:
                    bestz = float(bestz)
                except Exception:
                    print(catalog.entries[name])
                    raise
                if SUPERNOVA.VELOCITY not in catalog.entries[name]:
                    source = catalog.entries[name].add_self_source()
                    # FIX: what's happening here?!
                    pnum = CLIGHT / KM * \
                        ((bestz + 1.)**2. - 1.) / ((bestz + 1.)**2. + 1.)
                    pnum = pretty_num(pnum, sig=bestsig)
                    catalog.entries[name].add_quantity(
                        SUPERNOVA.VELOCITY,
                        pnum,
                        source,
                        kind=(SUPERNOVA.VELOCITY.kind_preference[bestkind]
                              if bestkind else ''))
                if bestz > 0.:
                    if SUPERNOVA.LUM_DIST not in catalog.entries[name]:
                        dl = cosmo.luminosity_distance(bestz)
                        sources = [
                            catalog.entries[name].add_self_source(),
                            catalog.entries[name]
                            .add_source(bibcode='2016A&A...594A..13P')
                        ]
                        sources = uniq_cdl(sources + bestsrc.split(','))
                        catalog.entries[name].add_quantity(
                            SUPERNOVA.LUM_DIST,
                            pretty_num(
                                dl.value, sig=bestsig + 1),
                            sources,
                            kind=(SUPERNOVA.LUM_DIST.kind_preference[bestkind]
                                  if bestkind else ''),
                            derived=True)
                        if (SUPERNOVA.MAX_ABS_MAG not in
                            catalog.entries[name] and SUPERNOVA.MAX_APP_MAG in
                                catalog.entries[name]):
                            source = catalog.entries[name].add_self_source()
                            pnum = pretty_num(
                                float(catalog.entries[name][
                                    SUPERNOVA.MAX_APP_MAG][0][QUANTITY.VALUE])
                                - 5.0 * (log10(dl.to('pc').value) - 1.0
                                         ) + 2.5 * log10(1.0 + bestz),
                                sig=bestsig + 1)
                            catalog.entries[name].add_quantity(
                                SUPERNOVA.MAX_ABS_MAG,
                                pnum,
                                sources,
                                derived=True)
                        if (SUPERNOVA.MAX_VISUAL_ABS_MAG not in
                                catalog.entries[name] and
                                SUPERNOVA.MAX_VISUAL_APP_MAG in
                                catalog.entries[name]):
                            source = catalog.entries[name].add_self_source()
                            pnum = pretty_num(
                                float(catalog.entries[name][
                                    SUPERNOVA.MAX_VISUAL_APP_MAG][0][
                                        QUANTITY.VALUE]) - 5.0 *
                                (log10(dl.to('pc').value) - 1.0),
                                sig=bestsig + 1)
                            catalog.entries[name].add_quantity(
                                SUPERNOVA.MAX_VISUAL_ABS_MAG,
                                pnum,
                                sources,
                                derived=True)
                    if SUPERNOVA.COMOVING_DIST not in catalog.entries[name]:
                        cd = cosmo.comoving_distance(bestz)
                        sources = [
                            catalog.entries[name].add_self_source(),
                            catalog.entries[name]
                            .add_source(bibcode='2016A&A...594A..13P')
                        ]
                        sources = uniq_cdl(sources + bestsrc.split(','))
                        catalog.entries[name].add_quantity(
                            SUPERNOVA.COMOVING_DIST,
                            pretty_num(
                                cd.value, sig=bestsig),
                            sources,
                            derived=True)
        if SUPERNOVA.HOST_REDSHIFT in catalog.entries[name]:
            # Find the "best" redshift to use for this
            bestz, bestkind, bestsig, bestsrc = catalog.entries[
                name].get_best_redshift(SUPERNOVA.HOST_REDSHIFT)
            if bestsig > 0:
                try:
                    bestz = float(bestz)
                except Exception:
                    print(catalog.entries[name])
                    raise
                if SUPERNOVA.HOST_VELOCITY not in catalog.entries[name]:
                    source = catalog.entries[name].add_self_source()
                    # FIX: what's happening here?!
                    pnum = CLIGHT / KM * \
                        ((bestz + 1.)**2. - 1.) / ((bestz + 1.)**2. + 1.)
                    pnum = pretty_num(pnum, sig=bestsig)
                    catalog.entries[name].add_quantity(
                        SUPERNOVA.HOST_VELOCITY,
                        pnum,
                        source,
                        kind=(SUPERNOVA.HOST_VELOCITY.kind_preference[bestkind]
                              if bestkind else ''))
                if bestz > 0.:
                    if SUPERNOVA.HOST_LUM_DIST not in catalog.entries[name]:
                        dl = cosmo.luminosity_distance(bestz)
                        sources = [
                            catalog.entries[name].add_self_source(),
                            catalog.entries[name]
                            .add_source(bibcode='2016A&A...594A..13P')
                        ]
                        sources = uniq_cdl(sources + bestsrc.split(','))
                        catalog.entries[name].add_quantity(
                            SUPERNOVA.HOST_LUM_DIST,
                            pretty_num(
                                dl.value, sig=bestsig + 1),
                            sources,
                            kind=(SUPERNOVA.HOST_LUM_DIST.kind_preference[
                                bestkind] if bestkind else ''),
                            derived=True)
                    if SUPERNOVA.HOST_COMOVING_DIST not in catalog.entries[
                            name]:
                        cd = cosmo.comoving_distance(bestz)
                        sources = [
                            catalog.entries[name].add_self_source(),
                            catalog.entries[name]
                            .add_source(bibcode='2016A&A...594A..13P')
                        ]
                        sources = uniq_cdl(sources + bestsrc.split(','))
                        catalog.entries[name].add_quantity(
                            SUPERNOVA.HOST_COMOVING_DIST,
                            pretty_num(
                                cd.value, sig=bestsig),
                            sources,
                            derived=True)
        if all([
                x in catalog.entries[name]
                for x in [
                    SUPERNOVA.RA, SUPERNOVA.DEC, SUPERNOVA.HOST_RA,
                    SUPERNOVA.HOST_DEC
                ]
        ]):
            # For now just using first coordinates that appear in entry
            try:
                c1 = coord(
                    ra=catalog.entries[name][SUPERNOVA.RA][0][QUANTITY.VALUE],
                    dec=catalog.entries[name][SUPERNOVA.DEC][0][
                        QUANTITY.VALUE],
                    unit=(un.hourangle, un.deg))
                c2 = coord(
                    ra=catalog.entries[name][SUPERNOVA.HOST_RA][0][
                        QUANTITY.VALUE],
                    dec=catalog.entries[name][SUPERNOVA.HOST_DEC][0][
                        QUANTITY.VALUE],
                    unit=(un.hourangle, un.deg))
            except (KeyboardInterrupt, SystemExit):
                raise
            except Exception:
                pass
            else:
                sources = uniq_cdl(
                    [catalog.entries[name].add_self_source()] + catalog.
                    entries[name][SUPERNOVA.RA][0][QUANTITY.SOURCE].split(',')
                    + catalog.entries[name][SUPERNOVA.DEC][0][QUANTITY.SOURCE]
                    .split(',') + catalog.entries[name][SUPERNOVA.HOST_RA][0][
                        QUANTITY.SOURCE].split(',') + catalog.entries[name][
                            SUPERNOVA.HOST_DEC][0][QUANTITY.SOURCE].split(','))
                if SUPERNOVA.HOST_OFFSET_ANG not in catalog.entries[name]:
                    hosa = Decimal(c1.separation(c2).arcsecond)
                    hosa = pretty_num(hosa)
                    catalog.entries[name].add_quantity(
                        SUPERNOVA.HOST_OFFSET_ANG,
                        hosa,
                        sources,
                        derived=True,
                        u_value='arcseconds')
                if (SUPERNOVA.COMOVING_DIST in catalog.entries[name] and
                        SUPERNOVA.REDSHIFT in catalog.entries[name] and
                        SUPERNOVA.HOST_OFFSET_DIST not in
                        catalog.entries[name]):
                    offsetsig = get_sig_digits(catalog.entries[name][
                        SUPERNOVA.HOST_OFFSET_ANG][0][QUANTITY.VALUE])
                    sources = uniq_cdl(
                        sources.split(',') + (catalog.entries[name][
                            SUPERNOVA.COMOVING_DIST][0][QUANTITY.SOURCE]).
                        split(',') + (catalog.entries[name][SUPERNOVA.REDSHIFT]
                                      [0][QUANTITY.SOURCE]).split(','))
                    (catalog.entries[name].add_quantity(
                        SUPERNOVA.HOST_OFFSET_DIST,
                        pretty_num(
                            float(catalog.entries[name][
                                SUPERNOVA.HOST_OFFSET_ANG][0][QUANTITY.VALUE])
                            / 3600. * (pi / 180.) *
                            float(catalog.entries[name][
                                SUPERNOVA.COMOVING_DIST][0][QUANTITY.VALUE]) *
                            1000. / (1.0 + float(catalog.entries[name][
                                SUPERNOVA.REDSHIFT][0][QUANTITY.VALUE])),
                            sig=offsetsig),
                        sources))

        catalog.entries[name].sanitize()
        catalog.journal_entries(bury=True, final=True, gz=True)
        cleanupcnt = cleanupcnt + 1
        if catalog.args.travis and cleanupcnt % 1000 == 0:
            break

    catalog.save_caches()

    return
