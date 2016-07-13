"""Supernovae specific catalog class.
"""
import codecs
import json
import os
from collections import OrderedDict
from subprocess import check_output

from astrocats.catalog.catalog import Catalog
from astrocats.catalog.utils import (is_number, pbar, read_json_arr,
                                     read_json_dict)
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
        for ni, name in enumerate(pbar(list(
                sorted(self.entries.keys())), task_str)):
            newname = ''
            aliases = self.entries[name].get_aliases()
            # if there are no other options to choose from, skip
            if len(aliases) <= 1:
                continue
            # If the name is already in the form 'SN####AA' then keep using
            # that
            if (name.startswith('SN') and
                ((is_number(name[2:6]) and not is_number(name[6:])) or
                 (is_number(name[2:5]) and not is_number(name[5:])))):
                continue
            # If one of the aliases is in the form 'SN####AA' then use that
            for alias in aliases:
                if (alias[:2] == 'SN' and
                    ((is_number(alias[2:6]) and not is_number(alias[6:])) or
                     (is_number(alias[2:5]) and not is_number(alias[5:])))):
                    newname = alias
                    break
            # Otherwise, name based on the 'discoverer' survey
            if not newname and 'discoverer' in self.entries[name]:
                discoverer = ','.join(
                    [x['value'].upper() for x in
                     self.entries[name]['discoverer']])
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
                        if True in [x in alias.upper()
                                    for x in ['CSS', 'MLS', 'SSS', 'SNHUNT']]:
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
                if not newname and 'GAIA' in discoverer:
                    for alias in aliases:
                        if 'GAIA' in alias.upper():
                            newname = alias
                            break
            # Always prefer another alias over PSN
            if not newname and name.startswith('PSN'):
                newname = aliases[0]
            if newname and name != newname:
                # Make sure new name doesn't already exist
                if self.proto.init_from_file(self, name=newname):
                    self.log.error("WARNING: `newname` already exists... "
                                   "should do something about that...")
                    continue

                new_entry = self.proto.init_from_file(self, name=name)
                if new_entry is None:
                    self.log.error(
                        "Could not load `new_entry` with name '{}'"
                        .format(name))
                else:
                    self.log.info("Changing entry from name '{}' to preferred"
                                  " name '{}'".format(name, newname))
                    self._delete_entry_file(entry=new_entry)
                    del self.entries[name]
                    self.entries[newname] = new_entry
                    self.entries[newname][self.proto._KEYS.NAME] = newname
                    if name in self.entries:
                        self.log.error(
                            "WARNING: `name` = '{}' is in `entries` "
                            "shouldnt happen?".format(name))
                        del self.entries[name]
                    self.journal_entries()

            if self.args.travis and ni > self.TRAVIS_QUERY_LIMIT:
                break

        return
