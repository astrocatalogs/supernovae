"""Supernovae specific catalog class."""
import codecs
import json
from collections import OrderedDict
from datetime import datetime

from astrocats.structures.catalog import Catalog
from astrocats.structures.struct import QUANTITY
from astrocats.utils import read_json_arr, read_json_dict

from supernovae import PATHS as _PATHS

from .supernova import SUPERNOVA, Supernova
from .utils import name_clean


class SupernovaCatalog(Catalog):
    """Catalog class for `Supernova` objects."""

    MODULE_NAME = "supernovae"
    PATHS = _PATHS

    def __init__(self, args, log):
        """Initialize catalog."""
        # Initialize super `astrocats.structures.catalog.Catalog` object
        super(SupernovaCatalog, self).__init__(args, log)
        self.proto = Supernova
        self._load_aux_data()
        return

    def should_bury(self, name):
        """Determine whether an entry should be "buried".

        An entry would be buried if it does not belong to the class of object
        associated with the given catalog.
        """
        (bury_entry, save_entry) = super(
            SupernovaCatalog, self).should_bury(name)

        ct_val = None
        if name.startswith(tuple(self.nonsneprefixes_dict)):
            self.log.debug(
                "Killing '{}', non-SNe prefix.".format(name))
            save_entry = False
        else:
            if SUPERNOVA.CLAIMED_TYPE in self.entries[name]:
                for ct in self.entries[name][SUPERNOVA.CLAIMED_TYPE]:
                    up_val = ct[QUANTITY.VALUE].upper().replace('?', '')
                    up_types = [x.upper() for x in self.nonsnetypes]
                    if up_val not in up_types and up_val != 'CANDIDATE':
                        bury_entry = False
                        save_entry = True
                        break
                    if up_val in up_types:
                        bury_entry = True
                        ct_val = ct[QUANTITY.VALUE]
            else:
                if (SUPERNOVA.DISCOVER_DATE in self.entries[name] and
                    any([x.get(QUANTITY.VALUE).startswith('AT')
                         for x in self.entries[name][SUPERNOVA.ALIAS]]) and
                    not any([x.get(QUANTITY.VALUE).startswith('SN')
                             for x in self.entries[name][SUPERNOVA.ALIAS]])):
                    try:
                        try:
                            dd = datetime.strptime(self.entries[name][
                                SUPERNOVA.DISCOVER_DATE][0].get('value', ''),
                                '%Y/%m/%d')
                        except ValueError:
                            dd = datetime.strptime(self.entries[name][
                                SUPERNOVA.DISCOVER_DATE][0].get('value', '') +
                                '/12/31',
                                '%Y')
                    except ValueError:
                        pass
                    else:
                        diff = datetime.today() - dd
                        # Because of the TNS, many non-SNe beyond 2016.
                        if dd.year >= 2016 and diff.days > 180:
                            save_entry = False

            if not save_entry:
                self.log.warning(
                    "Not saving '{}', {}.".format(name, ct_val))
            elif bury_entry:
                self.log.info(
                    "Burying '{}', {}.".format(name, ct_val))

        return (bury_entry, save_entry)

    def _load_aux_data(self):
        """Load auxiliary dictionaries for use in this catalog."""
        # Create/Load auxiliary dictionaries
        self.nedd_dict = OrderedDict()
        self.bibauthor_dict = read_json_dict(self.PATHS.AUTHORS_FILE)
        self.biberror_dict = read_json_dict(self.PATHS.BIBERRORS)
        self.extinctions_dict = read_json_dict(self.PATHS.EXTINCT)
        self.iaucs_dict = read_json_dict(self.PATHS.IAUCS)
        self.cbets_dict = read_json_dict(self.PATHS.CBETS)
        self.atels_dict = read_json_dict(self.PATHS.ATELS)
        self.source_syns = read_json_dict(self.PATHS.SOURCE_SYNONYMS)
        self.url_redirs = read_json_dict(self.PATHS.URL_REDIRECTS)
        self.type_syns = read_json_dict(self.PATHS.TYPE_SYNONYMS)
        # Create/Load auxiliary arrays
        self.nonsneprefixes_dict = read_json_arr(
            self.PATHS.NON_SNE_PREFIXES)
        self.nonsnetypes = read_json_arr(self.PATHS.NON_SNE_TYPES)
        return

    def save_caches(self):
        """Save caches to JSON files."""
        jsonstring = json.dumps(self.bibauthor_dict, indent='\t',
                                separators=(',', ':'), ensure_ascii=False)
        with codecs.open(self.PATHS.AUTHORS_FILE, 'w', encoding='utf8') as f:
            f.write(jsonstring)
        jsonstring = json.dumps(self.extinctions_dict, indent='\t',
                                separators=(',', ':'), ensure_ascii=False)
        with codecs.open(self.PATHS.EXTINCT, 'w', encoding='utf8') as f:
            f.write(jsonstring)

    def clean_entry_name(self, name):
        """Clean entry's name."""
        return name_clean(name)
