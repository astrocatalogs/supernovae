"""Supernovae specific catalog class.
"""
import codecs
import json
import os
from collections import OrderedDict
from subprocess import check_output

from astrocats.catalog.catalog import Catalog
from astrocats.catalog.utils import pbar, read_json_arr, read_json_dict

from .supernova import SUPERNOVA, Supernova
from .utils import name_clean


class SupernovaCatalog(Catalog):

    class PATHS(Catalog.PATHS):

        PATH_BASE = os.path.abspath(os.path.dirname(__file__))

        def __init__(self, catalog):
            super().__init__(catalog)
            # auxiliary datafiles
            self.TYPE_SYNONYMS = os.path.join(
                self.PATH_INPUT, 'type-synonyms.json')
            self.SOURCE_SYNONYMS = os.path.join(
                self.PATH_INPUT, 'source-synonyms.json')
            self.URL_REDIRECTS = os.path.join(
                self.PATH_INPUT, 'url-redirects.json')
            self.NON_SNE_TYPES = os.path.join(
                self.PATH_INPUT, 'non-sne-types.json')
            self.NON_SNE_PREFIXES = os.path.join(
                self.PATH_INPUT, 'non-sne-prefixes.json')
            self.BIBERRORS = os.path.join(self.PATH_INPUT, 'biberrors.json')
            self.ATELS = os.path.join(self.PATH_INPUT, 'atels.json')
            self.CBETS = os.path.join(self.PATH_INPUT, 'cbets.json')
            self.IAUCS = os.path.join(self.PATH_INPUT, 'iaucs.json')
            # cached datafiles
            self.BIBAUTHORS = os.path.join(
                self.PATH_OUTPUT, 'cache', 'bibauthors.json')
            self.EXTINCT = os.path.join(
                self.PATH_OUTPUT, 'cache', 'extinctions.json')

        def get_repo_years(self):
            """
            """
            repo_folders = self.get_repo_output_folders(bones=False)
            repo_years = [int(repo_folders[x][-4:])
                          for x in range(len(repo_folders))]
            repo_years[0] -= 1
            return repo_years

    class SCHEMA:
        HASH = (check_output(['git', 'log', '-n', '1', '--format="%H"',
                              '--',
                              'OSC-JSON-format.md'])
                .decode('ascii').strip().strip('"').strip())
        URL = ('https://github.com/astrocatalogs/sne/blob/' + HASH +
               '/OSC-JSON-format.md')

    def __init__(self, args, log):
        """
        """
        # Initialize super `astrocats.catalog.catalog.Catalog` object
        super().__init__(args, log)
        self.proto = Supernova
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
                    if up_val not in self.nonsnetypes and \
                            up_val != 'CANDIDATE':
                        bury_entry = False
                        break
                    if up_val in self.nonsnetypes:
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
        self.bibauthor_dict = read_json_dict(self.PATHS.BIBAUTHORS)
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
        jsonstring = json.dumps(self.bibauthor_dict, indent='\t',
                                separators=(',', ':'), ensure_ascii=False)
        with codecs.open(self.PATHS.BIBAUTHORS, 'w', encoding='utf8') as f:
            f.write(jsonstring)
        jsonstring = json.dumps(self.extinctions_dict, indent='\t',
                                separators=(',', ':'), ensure_ascii=False)
        with codecs.open(self.PATHS.EXTINCT, 'w', encoding='utf8') as f:
            f.write(jsonstring)

    def clone_repos(self):
        # Load the local 'supernovae' repository names
        all_repos = self.PATHS.get_repo_input_folders()
        all_repos += self.PATHS.get_repo_output_folders()
        super()._clone_repos(all_repos)
        return

    def clean_entry_name(self, name):
        return name_clean(name)

    def set_preferred_names(self):
        """Choose between each entries given name and its possible aliases for
        the best one.

        Highest preference goes to names of the form 'SN####AA'.
        Otherwise base the name on whichever survey is the 'discoverer'.

        FIX: create function to match SN####AA type names.
        """
        if len(self.entries) == 0:
            self.log.error("WARNING: `entries` is empty, loading stubs")
            self.load_stubs()

        task_str = self.get_current_task_str()
        for ni, oname in enumerate(pbar(self.entries, task_str)):
            name = self.add_entry(oname)
            self[name].set_preferred_name()

            if self.args.travis and ni > self.TRAVIS_QUERY_LIMIT:
                break

        return
