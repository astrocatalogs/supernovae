"""Import tasks related to the Hubble pointings page.
"""
import os
from glob import glob

import dropbox

from astrocats.catalog.utils import pbar
from astrocats.supernovae.supernova import Supernova


def do_mosfit(catalog):
    task_str = catalog.get_current_task_str()
    try:
        with open('mosfit.key', 'r') as f:
            mosfitkey = f.read().splitlines()[0]
    except:
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

        name = fname.split('_')[-3]

        new_entry = Supernova.init_from_file(
            catalog, path=fpath, compare_to_existing=False)

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
