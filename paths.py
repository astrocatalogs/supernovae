"""
"""
from glob import glob
import os
import sys

import astrocats
from astrocats import main, _ROOT_BASE_PATH
from astrocats.catalog.utils import read_json_dict, repo_priority


class Paths(astrocats.catalog.paths.Paths):
    """
    """

    def __init__(self, catalog=None, log=None):
        super().__init__(catalog=catalog, log=log)

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

        return

    def get_repo_years(self):
        """
        """
        repo_folders = self.get_repo_output_folders(bones=False)
        repo_years = [int(repo_folders[x][-4:])
                      for x in range(len(repo_folders))]
        repo_years[0] -= 1
        return repo_years
