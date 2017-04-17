
import json
import os
from collections import OrderedDict
from random import randint

from astropy.time import Time as astrotime
from bokeh.embed import file_html
from bokeh.models import ColumnDataSource, HoverTool
from bokeh.plotting import Figure, reset_output
from bokeh.resources import CDN

from astrocats.catalog.utils import bandaliasf, bandcolorf, tprint, tq
from astrocats.supernovae.scripts.events import get_event_text
from astrocats.supernovae.scripts.repos import repo_file_list

tools = "pan,wheel_zoom,box_zoom,save,crosshair,reset,resize"

outdir = "astrocats/supernovae/output/html"

averagetypes = ['Ia', 'I P', 'Ia P', 'Ib P', 'Ic P', 'Ia/c', 'Ib/c', 'Ib/c P',
                'II P', 'II L', 'IIn', 'IIn P',
                'IIb P', 'Ia CSM', 'SLSN-Ic', 'SLSN-I', 'SLSN-II', 'Ia-91bg',
                'Ia-91T', 'Ia-02cx', 'Ib-Ca', 'II P-97D', 'Ic BL']

files = repo_file_list(bones=False)


def photo_cut(x):
    return ('magnitude' in x and 'time' in x and 'includeshost' not in x)

with open('astrocats/supernovae/output/catalog.min.json', 'r') as f:
    filetext = f.read()
    meta = json.loads(filetext, object_pairs_hook=OrderedDict)

metanames = [x['name'] for x in meta]

