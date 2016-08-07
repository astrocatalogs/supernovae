"""Supernovae specific catalog class.
"""
import codecs
import json
import os
from collections import OrderedDict
from subprocess import check_output

from astrocats.catalog.catalog import Catalog
from astrocats.catalog.utils import read_json_arr, read_json_dict

from .supernova import SUPERNOVA, Supernova
from .paths import Paths
from .utils import name_clean


class SupernovaCatalog(Catalog):

    class SCHEMA:
        HASH = (check_output(['git', 'log', '-n', '1', '--format="%H"',
                              '--',
                              'OSC-JSON-format.md'])
                .decode('ascii').strip().strip('"').strip())
        URL = ('https://github.com/astrocatalogs/astrocats/blob/' + HASH +
               '/OSC-JSON-format.md')

    def __init__(self, args, log):
        """
        """
        # Initialize super `astrocats.catalog.catalog.Catalog` object
        super().__init__(args, log)
        self.proto = Supernova
        self.paths = Paths(self, log)
        self._load_aux_data()
        return

    def should_bury(self, name):
        """Determines whether an event should be "buried" because it does not
        belong to the class of object associated with the given catalog.
        """
        (bury_entry, save_entry) = super().should_bury(name)

        ct_val = None
        if name.startswith(tuple(self.nonsneprefixes_dict)):
            self.log.debug(
                "Killing '{}', non-SNe prefix.".format(name))
            save_entry = False
        else:
            if SUPERNOVA.CLAIMED_TYPE in self.entries[name]:
                for ct in self.entries[name][SUPERNOVA.CLAIMED_TYPE]:
                    up_val = ct['value'].upper()
                    up_types = [x.upper() for x in self.nonsnetypes]
                    if up_val not in up_types and \
                            up_val != 'CANDIDATE':
                        bury_entry = False
                        break
                    if up_val in up_types:
                        bury_entry = True
                        ct_val = ct['value']

            if bury_entry:
                self.log.debug(
                    "Burying '{}', {}.".format(name, ct_val))

        return (bury_entry, save_entry)

    def _load_aux_data(self):
        """Load auxiliary dictionaries for use in this catalog.
        """
        # Create/Load auxiliary dictionaries
        self.nedd_dict = OrderedDict()
        self.bibauthor_dict = read_json_dict(self.paths.BIBAUTHORS)
        self.biberror_dict = read_json_dict(self.paths.BIBERRORS)
        self.extinctions_dict = read_json_dict(self.paths.EXTINCT)
        self.iaucs_dict = read_json_dict(self.paths.IAUCS)
        self.cbets_dict = read_json_dict(self.paths.CBETS)
        self.atels_dict = read_json_dict(self.paths.ATELS)
        self.source_syns = read_json_dict(self.paths.SOURCE_SYNONYMS)
        self.url_redirs = read_json_dict(self.paths.URL_REDIRECTS)
        self.type_syns = read_json_dict(self.paths.TYPE_SYNONYMS)
        # Create/Load auxiliary arrays
        self.nonsneprefixes_dict = read_json_arr(
            self.paths.NON_SNE_PREFIXES)
        self.nonsnetypes = read_json_arr(self.paths.NON_SNE_TYPES)
        return

    def save_caches(self):
        jsonstring = json.dumps(self.bibauthor_dict, indent='\t',
                                separators=(',', ':'), ensure_ascii=False)
        with codecs.open(self.paths.BIBAUTHORS, 'w', encoding='utf8') as f:
            f.write(jsonstring)
        jsonstring = json.dumps(self.extinctions_dict, indent='\t',
                                separators=(',', ':'), ensure_ascii=False)
        with codecs.open(self.paths.EXTINCT, 'w', encoding='utf8') as f:
            f.write(jsonstring)

    def clone_repos(self):
        # Load the local 'supernovae' repository names
        all_repos = self.paths.get_repo_input_folders()
        all_repos += self.paths.get_repo_output_folders()
        super()._clone_repos(all_repos)
        return

    def clean_entry_name(self, name):
        return name_clean(name)
