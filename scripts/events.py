import gzip

def get_event_text(eventfile):
    if eventfile.split('.')[-1] == 'gz':
        with gzip.open(eventfile, 'rt') as f:
            filetext = f.read()
    else:
        with open(eventfile, 'r') as f:
            filetext = f.read()
    return filetext

def get_event_filename(name):
    return(name.replace('/', '_'))
