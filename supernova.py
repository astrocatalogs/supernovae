"""Supernova transient class."""
import warnings
from collections import OrderedDict
from decimal import Decimal

import numpy as np
from astrocats.catalog.entry import ENTRY, Entry
from astrocats.catalog.key import KEY_TYPES, Key
from astrocats.catalog.photometry import PHOTOMETRY
from astrocats.catalog.quantity import QUANTITY
from astrocats.catalog.source import SOURCE
from astrocats.catalog.utils import (bib_priority, get_sig_digits,
                                     get_source_year, is_integer, is_number,
                                     jd_to_mjd, listify, make_date_string,
                                     pretty_num, uniq_cdl)
from astropy.time import Time as astrotime
from six import string_types

from .constants import MAX_VISUAL_BANDS
from .utils import frame_priority, host_clean, radec_clean


class SUPERNOVA(ENTRY):
    """Supernova `Key` child class."""

    CLAIMED_TYPE = Key('claimedtype',
                       KEY_TYPES.STRING,
                       kind_preference=['spectroscopic', 'photometric'],
                       replace_better=True)
    DISCOVERY_DATE = Key('discoverdate', KEY_TYPES.STRING)
    EXPLOSION_DATE = Key('explosiondate', KEY_TYPES.STRING)
    MAX_VISUAL_ABS_MAG = Key('maxvisualabsmag', KEY_TYPES.NUMERIC)
    MAX_VISUAL_APP_MAG = Key('maxvisualappmag', KEY_TYPES.NUMERIC)
    MAX_VISUAL_BAND = Key('maxvisualband', KEY_TYPES.STRING)
    MAX_VISUAL_DATE = Key('maxvisualdate',
                          KEY_TYPES.STRING,
                          replace_better=True)
    ERRORS = Key('errors')


