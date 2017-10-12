"""Import tasks related to MOSFiT."""
import os
from glob import glob

import dropbox

from astrocats.catalog.utils import pbar
from astrocats.supernovae.supernova import Supernova, SUPERNOVA
from astrocats.catalog.photometry import PHOTOMETRY


def do_mosfit(catalog):
    """Import models produced by MOSFiT from Dropbox."""
    REALIZATION_LIMIT = 10

    task_str = catalog.get_current_task_str()
    try:
        with open('mosfit.key', 'r') as f:
            mosfitkey = f.read().splitlines()[0]
    except Exception:
        catalog.log.warning('MOSFiT key not found, make sure a file named '
                            '`mosfit.key` containing the key is placed the '
                            'astrocats directory.')
        mosfitkey = ''

    dbx = dropbox.Dropbox(mosfitkey)
    files = list(sorted([
        x.name for x in dbx.files_list_folder('').entries
        if not x.name.startswith('.')
    ]))
    fdir = os.path.join(catalog.get_current_task_repo(), 'MOSFiT')
    if not os.path.isdir(fdir):
        os.mkdir(fdir)
    efiles = [x.split('/')[-1] for x in glob(os.path.join(fdir, '*'))]
    old_name = ''
    for fname in pbar(files, desc=task_str):
        if fname in efiles:
            efiles.remove(fname)
        fpath = os.path.join(fdir, fname)
        if not os.path.isfile(fpath):
            md, res = dbx.files_download('/' + fname)
            jtxt = res.content
            with open(fpath, 'wb') as f:
                f.write(jtxt)

        new_entry = Supernova.init_from_file(
            catalog, path=fpath, compare_to_existing=False, try_gzip=True,
            clean=False, merge=False, filter_on={
                'realization': [str(x) for x in range(1, REALIZATION_LIMIT)]})

        name = new_entry[SUPERNOVA.NAME]

        # Only take a number of realizations up to the realization limit.
        new_photo = []
        for photo in new_entry[SUPERNOVA.PHOTOMETRY]:
            real = int(photo.get(PHOTOMETRY.REALIZATION, -1))
            if real < 0 or real >= REALIZATION_LIMIT:
                continue
            new_photo.append(photo)
        new_entry[SUPERNOVA.PHOTOMETRY] = new_photo

        old_entry = None
        if name in catalog.entries:
            if catalog.entries[name]._stub:
                old_entry = Supernova.init_from_file(
                    catalog, name=name, compare_to_existing=False)
            else:
                old_entry = catalog.entries[name]

        if old_entry:
            catalog.copy_entry_to_entry(new_entry, old_entry,
                                        compare_to_existing=False)
            catalog.entries[name] = old_entry
        else:
            catalog.entries[name] = new_entry

        if old_name != name:
            catalog.journal_entries()
        old_name = name
    for fname in efiles:
        os.remove(os.path.join(fdir, fname))

    return
