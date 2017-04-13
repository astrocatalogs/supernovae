'''Import tasks for NED-D, the galactic distances catalog.
'''
import csv
import os
from collections import OrderedDict
from html import unescape

from astrocats.catalog.utils import (get_sig_digits, is_number, pbar,
                                     pretty_num, uniq_cdl)
from astropy import units as un
from astropy.cosmology import Planck15 as cosmo
from astropy.cosmology import z_at_value

from decimal import Decimal

from ..supernova import SUPERNOVA
from ..utils import host_clean, name_clean


def do_nedd(catalog):
    task_str = catalog.get_current_task_str()
    nedd_path = os.path.join(
        catalog.get_current_task_repo(), 'NED26.10.1-D-13.1.0-20160930.csv')

    f = open(nedd_path, 'r')

    data = sorted(list(csv.reader(f, delimiter=',', quotechar='"'))[
                  13:], key=lambda x: (x[9], x[3]))
    reference = "NED-D v" + nedd_path.split('-')[-2]
    refurl = "http://ned.ipac.caltech.edu/Library/Distances/"
    nedbib = "1991ASSL..171...89H"
    olddistname = ''
    loopcnt = 0
    for r, row in enumerate(pbar(data, task_str)):
        if r <= 12:
            continue
        distname = row[3]
        name = name_clean(distname)
        # distmod = row[4]
        # moderr = row[5]
        dist = row[6]
        bibcode = unescape(row[8])
        snname = name_clean(row[9])
        redshift = row[10]
        cleanhost = ''
        if name != snname and (name + ' HOST' != snname):
            cleanhost = host_clean(distname)
            if cleanhost.endswith(' HOST'):
                cleanhost = ''
            if not is_number(dist):
                print(dist)
            if dist:
                catalog.nedd_dict.setdefault(
                    cleanhost, []).append(Decimal(dist))
        if snname and 'HOST' not in snname:
            snname, secondarysource = catalog.new_entry(
                snname, srcname=reference, bibcode=nedbib, url=refurl,
                secondary=True)
            if bibcode:
                source = catalog.entries[snname].add_source(bibcode=bibcode)
                sources = uniq_cdl([source, secondarysource])
            else:
                sources = secondarysource
            if name == snname:
                if redshift:
                    catalog.entries[snname].add_quantity(
                        SUPERNOVA.REDSHIFT, redshift, sources)
                if dist:
                    catalog.entries[snname].add_quantity(
                        SUPERNOVA.COMOVING_DIST, dist, sources)
                    if not redshift:
                        try:
                            zatval = z_at_value(cosmo.comoving_distance,
                                                float(dist) * un.Mpc, zmax=5.0)
                            sigd = get_sig_digits(str(dist))
                            redshift = pretty_num(zatval, sig=sigd)
                        except (KeyboardInterrupt, SystemExit):
                            raise
                        except Exception:
                            pass
                        else:
                            cosmosource = catalog.entries[name].add_source(
                                bibcode='2016A&A...594A..13P')
                            combsources = uniq_cdl(sources.split(',') +
                                                   [cosmosource])
                            catalog.entries[snname].add_quantity(
                                SUPERNOVA.REDSHIFT, redshift, combsources,
                                derived=True)
            if cleanhost:
                catalog.entries[snname].add_quantity(
                    SUPERNOVA.HOST, cleanhost, sources)
            if catalog.args.update and olddistname != distname:
                catalog.journal_entries()
        olddistname = distname

        loopcnt = loopcnt + 1
        if catalog.args.travis and loopcnt % catalog.TRAVIS_QUERY_LIMIT == 0:
            break
    catalog.journal_entries()

    f.close()

    return
