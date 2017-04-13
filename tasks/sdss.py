"""Import tasks for the Sloan Digital Sky Survey.
"""
import csv
import os
from glob import glob

from astropy.coordinates import SkyCoord as coord
from astropy.time import Time as astrotime

from astrocats.catalog.photometry import PHOTOMETRY
from astrocats.catalog.quantity import QUANTITY
from astrocats.catalog.utils import make_date_string, pbar, pbar_strings
from decimal import Decimal

from ..supernova import SUPERNOVA


def do_sdss_photo(catalog):
    task_str = catalog.get_current_task_str()
    D25 = Decimal('2.5')

    # fits_path = os.path.join(catalog.get_current_task_repo(),
    #                          'SDSS/SDSS_allCandidates+BOSS_HEAD.FITS')
    #
    # hdulist = fits.open(fits_path)
    # print(hdulist[1].columns)
    # for ri, row in enumerate(hdulist[1].data['SNID']):
    #     print([[tag, hdulist[1].data[tag][ri]] for tag in hdulist[1].data])
    #     print(hdulist[1].data['SNID'][ri], hdulist[1].data['IAUC'][ri],
    #           hdulist[1].data['REDSHIFT_HELIO'][ri])
    #
    # # print(hdulist[1].data['MJD'])
    # hdulist.close()
    # return

    # Load up metadata first
    with open(
            os.path.join(catalog.get_current_task_repo(),
                         'SDSS/sdsssn_master.dat2'), 'r') as f:
        rows = list(csv.reader(f.read().splitlines()[1:], delimiter=' '))
        ignored_cids = []
        columns = {
            SUPERNOVA.RA: 1,
            SUPERNOVA.DEC: 2,
            SUPERNOVA.ALIAS: 4,
            SUPERNOVA.CLAIMED_TYPE: 5,
            SUPERNOVA.REDSHIFT: 11,
            SUPERNOVA.MAX_DATE: 21,
            SUPERNOVA.HOST_RA: 99,
            SUPERNOVA.HOST_DEC: 100
        }
        colnums = {v: k for k, v in columns.items()}

        rows = [[x.replace('\\N', '') for x in y] for y in rows]

        co = [[x[0], x[99], x[100]] for x in rows if x[99] and x[100]]
        coo = coord([x[1] for x in co], [x[2] for x in co], unit="deg")
        coo = [
            ''.join([y[:9] for y in x.split()])
            for x in coo.to_string(
                'hmsdms', sep='')
        ]
        hostdict = dict(
            zip([x[0] for x in co], ['SDSS J' + x[1:] for x in coo]))

        for ri, row in enumerate(pbar(rows, task_str + ": metadata")):
            name = ''

            # Check if type is non-SNe first
            ct = row[columns[SUPERNOVA.CLAIMED_TYPE]]
            al = row[columns[SUPERNOVA.ALIAS]]
            if ct in ['AGN', 'Variable', 'Unknown'] and not al:
                catalog.log.info('`{}` is not a SN, not '
                                 'adding.'.format(row[0]))
                ignored_cids.append(row[0])
                continue

            # Add entry
            (name, source) = catalog.new_entry(
                'SDSS-II SN ' + row[0],
                bibcode='2014arXiv1401.3317S',
                url='http://data.sdss3.org/sas/dr10/boss/papers/supernova/')

            # Add host name
            if row[0] in hostdict:
                catalog.entries[name].add_quantity(SUPERNOVA.HOST,
                                                   hostdict[row[0]], source)

            # Add other metadata
            for cn in colnums:
                key = colnums[cn]
                if not key:
                    continue
                ic = int(cn)
                val = row[ic]
                if not val:
                    continue
                kwargs = {}
                if key == SUPERNOVA.ALIAS:
                    val = 'SN' + val
                elif key in [
                        SUPERNOVA.RA, SUPERNOVA.DEC, SUPERNOVA.HOST_RA,
                        SUPERNOVA.HOST_DEC
                ]:
                    kwargs = {QUANTITY.U_VALUE: 'floatdegrees'}
                    if key in [SUPERNOVA.RA, SUPERNOVA.HOST_RA]:
                        fval = float(val)
                        if fval < 0.0:
                            val = str(Decimal(360) + Decimal(fval))
                elif key == SUPERNOVA.CLAIMED_TYPE:
                    val = val.lstrip('pz').replace('SN', '')
                elif key == SUPERNOVA.REDSHIFT:
                    kwargs[QUANTITY.KIND] = 'spectroscopic'
                    if float(val) < -1.0:
                        continue
                    if float(row[ic + 1]) > 0.0:
                        kwargs[QUANTITY.E_VALUE] = row[ic + 1]
                elif key == SUPERNOVA.MAX_DATE:
                    dt = astrotime(float(val), format='mjd').datetime
                    val = make_date_string(dt.year, dt.month, dt.day)
                catalog.entries[name].add_quantity(key, val, source, **kwargs)

    with open(
            os.path.join(catalog.get_current_task_repo(),
                         'SDSS/2010ApJ...708..661D.txt'), 'r') as sdss_file:
        bibcodes2010 = sdss_file.read().split('\n')
    sdssbands = ['u', 'g', 'r', 'i', 'z']
    file_names = (list(
        glob(os.path.join(catalog.get_current_task_repo(), 'SDSS/sum/*.sum')))
                  + list(
                      glob(
                          os.path.join(catalog.get_current_task_repo(),
                                       'SDSS/SMP_Data/*.dat'))))
    skipphoto = ['SDSS-II SN 15557']
    for fi, fname in enumerate(pbar_strings(file_names, task_str)):
        tsvin = csv.reader(
            open(fname, 'r'), delimiter=' ', skipinitialspace=True)
        basename = os.path.basename(fname)
        hasred = True
        rst = 19
        if '.dat' in fname:
            bibcode = '2014arXiv1401.3317S'
            hasred = False
            rst = 4
        elif basename in bibcodes2010:
            bibcode = '2010ApJ...708..661D'
        else:
            bibcode = '2008AJ....136.2306H'

        skip_entry = False
        for rr, row in enumerate(tsvin):
            if skip_entry:
                break
            if rr == 0:
                # Ignore non-SNe objects and those not in metadata table above
                if row[3] in ignored_cids:
                    skip_entry = True
                    continue
                # Ignore IAU names from file headers as they are unreliable
                oname = 'SDSS-II SN ' + row[3]
                (name, source) = catalog.new_entry(oname, bibcode=bibcode)
                catalog.entries[name].add_quantity(
                    SUPERNOVA.RA, row[-4], source, u_value='floatdegrees')
                catalog.entries[name].add_quantity(
                    SUPERNOVA.DEC, row[-2], source, u_value='floatdegrees')
            if hasred and rr == 1:
                error = row[4] if float(row[4]) >= 0.0 else ''
                val = row[2]
                if float(val) < -1.0:
                    continue
                (catalog.entries[name].add_quantity(
                    SUPERNOVA.REDSHIFT,
                    val,
                    source,
                    e_value=error,
                    kind='heliocentric'))
            if rr >= rst:
                # Skip bad measurements
                if int(row[0]) > 1024:
                    continue
                if oname in skipphoto:
                    break

                mjd = row[1]
                band = sdssbands[int(row[2])] + "'"
                magnitude = row[3]
                e_mag = row[4]
                fluxd = row[7]
                e_fluxd = row[8]
                telescope = 'SDSS'
                photodict = {
                    PHOTOMETRY.TIME: mjd,
                    PHOTOMETRY.U_TIME: 'MJD',
                    PHOTOMETRY.TELESCOPE: telescope,
                    PHOTOMETRY.BAND: band,
                    PHOTOMETRY.MAGNITUDE: magnitude,
                    PHOTOMETRY.E_MAGNITUDE: e_mag,
                    PHOTOMETRY.FLUX_DENSITY: fluxd,
                    PHOTOMETRY.E_FLUX_DENSITY: e_fluxd,
                    PHOTOMETRY.U_FLUX_DENSITY: 'μJy',
                    PHOTOMETRY.SOURCE: source,
                    PHOTOMETRY.BAND_SET: 'SDSS',
                    PHOTOMETRY.SYSTEM: 'SDSS'
                }
                if float(fluxd) > 0.0:
                    photodict[PHOTOMETRY.ZERO_POINT] = str(D25 * Decimal(
                        fluxd).log10() + Decimal(magnitude))
                ul_sigma = 3.0
                if int(row[0]) & 32 or float(fluxd) < ul_sigma * float(
                        e_fluxd):
                    photodict[PHOTOMETRY.UPPER_LIMIT] = True
                    photodict[PHOTOMETRY.UPPER_LIMIT_SIGMA] = str(ul_sigma)
                catalog.entries[name].add_photometry(**photodict)
        if catalog.args.travis and fi >= catalog.TRAVIS_QUERY_LIMIT:
            break
        if not fi % 1000:
            catalog.journal_entries()

    catalog.journal_entries()
    return
