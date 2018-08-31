"""The Supernova AstroCatalog.
"""

import astrocats
import os

catalog_info = {
    "catalog_name": __name__,
    "catalog_class": {
        "name": "SupernovaCatalog",
        "file": "supernovacatalog",
        "path": "supernovae."
    },
    "schema_path": None
}


class Supernova_Paths(astrocats.Paths):
    """Paths to catalog inputs/outputs."""

    ROOT = os.path.join(os.path.dirname(__file__), "")
    NAME = __name__
    FILE = __file__

    BASE = os.path.abspath(os.path.dirname(__file__))

    def __init__(self):
        """Initialize paths."""
        super(Supernova_Paths, self).__init__()
        # auxiliary datafiles
        self.TYPE_SYNONYMS = os.path.join(
            self.INPUT, 'type-synonyms.json')
        self.SOURCE_SYNONYMS = os.path.join(
            self.INPUT, 'source-synonyms.json')
        self.URL_REDIRECTS = os.path.join(
            self.INPUT, 'url-redirects.json')
        self.NON_SNE_TYPES = os.path.join(
            self.INPUT, 'non-sne-types.json')
        self.NON_SNE_PREFIXES = os.path.join(
            self.INPUT, 'non-sne-prefixes.json')
        self.BIBERRORS = os.path.join(self.INPUT, 'biberrors.json')
        self.ATELS = os.path.join(self.INPUT, 'atels.json')
        self.CBETS = os.path.join(self.INPUT, 'cbets.json')
        self.IAUCS = os.path.join(self.INPUT, 'iaucs.json')
        # cached datafiles
        self.EXTINCT = os.path.join(
            self.CACHE, 'extinctions.json')

    def get_repo_years(self):
        """Return an array of years based upon output repositories."""
        repo_folders = self.get_repo_output_folders(bones=False)
        repo_years = [int(repo_folders[x][-4:])
                      for x in range(len(repo_folders))]
        repo_years[0] -= 1
        return repo_years


PATHS = Supernova_Paths()
