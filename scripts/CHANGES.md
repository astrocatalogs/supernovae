# Change Log #

## To-Do ##
-   `importer/tasks/vizier.py:do_vizier`
    -   Break down into separate functions, or classes.  Can use significant templating to cleanup.
-   `importer/tasks/donations.py:do_donations`
    -   Break down into separate " " " ".
-   `main.py`
    -   Look at '--archived' vs. '--refresh[list]' and '--full-refresh'... what exactly is desired?
-   `name_clean`
    -   FIX: IMPROVE THIS!
-   `EVENTS.add_quantity`
    -   FIX: IMPROVE THIS!
-   Create methods for parsing/cleaning RA & DEC  (e.g. to go into `add_quantity`)
-   `scripts/constants.py`
    -   Combine `OSC_` values into a class
-   Work on fuzzy finding for events, e.g. for 'ASASSN-13ax' perhaps include alias '13ax'?
-   `write_all_events`: save `non_sne_types` data somewhere instead of reloading each time
    -   Move all of the stuff inside the names loop into the EVENT class.
-   Change 'writevents' from a task to an argument parameter?  (e.g. for `journal_events`)
-   Combine `EVENT.check` with `Events.clean_event`
-   `load_cached_url` add warnings for failures
-   Have the different `add_` methods accept lists and add each
-   `NON_SNE_TYPES` needs to be added to some sort of global namespace
-   Consider parallelizing/multithreading --- especially for html queries, throw em in the
    background.
-   Why are there so many calls to `add_event` for the same events??  e.g. 'SN2001kd' in Vizier task
-   In `set_preferred_names`, when checking that the `newname` doesn't already exist: if it does,
    then they should be merged (or something?).


## Questions ##
-   Maybe unify things in 'csv' format, e.g. `do_snls` which seem to start the same way?
-   `tasks.general_data.do_snls` see note:
    -   "NOTE: Datafiles avail for download suggest diff zeropoints than 30, need to inquire."
-   What is `copy_to_event` doing with all the `null_field`s?  Why not just change the name...??
-   [JFG] I've currently split the "Event" and "Entry" classes into separate
    files, and also renamed the "Event" class "Supernova," as it is specific to
    the Supernova catalog. For the keys though I'm not sure how to split; there
    are ENTRY that should be defined only for Supernova but there are definitely
    many keys that will be shared (names, aliases, etc.). The keys should
    likely be defined in a JSON file for each catalog, in addition to a base
    list of keys provided by the parent Catalog class.

## Current ##

-   Drastic restructuring of code, primarily the main `import.py` script into modular, functional, and object oriented code.