class Supernova(Entry):
    """Supernova `Entry` child class.

    NOTE: OrderedDict data is just the `name` values from the JSON file.
          I.e. it does not include the highest nesting level
          { name: DATA }, it *just* includes DATA

    FIX: check that no stored values are empty/invalid (delete key in that
         case?)
    """

    _KEYS = SUPERNOVA

    def __init__(self, catalog, name=None, stub=False):
        """Initialize `Supernova`."""
        super(Supernova, self).__init__(catalog, name, stub=stub)
        return

    def _append_additional_tags(self, name, sources, quantity):
        """Append additional bits of data to an existing quantity when a newly
        added quantity is found to be a duplicate
        """
        svalue = quantity.get(QUANTITY.VALUE, '')
        serror = quantity.get(QUANTITY.E_VALUE, '')
        sprob = quantity.get(QUANTITY.PROB, '')
        skind = quantity.get(QUANTITY.KIND, '')

        for ii, ct in enumerate(self[name]):
            if ct[QUANTITY.VALUE] == svalue and sources:
                if ct.get(QUANTITY.KIND, '') != skind:
                    return
                for source in sources.split(','):
                    if (source not in
                            self[name][ii][QUANTITY.SOURCE].split(',')):
                        self[name][ii][QUANTITY.SOURCE] += ',' + source
                        if serror and QUANTITY.E_VALUE not in self[name][ii]:
                            self[name][ii][QUANTITY.E_VALUE] = serror
                        if sprob and QUANTITY.PROB not in self[name][ii]:
                            self[name][ii][QUANTITY.PROB] = sprob
                return

    def _clean_quantity(self, quantity):
        """Clean quantity value before it is added to entry."""
        value = quantity.get(QUANTITY.VALUE, '').strip()
        error = quantity.get(QUANTITY.E_VALUE, '').strip()
        unit = quantity.get(QUANTITY.U_VALUE, '').strip()
        kinds = [x.strip() for x in listify(quantity.get(QUANTITY.KIND, []))]
        key = quantity._key

        if not value:
            return False

        if error and (not is_number(error) or float(error) < 0):
            raise ValueError(self[self._KEYS.NAME] + "'s quanta " + key +
                             ' error value must be a number and positive.')

        # Set default units
        if not unit and key == self._KEYS.VELOCITY:
            unit = 'km/s'
        if not unit and key == self._KEYS.RA:
            unit = 'hours'
        if not unit and key == self._KEYS.DEC:
            unit = 'degrees'
        if not unit and key in [self._KEYS.LUM_DIST, self._KEYS.COMOVING_DIST]:
            unit = 'Mpc'

        # Handle certain name
        if key == self._KEYS.ALIAS:
            value = self.catalog.clean_entry_name(value)
            for df in quantity.get(self._KEYS.DISTINCT_FROM, []):
                if value == df[QUANTITY.VALUE]:
                    return False
        elif key == self._KEYS.HOST:
            if is_number(value):
                return False
            if value.lower() in [
                    'anonymous', 'anon.', 'anon', 'intergalactic'
            ]:
                return False
            value = host_clean(value)
            if ((not kinds and ((value.lower().startswith('abell') and
                                 is_number(value[5:].strip())) or
                                'cluster' in value.lower()))):
                kinds = ['cluster']
        elif key == self._KEYS.HOST_REDSHIFT:
            kinds = list(filter(lambda x: x != 'host', kinds))
        elif key == self._KEYS.CLAIMED_TYPE:
            isq = False
            if value.startswith('SN '):
                value = value.replace('SN ', '', 1)
            value = value.replace('young', '')
            if '?' in value:
                isq = True
                value = value.strip(' ?')
            for rep in self.catalog.type_syns:
                if value in self.catalog.type_syns[rep]:
                    value = rep
                    break
            if isq:
                value = value + '?'
            if not value:
                return False
        elif key in [
                self._KEYS.RA, self._KEYS.DEC, self._KEYS.HOST_RA,
                self._KEYS.HOST_DEC
        ]:
            (value, unit) = radec_clean(value, key, unit=unit)
        elif key == self._KEYS.MAX_DATE or key == self._KEYS.DISCOVER_DATE:
            # Make sure month and day have leading zeroes
            sparts = value.split('/')
            if len(sparts[0]) > 5:
                self._log.warn("Date year {} greater than four "
                               "digits.".format(sparts[0]))
            if len(sparts) >= 2:
                value = sparts[0] + '/' + sparts[1].zfill(2)
            if len(sparts) == 3:
                value = value + '/' + sparts[2].zfill(2)

            # for ii, ct in enumerate(self.parent[key]):
            #     # Only add dates if they have more information
            #     if len(ct[QUANTITY.VALUE].split('/')) >
            #            len(value.split('/')):
            #         return False

        if is_number(value):
            value = '%g' % Decimal(value)
        if error:
            error = '%g' % Decimal(error)

        if value:
            quantity[QUANTITY.VALUE] = value
        if error:
            quantity[QUANTITY.E_VALUE] = error
        if unit:
            quantity[QUANTITY.U_VALUE] = unit
        if kinds:
            quantity[QUANTITY.KIND] = kinds if len(kinds) > 1 else kinds[0]
        elif QUANTITY.KIND in quantity:
            del (quantity[QUANTITY.KIND])

        return True

    def add_quantity(self,
                     quantities,
                     value,
                     source,
                     forcereplacebetter=False,
                     **kwargs):
        """Add `Quantity` to `Supernova`."""
        success = super(Supernova, self).add_quantity(
            quantities, value, source, **kwargs)

        if not success:
            return

        for quantity in listify(quantities):
            my_quantity_list = self.get(quantity, [])

            if ((forcereplacebetter or quantity.replace_better) and
                    len(my_quantity_list) > 1):

                # The quantity that was just added should be last in the list
                added_quantity = my_quantity_list.pop()

                newquantities = []
                isworse = True
                if quantity in [self._KEYS.DISCOVER_DATE, self._KEYS.MAX_DATE]:
                    for ct in my_quantity_list:
                        ctsplit = ct[QUANTITY.VALUE].split('/')
                        svsplit = added_quantity[QUANTITY.VALUE].split('/')
                        if len(ctsplit) < len(svsplit):
                            isworse = False
                            continue
                        elif len(ctsplit) < len(svsplit) and len(svsplit) == 3:
                            val_one = max(
                                2, get_sig_digits(ctsplit[-1].lstrip('0')))
                            val_two = max(
                                2, get_sig_digits(svsplit[-1].lstrip('0')))
                            if val_one < val_two:
                                isworse = False
                                continue
                        newquantities.append(ct)
                else:
                    if type(quantity) != Key:
                        isworse = False
                    elif quantity.type == KEY_TYPES.NUMERIC:
                        newsig = get_sig_digits(added_quantity[QUANTITY.VALUE])
                        for ct in my_quantity_list:
                            addct = False
                            checke = False
                            if (len(quantity.kind_preference) > 0 and not set(
                                    listify(ct.get(QUANTITY.KIND, [])))
                                    .isdisjoint(quantity.kind_preference) and
                                    not set(
                                        listify(
                                            added_quantity.get(QUANTITY.KIND,
                                                               [])))
                                    .isdisjoint(quantity.kind_preference)):
                                aqi = min([
                                    quantity.kind_preference.index(x)
                                    for x in listify(added_quantity[
                                        QUANTITY.KIND])
                                ])
                                qqi = min([
                                    quantity.kind_preference.index(x)
                                    for x in listify(ct[QUANTITY.KIND])
                                ])
                                if aqi > qqi:
                                    addct = True
                                if aqi == qqi:
                                    checke = True
                                if aqi <= qqi:
                                    isworse = False
                            else:
                                checke = True
                            if checke and QUANTITY.E_VALUE in ct:
                                if QUANTITY.E_VALUE in added_quantity:
                                    if (float(added_quantity[QUANTITY.E_VALUE])
                                            >= float(ct[QUANTITY.E_VALUE])):
                                        addct = True
                                    if (float(added_quantity[QUANTITY.E_VALUE])
                                            <= float(ct[QUANTITY.E_VALUE])):
                                        isworse = False
                            else:
                                if (checke and
                                        QUANTITY.E_VALUE in added_quantity):
                                    isworse = False
                                else:
                                    oldsig = get_sig_digits(ct[QUANTITY.VALUE])
                                    if oldsig >= newsig:
                                        addct = True
                                    if newsig >= oldsig:
                                        isworse = False
                            if addct:
                                newquantities.append(ct)
                    elif quantity.type == KEY_TYPES.STRING:
                        for ct in my_quantity_list:
                            addct = False
                            if (len(quantity.kind_preference) > 0 and not set(
                                    listify(ct.get(QUANTITY.KIND, [])))
                                    .isdisjoint(quantity.kind_preference) and
                                    not set(
                                        listify(
                                            added_quantity.get(QUANTITY.KIND,
                                                               [])))
                                    .isdisjoint(quantity.kind_preference)):
                                aqi = min([
                                    quantity.kind_preference.index(x)
                                    for x in listify(added_quantity[
                                        QUANTITY.KIND])
                                ])
                                qqi = min([
                                    quantity.kind_preference.index(x)
                                    for x in listify(ct[QUANTITY.KIND])
                                ])
                                if aqi >= qqi:
                                    addct = True
                                if aqi <= qqi:
                                    isworse = False
                            else:
                                addct = True
                                isworse = False
                            if addct:
                                newquantities.append(ct)

                if isworse:
                    self._log.info("Removing quantity '{}' with value '{}' "
                                   "and kind '{}' determined to be worse than "
                                   "existing alternative values.".format(
                                       quantity, added_quantity[
                                           QUANTITY.VALUE],
                                       added_quantity.get(QUANTITY.KIND, '')))
                else:
                    newquantities.append(added_quantity)
                if len(newquantities) > 0:
                    self[quantity] = newquantities

            # As all SN####xx designations for 2016+ have corresponding AT
            # designations, add the AT alias when the SN alias is added.
            if quantity == self._KEYS.ALIAS:
                for alias in self.get(quantity, []):
                    cleaned_value = alias[QUANTITY.VALUE]
                    if (cleaned_value.startswith('SN') and
                            is_integer(cleaned_value[2:6]) and
                            int(cleaned_value[2:6]) >= 2016):
                        success = super(Supernova, self).add_quantity(
                            SUPERNOVA.ALIAS, 'AT' + cleaned_value[2:], source,
                            **kwargs)

        return True

    def add_source(self, **kwargs):
        # Sanitize some fields before adding source
        # Replace reference names and URLs using dictionaries.
        if (kwargs.get(SOURCE.BIBCODE, []) and
                len(kwargs[SOURCE.BIBCODE]) != 19):
            raise ValueError("Bibcode '{}' must be exactly 19 characters "
                             "long".format(kwargs[SOURCE.BIBCODE]))

        # if SOURCE.NAME not in kwargs:
        #     kwargs[SOURCE.NAME] = kwargs[SOURCE.BIBCODE]

        if SOURCE.NAME in kwargs:
            if (kwargs[SOURCE.NAME].upper().startswith('ATEL') and
                    SOURCE.BIBCODE not in kwargs):
                kwargs[SOURCE.NAME] = (
                    kwargs[SOURCE.NAME].replace('ATEL', 'ATel')
                    .replace('Atel', 'ATel').replace('ATel #', 'ATel ')
                    .replace('ATel#', 'ATel').replace('ATel', 'ATel '))
                kwargs[SOURCE.NAME] = ' '.join(kwargs[SOURCE.NAME].split())
                atelnum = kwargs[SOURCE.NAME].split()[-1]
                if is_number(atelnum) and atelnum in self.catalog.atels_dict:
                    kwargs[SOURCE.BIBCODE] = self.catalog.atels_dict[atelnum]

            if (kwargs[SOURCE.NAME].upper().startswith('CBET') and
                    SOURCE.BIBCODE not in kwargs):
                kwargs[SOURCE.NAME] = kwargs[SOURCE.NAME].replace('CBET',
                                                                  'CBET ')
                kwargs[SOURCE.NAME] = ' '.join(kwargs[SOURCE.NAME].split())
                cbetnum = kwargs[SOURCE.NAME].split()[-1]
                if is_number(cbetnum) and cbetnum in self.catalog.cbets_dict:
                    kwargs[SOURCE.BIBCODE] = self.catalog.cbets_dict[cbetnum]

            if (kwargs[SOURCE.NAME].upper().startswith('IAUC') and
                    SOURCE.BIBCODE not in kwargs):
                kwargs[SOURCE.NAME] = kwargs[SOURCE.NAME].replace('IAUC',
                                                                  'IAUC ')
                kwargs[SOURCE.NAME] = ' '.join(kwargs[SOURCE.NAME].split())
                iaucnum = kwargs[SOURCE.NAME].split()[-1]
                if is_number(iaucnum) and iaucnum in self.catalog.iaucs_dict:
                    kwargs[SOURCE.BIBCODE] = self.catalog.iaucs_dict[iaucnum]

            for rep in self.catalog.source_syns:
                if kwargs[SOURCE.NAME] in self.catalog.source_syns[rep]:
                    kwargs[SOURCE.NAME] = rep
                    break

        if SOURCE.URL in kwargs:
            for rep in self.catalog.url_redirs:
                if kwargs[SOURCE.URL] in self.catalog.url_redirs[rep]:
                    kwargs[SOURCE.URL] = rep
                    break

        return super(Supernova, self).add_source(**kwargs)

    def priority_prefixes(self):
        """Prefixes to given priority to when merging duplicate entries.
        """
        return ('AT', 'SN')

    def add_self_source(self):
        return self.add_source(
            bibcode=self.catalog.OSC_BIBCODE,
            name=self.catalog.OSC_NAME,
            url=self.catalog.OSC_URL,
            secondary=True)

    def extra_aliases(self):
        """These aliases are considered when merging duplicates only, but are
        not added to the list of aliases that would be included with the event
        """
        if (self[SUPERNOVA.NAME].startswith('SN') and
                is_number(self[SUPERNOVA.NAME][2:6])):
            return ['AT' + self[SUPERNOVA.NAME][2:]]
        return []

    def _get_save_path(self, bury=False):
        """Return the path that this Entry should be saved to.

        Determines output repository based on the name (i.e. the year) of the
        supernova.  If `bury` is true, then this entry is saved to the
        'boneyard'.
        """
        self._log.debug("_get_save_path(): {}".format(self.name()))
        filename = self.get_filename(self[self._KEYS.NAME])

        # Put non-SNe in the boneyard
        if bury:
            outdir = self.catalog.PATHS.get_repo_boneyard()

        # Get normal repository save directory
        else:
            repo_folders = self.catalog.PATHS.get_repo_output_folders()
            repo_folders = sorted(repo_folders, key=lambda x: x.split('-')[-1])
            outdir = repo_folders[0]

            if self._KEYS.DISCOVERY_DATE in self.keys():
                repo_years = self.catalog.PATHS.get_repo_years()
                try:
                    dyr = int(self[self._KEYS.DISCOVERY_DATE][0][QUANTITY.VALUE].split(
                        '/')[0])
                except Exception as exc:
                    self._log.warn("Could not extract year from discovery date ({}).".format(repr(exc)))
                else:
                    for r, year in enumerate(repo_years):
                        if int(dyr) <= year:
                            outdir = repo_folders[r]
                            break

        return outdir, filename

    def sanitize(self):
        super(Supernova, self).sanitize()

        # Calculate some columns based on imported data, sanitize some fields
        name = self[self._KEYS.NAME]
        aliases = self.get_aliases()

        if ((name.startswith('SN') and is_number(name[2:6]) and
             self._KEYS.DISCOVER_DATE in self and
             int(self[self._KEYS.DISCOVER_DATE][0][QUANTITY.VALUE].split('/')[
                 0]) >= 2016 and not any(['AT' in x for x in aliases]))):
            source = self.add_self_source()
            self.add_quantity(self._KEYS.ALIAS, 'AT' + name[2:], source)

        if self._KEYS.CLAIMED_TYPE in self:
            # FIX: this is something that should be done completely internally
            #      i.e. add it to `clean` or something??
            self[self._KEYS.CLAIMED_TYPE] = self.ct_list_prioritized()
        if self._KEYS.CLAIMED_TYPE in self:
            self[self._KEYS.CLAIMED_TYPE][:] = [
                ct for ct in self[self._KEYS.CLAIMED_TYPE]
                if ct[QUANTITY.VALUE] not in ['?', '-']
            ]
            if (len(self[self._KEYS.CLAIMED_TYPE]) > 1 and
                any([x[QUANTITY.VALUE].lower() == 'candidate'
                     for x in self[self._KEYS.CLAIMED_TYPE]])):
                self[self._KEYS.CLAIMED_TYPE][:] = [
                    ct for ct in self[self._KEYS.CLAIMED_TYPE]
                    if ct[QUANTITY.VALUE].lower() != 'candidate'
                ]
            if not len(self[self._KEYS.CLAIMED_TYPE]):
                del (self[self._KEYS.CLAIMED_TYPE])
        if self._KEYS.CLAIMED_TYPE not in self and name.startswith('AT'):
            source = self.add_self_source()
            self.add_quantity(self._KEYS.CLAIMED_TYPE, 'Candidate', source)

        if self._KEYS.SOURCES in self:
            for source in self[self._KEYS.SOURCES]:
                if SOURCE.BIBCODE in source:
                    import urllib
                    from html import unescape
                    # First sanitize the bibcode
                    if len(source[SOURCE.BIBCODE]) != 19:
                        source[SOURCE.BIBCODE] = urllib.parse.unquote(
                            unescape(source[SOURCE.BIBCODE])).replace('A.A.',
                                                                      'A&A')
                    if source[SOURCE.BIBCODE] in self.catalog.biberror_dict:
                        source[SOURCE.BIBCODE] = \
                            self.catalog.biberror_dict[source[SOURCE.BIBCODE]]

                    if (source[SOURCE.BIBCODE] not in
                            self.catalog.bibauthor_dict):
                        bibcode = source[SOURCE.BIBCODE]
                        adsquery = (self.catalog.ADS_BIB_URL +
                                    urllib.parse.quote(bibcode) +
                                    '&data_type=Custom&format=%253m%20%25(y)')
                        bibcodeauthor = ''
                        try:
                            response = urllib.request.urlopen(adsquery)
                            html = response.read().decode('utf-8')
                            hsplit = html.split("\n")
                            if len(hsplit) > 5:
                                bibcodeauthor = hsplit[5]
                        except:
                            pass

                        if not bibcodeauthor:
                            warnings.warn(
                                "Bibcode didn't return authors, not converting"
                                "this bibcode.")

                        self.catalog.bibauthor_dict[bibcode] = unescape(
                            bibcodeauthor).strip()

            for source in self[self._KEYS.SOURCES]:
                if (SOURCE.BIBCODE in source and
                        source[SOURCE.BIBCODE] in self.catalog.bibauthor_dict
                        and
                        self.catalog.bibauthor_dict[source[SOURCE.BIBCODE]]):
                    source[SOURCE.REFERENCE] = self.catalog.bibauthor_dict[
                        source[SOURCE.BIBCODE]]
                if (SOURCE.NAME not in source and SOURCE.BIBCODE in source and
                        source[SOURCE.BIBCODE]):
                    source[SOURCE.NAME] = source[SOURCE.BIBCODE]

        if self._KEYS.REDSHIFT in self:
            self[self._KEYS.REDSHIFT] = list(
                sorted(
                    self[self._KEYS.REDSHIFT],
                    key=lambda q: frame_priority(q, self._KEYS.REDSHIFT)))

        if self._KEYS.VELOCITY in self:
            self[self._KEYS.VELOCITY] = list(
                sorted(
                    self[self._KEYS.VELOCITY],
                    key=lambda q: frame_priority(q, self._KEYS.VELOCITY)))

        if self._KEYS.CLAIMED_TYPE in self:
            self[self._KEYS.CLAIMED_TYPE] = self.ct_list_prioritized()

        # Renumber and reorder sources
        if self._KEYS.SOURCES in self:
            # Sort sources reverse-chronologically
            self[self._KEYS.SOURCES] = sorted(
                self[self._KEYS.SOURCES], key=lambda x: bib_priority(x))

            # Assign new aliases to match new order
            source_reps = OrderedDict(
                [[x[SOURCE.ALIAS], str(i + 1)]
                 for i, x in enumerate(self[self._KEYS.SOURCES])])
            for i, source in enumerate(self[self._KEYS.SOURCES]):
                self[self._KEYS.SOURCES][i][SOURCE.ALIAS] = source_reps[source[
                    SOURCE.ALIAS]]

            # Change sources to match new aliases
            for key in self.keys():
                if self._KEYS.get_key_by_name(key).no_source:
                    continue
                for item in self[key]:
                    aliases = [
                        str(y)
                        for y in sorted(
                            int(source_reps[x])
                            for x in item[item._KEYS.SOURCE].split(','))
                    ]
                    item[item._KEYS.SOURCE] = ','.join(aliases)

    def clean_internal(self, data):
        """Clean input data from the 'Supernovae/input/internal' repository.

        FIX: instead of making changes in place to `dirty_event`, should a new
             event be created, values filled, then returned??
        FIX: currently will fail if no bibcode and no url
        """
        self._log.debug("clean_internal(): {}".format(self.name()))

        def_source_dict = {}
        # Find source that will be used as default
        sources = data.get(self._KEYS.SOURCES, [])
        if sources:
            def_source_dict = sources[0]
            allow_alias = False
            if SOURCE.ALIAS in def_source_dict:
                del (def_source_dict[SOURCE.ALIAS])
        else:
            # If there are no existing sources, add OSC as one
            self.add_self_source()
            sources = self.get(self._KEYS.SOURCES, [])
            def_source_dict = sources[0]
            allow_alias = True

        # Clean some legacy fields
        alias_key = 'aliases'
        if alias_key in data:
            # Remove the entry in the data
            aliases = data.pop(alias_key)
            # Make sure this is a list
            if not isinstance(aliases, list):
                raise ValueError("{}: aliases not a list '{}'".format(
                    self.name(), aliases))
            # Add OSC source entry
            source = self.add_self_source()

            for alias in aliases:
                self.add_quantity(self._KEYS.ALIAS, alias, source)

        dist_key = 'distinctfrom'
        if dist_key in data:
            distincts = data.pop(dist_key)
            if ((isinstance(distincts, list) and
                 isinstance(distincts[0], string_types))):
                source = self.add_self_source()
                for df in distincts:
                    self.add_quantity(self._KEYS.DISTINCT_FROM, df, source)
            else:
                data[dist_key] = list(distincts)

        # Go through all remaining keys in 'dirty' event, and make sure
        # everything is a quantity with a source (OSC if no other)
        for key in data.keys():
            # The following line should be used to replace the above once keys
            # returns the superclass keys too
            if self._KEYS.get_key_by_name(key).no_source:
                pass
            elif key == self._KEYS.PHOTOMETRY:
                for p, photo in enumerate(data[self._KEYS.PHOTOMETRY]):
                    if photo.get(PHOTOMETRY.U_TIME) == 'JD':
                        data[self._KEYS.PHOTOMETRY][p][
                            PHOTOMETRY.U_TIME] = 'MJD'
                        data[self._KEYS.PHOTOMETRY][p][PHOTOMETRY.TIME] = str(
                            jd_to_mjd(Decimal(photo['time'])))
                    if QUANTITY.SOURCE not in photo:
                        if not def_source_dict:
                            raise ValueError("No sources found, can't add "
                                             "photometry.")
                        source = self.add_source(
                            allow_alias=allow_alias, **def_source_dict)
                        data[self._KEYS.PHOTOMETRY][p][
                            QUANTITY.SOURCE] = source
            else:
                for qi, quantity in enumerate(data[key]):
                    if QUANTITY.SOURCE not in quantity:
                        if not def_source_dict:
                            raise ValueError("No sources found, can't add "
                                             "quantity.")
                        source = self.add_source(
                            allow_alias=allow_alias, **def_source_dict)
                        data[key][qi][QUANTITY.SOURCE] = source

        return data

    def _get_max_light(self, visual=False):
        if self._KEYS.PHOTOMETRY not in self:
            return (None, None, None, None)

        eventphoto = [
            (x[PHOTOMETRY.U_TIME], Decimal(x[PHOTOMETRY.TIME])
             if not isinstance(x[PHOTOMETRY.TIME], list) else
             Decimal(np.mean([float(y) for y in x[PHOTOMETRY.TIME]])),
             Decimal(x[PHOTOMETRY.MAGNITUDE]), x.get(PHOTOMETRY.BAND, ''),
             x[PHOTOMETRY.SOURCE]) for x in self[self._KEYS.PHOTOMETRY]
            if (PHOTOMETRY.MAGNITUDE in x and PHOTOMETRY.TIME in x and x.get(
                PHOTOMETRY.U_TIME, '') == 'MJD' and PHOTOMETRY.UPPER_LIMIT
                not in x and not x.get(PHOTOMETRY.INCLUDES_HOST, False))
        ]
        # Use photometry that includes host if no other photometry available.
        if not eventphoto:
            eventphoto = [
                (x[PHOTOMETRY.U_TIME], Decimal(x[PHOTOMETRY.TIME])
                 if not isinstance(x[PHOTOMETRY.TIME], list) else
                 Decimal(np.mean([float(y) for y in x[PHOTOMETRY.TIME]])),
                 Decimal(x[PHOTOMETRY.MAGNITUDE]), x.get(PHOTOMETRY.BAND, ''),
                 x[PHOTOMETRY.SOURCE]) for x in self[self._KEYS.PHOTOMETRY]
                if (PHOTOMETRY.MAGNITUDE in x and PHOTOMETRY.TIME in x and
                    x.get(PHOTOMETRY.U_TIME, '') == 'MJD' and not x.get(
                        PHOTOMETRY.INCLUDES_HOST, False))
            ]
        if not eventphoto:
            return None, None, None, None

        mlmag = None

        if visual:
            for mb in MAX_VISUAL_BANDS:
                leventphoto = [x for x in eventphoto if x[3] in mb]
                if leventphoto:
                    mlmag = min([x[2] for x in leventphoto])
                    eventphoto = leventphoto
                    break

        if not mlmag:
            mlmag = min([x[2] for x in eventphoto])

        mlindex = [x[2] for x in eventphoto].index(mlmag)
        mlband = eventphoto[mlindex][3]
        mlsource = eventphoto[mlindex][4]

        if eventphoto[mlindex][0] == 'MJD':
            mlmjd = float(eventphoto[mlindex][1])
            mlmjd = astrotime(mlmjd, format='mjd').datetime
            return mlmjd, mlmag, mlband, mlsource
        else:
            return None, mlmag, mlband, mlsource

    def _get_first_light(self):
        if self._KEYS.PHOTOMETRY not in self:
            return None, None

        eventphoto = [(Decimal(x[PHOTOMETRY.TIME])
                       if not isinstance(x[PHOTOMETRY.TIME], list) else
                       Decimal(min(float(y) for y in x[PHOTOMETRY.TIME])),
                       x[PHOTOMETRY.SOURCE])
                      for x in self[self._KEYS.PHOTOMETRY]
                      if PHOTOMETRY.UPPER_LIMIT not in x and PHOTOMETRY.TIME in
                      x and x.get(PHOTOMETRY.U_TIME, '') == 'MJD' and
                      PHOTOMETRY.INCLUDES_HOST not in x]
        # Use photometry that includes host if no other photometry available.
        if not eventphoto:
            eventphoto = [
                (Decimal(x[PHOTOMETRY.TIME])
                 if not isinstance(x[PHOTOMETRY.TIME], list) else
                 Decimal(min(float(y) for y in x[PHOTOMETRY.TIME])),
                 x[PHOTOMETRY.SOURCE]) for x in self[self._KEYS.PHOTOMETRY]
                if PHOTOMETRY.UPPER_LIMIT not in x and PHOTOMETRY.TIME in x and
                x.get(PHOTOMETRY.U_TIME, '') == 'MJD'
            ]
        if not eventphoto:
            return None, None
        flmjd = min([x[0] for x in eventphoto])
        flindex = [x[0] for x in eventphoto].index(flmjd)
        flmjd = astrotime(float(flmjd), format='mjd').datetime
        flsource = eventphoto[flindex][1]
        return flmjd, flsource

    def set_first_max_light(self):
        if SUPERNOVA.MAX_APP_MAG not in self:
            # Get the maximum amongst all bands
            mldt, mlmag, mlband, mlsource = self._get_max_light()
            if mldt or mlmag or mlband:
                source = self.add_self_source()
                uniq_src = uniq_cdl([source] + mlsource.split(','))
            if mldt:
                max_date = make_date_string(mldt.year, mldt.month, mldt.day)
                self.add_quantity(
                    SUPERNOVA.MAX_DATE, max_date, uniq_src, derived=True)
            if mlmag:
                mlmag = pretty_num(mlmag)
                self.add_quantity(
                    SUPERNOVA.MAX_APP_MAG, mlmag, uniq_src, derived=True)
            if mlband:
                self.add_quantity(
                    SUPERNOVA.MAX_BAND, mlband, uniq_src, derived=True)

        if SUPERNOVA.MAX_VISUAL_APP_MAG not in self:
            # Get the "visual" maximum
            mldt, mlmag, mlband, mlsource = self._get_max_light(visual=True)
            if mldt or mlmag or mlband:
                source = self.add_self_source()
                uniq_src = uniq_cdl([source] + mlsource.split(','))
            if mldt:
                max_date = make_date_string(mldt.year, mldt.month, mldt.day)
                self.add_quantity(
                    SUPERNOVA.MAX_VISUAL_DATE,
                    max_date,
                    uniq_src,
                    derived=True)
            if mlmag:
                mlmag = pretty_num(mlmag)
                self.add_quantity(
                    SUPERNOVA.MAX_VISUAL_APP_MAG,
                    mlmag,
                    uniq_src,
                    derived=True)
            if mlband:
                self.add_quantity(
                    SUPERNOVA.MAX_VISUAL_BAND, mlband, uniq_src, derived=True)

        if (self._KEYS.DISCOVER_DATE not in self or max([
                len(x[QUANTITY.VALUE].split('/'))
                for x in self[self._KEYS.DISCOVER_DATE]
        ]) < 3):
            fldt, flsource = self._get_first_light()
            if fldt:
                source = self.add_self_source()
                disc_date = make_date_string(fldt.year, fldt.month, fldt.day)
                self.add_quantity(
                    self._KEYS.DISCOVER_DATE,
                    disc_date,
                    uniq_cdl([source] + flsource.split(',')),
                    derived=True)

        if self._KEYS.DISCOVER_DATE not in self and self._KEYS.SPECTRA in self:
            minspecmjd = float("+inf")
            for spectrum in self[self._KEYS.SPECTRA]:
                if 'time' in spectrum and 'u_time' in spectrum:
                    if spectrum['u_time'] == 'MJD':
                        mjd = float(spectrum['time'])
                    elif spectrum['u_time'] == 'JD':
                        mjd = float(jd_to_mjd(Decimal(spectrum['time'])))
                    else:
                        continue

                    if mjd < minspecmjd:
                        minspecmjd = mjd
                        minspecsource = spectrum['source']

            if minspecmjd < float("+inf"):
                fldt = astrotime(minspecmjd, format='mjd').datetime
                source = self.add_self_source()
                disc_date = make_date_string(fldt.year, fldt.month, fldt.day)
                self.add_quantity(
                    self._KEYS.DISCOVER_DATE,
                    disc_date,
                    uniq_cdl([source] + minspecsource.split(',')),
                    derived=True)
        return

    def purge_bandless_photometry(self):
        """This function removes photometry without band information in cases
        where photometry with band information exists before and after the
        bandless photometry, in such cases the bandless photometry is not
        providing additional information.
        """
        if SUPERNOVA.PHOTOMETRY not in self:
            return
        mjds = [
            np.mean([float(x) for x in listify(
                x[PHOTOMETRY.TIME])]) for x in self[SUPERNOVA.PHOTOMETRY]
            if (PHOTOMETRY.TIME in x and x.get(PHOTOMETRY.U_TIME, '') == 'MJD'
                and PHOTOMETRY.MAGNITUDE in x and PHOTOMETRY.BAND in x)
        ]
        if not mjds:
            return
        minmjd = min(mjds) - 1
        maxmjd = max(mjds) + 1
        newphotos = []
        for photo in self[SUPERNOVA.PHOTOMETRY]:
            ptime = np.mean([float(x) for x in listify(
                photo[PHOTOMETRY.TIME])]) if PHOTOMETRY.TIME in photo else None
            if (PHOTOMETRY.MAGNITUDE in photo and
                    PHOTOMETRY.BAND not in photo and
                (PHOTOMETRY.TIME not in photo or
                 PHOTOMETRY.U_TIME not in photo or
                 (float(ptime) >= minmjd and float(ptime) <= maxmjd))):
                self._log.info("Purging photometry without band information, "
                               "MJD: {}, Mag: {}".format(
                                   'N/A' if ptime is None else ptime,
                                   photo.get(PHOTOMETRY.MAGNITUDE, 'N/A')))
                continue
            newphotos.append(photo)
        self[SUPERNOVA.PHOTOMETRY] = newphotos
        return

    def get_best_redshift(self, key=SUPERNOVA.REDSHIFT):
        bestsig = -1
        bestkind = None
        for z in self[key]:
            try:
                kind = min([
                    z.kind_preference.index(x)
                    for x in listify(z.get(QUANTITY.KIND, []))
                ])
            except:
                kind = None
            sig = get_sig_digits(z[QUANTITY.VALUE])
            if (sig > bestsig and ((kind is None and bestkind is None) or
                                   kind <= bestkind)):
                bestz = z[QUANTITY.VALUE]
                bestkind = kind
                bestsig = sig
                bestsrc = z[QUANTITY.SOURCE]

        return bestz, bestkind, bestsig, bestsrc

    def set_preferred_name(self):
        """Set preferred name of supernova.

        Highest preference goes to names of the form 'SN####AA'.
        Otherwise base the name on whichever survey is the 'discoverer'.

        FIX: create function to match SN####AA type names.
        """
        name = self[self._KEYS.NAME]
        newname = ''
        aliases = self.get_aliases()
        # if there are no other options to choose from, skip
        if len(aliases) <= 1:
            return name
        # If the name is already in the form 'SN####AA' then keep using
        # that
        if (name.startswith('SN') and
            ((is_number(name[2:6]) and not is_number(name[6:])) or
             (is_number(name[2:5]) and not is_number(name[5:])))):
            return name
        # If one of the aliases is in the form 'SN####AA' then use that
        for alias in aliases:
            if (alias.startswith('SN') and
                ((is_number(alias[2:6]) and not is_number(alias[6:])) or
                 (is_number(alias[2:5]) and not is_number(alias[5:])))):
                newname = alias
                break
        # If not, name based on the 'discoverer' survey
        if not newname and SUPERNOVA.DISCOVERER in self:
            discoverer = ','.join(
                [x['value'].upper() for x in self[SUPERNOVA.DISCOVERER]])
            if 'ASAS' in discoverer:
                for alias in aliases:
                    if 'ASASSN' in alias.upper():
                        newname = alias
                        break
            if not newname and 'OGLE' in discoverer:
                for alias in aliases:
                    if 'OGLE' in alias.upper():
                        newname = alias
                        break
            if not newname and 'CRTS' in discoverer:
                for alias in aliases:
                    if True in [
                            x in alias.upper()
                            for x in ['CSS', 'MLS', 'SSS', 'SNHUNT']
                    ]:
                        newname = alias
                        break
            if not newname and 'PS1' in discoverer:
                for alias in aliases:
                    if 'PS1' in alias.upper():
                        newname = alias
                        break
            if not newname and 'PTF' in discoverer:
                for alias in aliases:
                    if 'PTF' in alias.upper():
                        newname = alias
                        break
            if not newname and 'la silla-quest' in discoverer.lower():
                for alias in aliases:
                    if 'LSQ' in alias.upper():
                        newname = alias
                        break
            if not newname and 'GAIA' in discoverer:
                for alias in aliases:
                    if 'GAIA' in alias.upper():
                        newname = alias
                        break
        # If one of the aliases is in the form 'AT####AA' then use that
        if not newname:
            for alias in aliases:
                if (alias.startswith('AT') and
                    ((is_number(alias[2:6]) and not is_number(alias[6:])) or
                     (is_number(alias[2:5]) and not is_number(alias[5:])))):
                    newname = alias
                    break
        # Otherwise, use the shortest name.
        if not newname:
            newname = min(aliases, key=len)
        # Always prefer another alias over PSN
        if not newname and name.startswith('PSN'):
            for alias in aliases:
                if not alias.startswith('PSN'):
                    newname = alias
        if newname and name != newname:
            file_entry = None
            # Make sure new name doesn't already exist
            if newname in self.catalog.entries:
                if self.catalog.entries[newname]._stub:
                    file_entry = self.init_from_file(
                        self.catalog, name=newname)
                else:
                    file_entry = self.catalog.entries[newname]

            if file_entry:
                self._log.info("`{}` already exists, copying `{}` to it".
                               format(newname, name))
                self.catalog.copy_entry_to_entry(
                    self.catalog.entries[name], file_entry)
                self.catalog.entries[newname] = file_entry
            else:
                self._log.info("Changing entry from name '{}' to preferred"
                               " name '{}'".format(name, newname))
                self.catalog.entries[newname] = self.catalog.entries[name]
                self.catalog.entries[newname][self._KEYS.NAME] = newname
            del self.catalog.entries[name]
            return newname

        return name

    def ct_list_prioritized(self):
        ct_list = list(
            sorted(
                self[self._KEYS.CLAIMED_TYPE],
                key=lambda key: self._ct_priority(key)))
        return ct_list

    def _ct_priority(self, attr):
        aliases = attr['source'].split(',')
        max_source_year = -10000
        vaguetypes = ['CC', 'I']
        if attr[QUANTITY.VALUE] in vaguetypes:
            return -max_source_year
        for alias in aliases:
            if alias == 'D':
                continue
            source = self.get_source_by_alias(alias)
            if SOURCE.BIBCODE in source:
                source_year = get_source_year(source)
                if source_year > max_source_year:
                    max_source_year = source_year
        return -max_source_year
