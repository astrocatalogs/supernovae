'''Import tasks for NED-D, the galactic distances catalog.
'''
import csv
import os
from collections import OrderedDict
from html import unescape

from astropy import units as un
from astropy.cosmology import Planck15 as cosmo
from astropy.cosmology import z_at_value

from astrocats.catalog.utils import (get_sig_digits, is_number, pbar,
                                     pretty_num, uniq_cdl)
from astrocats.supernovae.utils import host_clean, name_clean
from cdecimal import Decimal


def do_nedd(catalog):
    task_str = catalog.get_current_task_str()
    nedd_path = os.path.join(
        catalog.get_current_task_repo(), 'NED26.05.1-D-12.1.0-20160501.csv')

    f = open(nedd_path, 'r')

    data = sorted(list(csv.reader(f, delimiter=',', quotechar='"'))[
                  13:], key=lambda x: (x[9], x[3]))
    reference = "NED-D"
    refurl = "http://ned.ipac.caltech.edu/Library/Distances/"
    nedd_dict = OrderedDict()
    olddistname = ''
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
                nedd_dict.setdefault(cleanhost, []).append(Decimal(dist))
        if snname and 'HOST' not in snname:
            snname, secondarysource = catalog.new_entry(
                snname, srcname=reference, url=refurl, secondary=True)
            if bibcode:
                source = catalog.entries[snname].add_source(bibcode=bibcode)
                sources = uniq_cdl([source, secondarysource])
            else:
                sources = secondarysource
            if name == snname:
                if redshift:
                    catalog.entries[snname].add_quantity(
                        'redshift', redshift, sources)
                if dist:
                    catalog.entries[snname].add_quantity(
                        'comovingdist', dist, sources)
                    if not redshift:
                        try:
                            zatval = z_at_value(cosmo.comoving_distance,
                                                float(dist) * un.Mpc, zmax=5.0)
                            sigd = get_sig_digits(str(dist))
                            redshift = pretty_num(zatval, sig=sigd)
                        except (KeyboardInterrupt, SystemExit):
                            raise
                        except:
                            pass
                        else:
                            cosmosource = catalog.entries[name].add_source(
                                bibcode='2015arXiv150201589P')
                            combsources = uniq_cdl(sources.split(',') +
                                                   [cosmosource])
                            catalog.entries[snname].add_quantity('redshift',
                                                                 redshift,
                                                                 combsources)
            if cleanhost:
                catalog.entries[snname].add_quantity(
                    'host', cleanhost, sources)
            if catalog.args.update and olddistname != distname:
                catalog.journal_entries()
        olddistname = distname
    catalog.journal_entries()

    f.close()

    return