for averagetype in averagetypes:
    phototime = []
    phototimelowererrs = []
    phototimeuppererrs = []
    photoAB = []
    photoABerrs = []
    photoband = []
    photoinstru = []
    photoevent = []
    phototype = []

    for fcnt, eventfile in enumerate(
        tq(sorted(files, key=lambda s: s.lower()), 'Looping over ' +
           averagetype + ' SNe')):
        # if fcnt > 2000:
        #    break

        name = os.path.basename(os.path.splitext(eventfile)[0])
        if name in metanames:
            foundtype = False
            mi = metanames.index(name)
            if meta[mi]['claimedtype']:
                for ct in meta[mi]['claimedtype']:
                    if ct['value'] == averagetype:
                        foundtype = True
                        break
            if not foundtype:
                continue
        else:
            continue

        filetext = get_event_text(eventfile)

        thisevent = json.loads(filetext, object_pairs_hook=OrderedDict)
        thisevent = thisevent[list(thisevent.keys())[0]]

        if ('photometry' not in thisevent or 'maxdate' not in thisevent or 'maxabsmag' not in thisevent or
            'maxappmag' not in thisevent or 'claimedtype' not in thisevent or
                len(thisevent['maxdate'][0]['value'].split('/')) < 3 or 'discoverdate' not in thisevent):
            continue

        foundtype = False
        for ct in thisevent['claimedtype']:
            if ct['value'] == averagetype:
                foundtype = True
                break
        if not foundtype:
            continue

        maxdate = astrotime(thisevent['maxdate'][0][
                            'value'].replace('/', '-')).mjd
        discoverdate = astrotime(thisevent['discoverdate'][0][
                                 'value'].replace('/', '-')).mjd

        if maxdate == discoverdate:
            continue

        distmod = float(thisevent['maxappmag'][0]['value']) - \
            float(thisevent['maxabsmag'][0]['value'])

        tprint(thisevent['name'])

        prange = list(range(len([x for x in thisevent['photometry'] if photo_cut(
            x)]))) if 'photometry' in thisevent else []

        if len(prange) <= 3:
            continue

        phototime += [float(x['time'][:-1] + str(0 * randint(0, 9)) if x['time'][-1] != '.' else x['time'] + '.' + str(0 * randint(0, 9))) - maxdate
                      for x in thisevent['photometry'] if photo_cut(x)]
        phototimelowererrs += [float(x['e_lower_time']) if ('e_lower_time' in x and 'e_upper_time' in x)
                               else (float(x['e_time']) if 'e_time' in x else 0.) for x in thisevent['photometry'] if photo_cut(x)]
        phototimeuppererrs += [float(x['e_upper_time']) if ('e_lower_time' in x and 'e_upper_time' in x) in x
                               else (float(x['e_time']) if 'e_time' in x else 0.) for x in thisevent['photometry'] if photo_cut(x)]
        photoAB += [float(x['magnitude'] + str(0 * randint(0, 9)) if '.' in x['magnitude'] else x['magnitude'] + '.' +
                          str(0 * randint(0, 9))) - distmod for x in thisevent['photometry'] if photo_cut(x)]
        photoABerrs += [(float(x['e_magnitude']) if 'e_magnitude' in x else 0.)
                        for x in thisevent['photometry'] if photo_cut(x)]
        photoband += [(x['band'] if 'band' in x else '')
                      for x in thisevent['photometry'] if photo_cut(x)]
        photoinstru += [(x['instrument'] if 'instrument' in x else '')
                        for x in thisevent['photometry'] if photo_cut(x)]
        photoevent += [thisevent['name'] for x in prange]
        phototype += [(x['upperlimit'] if 'upperlimit' in x else False)
                      for x in thisevent['photometry'] if photo_cut(x)]

    if not len(phototime):
        continue

    bandset = set(photoband)
    bandset = [i for (j, i) in sorted(
        list(zip(list(map(bandaliasf, bandset)), bandset)))]

    x_buffer = 0.1 * (max(phototime) - min(phototime)
                      ) if len(phototime) > 1 else 1.0

    tt = [
        ("Event", "@src"),
        ("Epoch (MJD)", "@x{1.11}"),
        ("Absolute Magnitude", "@y{1.111}")
    ]
    if len(list(filter(None, photoABerrs))):
        tt += [("Error", "@err{1.111}")]
    if len(list(filter(None, photoband))):
        tt += [("Band", "@desc")]
    if len(list(filter(None, photoinstru))):
        tt += [("Instrument", "@instr")]
    hover = HoverTool(tooltips=tt)

    min_x_range = -x_buffer + \
        min([x - y for x, y in list(zip(phototime, phototimeuppererrs))])
    max_x_range = x_buffer + \
        max([x + y for x, y in list(zip(phototime, phototimelowererrs))])

    p1 = Figure(title='Average Photometry for Type ' + averagetype + ' SNe', x_axis_label='Time (MJD)',
                # responsive = True,
                y_axis_label='Absolute Magnitude', tools=tools, plot_width=1000, plot_height=1000,
                x_range=(min_x_range, max_x_range),
                y_range=(0.5 + max([x + y for x, y in list(zip(photoAB, photoABerrs))]),
                         -0.5 + min([x - y for x, y in list(zip(photoAB, photoABerrs))])),
                title_text_font_size='20pt', webgl=True)
    p1.xaxis.axis_label_text_font_size = '16pt'
    p1.yaxis.axis_label_text_font_size = '16pt'
    p1.xaxis.major_label_text_font_size = '12pt'
    p1.yaxis.major_label_text_font_size = '12pt'

    p1.add_tools(hover)

    xs = []
    ys = []
    err_xs = []
    err_ys = []

    for x, y, xlowerr, xupperr, yerr in list(zip(phototime, photoAB, phototimelowererrs, phototimeuppererrs, photoABerrs)):
        xs.append(x)
        ys.append(y)
        err_xs.append((x - xlowerr, x + xupperr))
        err_ys.append((y - yerr, y + yerr))

    for band in bandset:
        bandname = bandaliasf(band)
        indb = [i for i, j in enumerate(photoband) if j == band]
        indt = [i for i, j in enumerate(phototype) if not j]
        # Should always have upper error if have lower error.
        indnex = [i for i, j in enumerate(phototimelowererrs) if j == 0.]
        indyex = [i for i, j in enumerate(phototimelowererrs) if j > 0.]
        indney = [i for i, j in enumerate(photoABerrs) if j == 0.]
        indyey = [i for i, j in enumerate(photoABerrs) if j > 0.]
        indne = set(indb).intersection(indt).intersection(
            indney).intersection(indnex)
        indye = set(indb).intersection(
            indt).intersection(set(indyey).union(indyex))

        noerrorlegend = bandname if len(indne) == 0 else ''

        source = ColumnDataSource(
            data=dict(
                x=[phototime[i] for i in indne],
                y=[photoAB[i] for i in indne],
                err=[photoABerrs[i] for i in indne],
                desc=[photoband[i] for i in indne],
                instr=[photoinstru[i] for i in indne],
                src=[photoevent[i] for i in indne]
            )
        )
        p1.circle('x', 'y', source=source, color=bandcolorf(band),
                  legend='', size=2, line_alpha=0.75, fill_alpha=0.75)

        source = ColumnDataSource(
            data=dict(
                x=[phototime[i] for i in indye],
                y=[photoAB[i] for i in indye],
                err=[photoABerrs[i] for i in indye],
                desc=[photoband[i] for i in indye],
                instr=[photoinstru[i] for i in indye],
                src=[photoevent[i] for i in indye]
            )
        )
        p1.circle('x', 'y', source=source, color=bandcolorf(band),
                  legend=bandname, size=2, line_alpha=0.75, fill_alpha=0.75)

    p1.legend.label_text_font_size = '8pt'
    p1.legend.label_width = 20
    p1.legend.label_height = 14
    p1.legend.glyph_height = 14

    html = file_html(p1, CDN, 'Average ' + averagetype)

    with open(outdir + "LCs-" + averagetype.lower().replace(' ', '_').replace('/', '-') + ".html", "w") as f:
        f.write(html)

    # Necessary to clear Bokeh state
    reset_output()
