'''Clean various supernova-specific values.
'''
from math import floor

from astrocats.catalog.utils import (get_sig_digits, is_integer, is_number,
                                     pretty_num, zpad)

from decimal import Decimal

__all__ = ['name_clean', 'host_clean', 'radec_clean', 'clean_snname']


def name_clean(name):
    newname = name.strip(' ;,*.')
    if newname.startswith('NAME '):
        newname = newname.replace('NAME ', '', 1)
    if newname.endswith(' SN'):
        newname = newname.replace(' SN', '')
    if newname.endswith(':SN'):
        newname = newname.replace(':SN', '')
    if newname.startswith('MASJ'):
        newname = newname.replace('MASJ', 'MASTER OT J', 1)
    if (newname.startswith('MASTER') and len(newname) > 7 and
            is_number(newname[7])):
        newname = newname.replace('MASTER', 'MASTER OT J', 1)
    if (newname.startswith('MASTER OT') and len(newname) > 10 and
            is_number(newname[10])):
        newname = newname.replace('MASTER OT', 'MASTER OT J', 1)
    if newname.startswith('MASTER OT J '):
        newname = newname.replace('MASTER OT J ', 'MASTER OT J', 1)
    if newname.startswith('OGLE '):
        newname = newname.replace('OGLE ', 'OGLE-', 1)
    if newname.startswith('OGLE-') and len(newname) != 16:
        namesp = newname.split('-')
        if (len(namesp) == 4 and len(namesp[1]) == 4 and
                is_number(namesp[1]) and is_number(namesp[3])):
            newname = 'OGLE-' + namesp[1] + '-SN-' + namesp[3].zfill(3)
        elif (len(namesp) == 2 and is_number(namesp[1][:2]) and
              not is_number(namesp[1][2:])):
            newname = 'OGLE' + namesp[1]
    if newname.startswith('SN SDSS'):
        newname = newname.replace('SN SDSS ', 'SDSS', 1)
    if newname.startswith('SDSS '):
        newname = newname.replace('SDSS ', 'SDSS', 1)
    if newname.startswith('SDSS'):
        namesp = newname.split('-')
        if (len(namesp) == 3 and is_number(namesp[0][4:]) and
                is_number(namesp[1]) and is_number(namesp[2])):
            newname = namesp[0] + '-' + namesp[1] + '-' + namesp[2].zfill(3)
    if newname.startswith('SDSS-II SN'):
        namesp = newname.split()
        if len(namesp) == 3 and is_number(namesp[2]):
            newname = 'SDSS-II SN ' + namesp[2].lstrip('0')
    if newname.startswith('SN CL'):
        newname = newname.replace('SN CL', 'CL', 1)
    if newname.startswith('SN HiTS'):
        newname = newname.replace('SN HiTS', 'SNHiTS', 1)
    if newname.startswith('SNHiTS '):
        newname = newname.replace('SNHiTS ', 'SNHiTS', 1)
    if newname.startswith('GAIA'):
        newname = newname.replace('GAIA', 'Gaia', 1)
    if newname.startswith('KSN-'):
        newname = newname.replace('KSN-', 'KSN', 1)
    if newname.startswith('KSN'):
        newname = 'KSN' + newname[3:].lower()
    if newname.startswith('Gaia '):
        newname = newname.replace('Gaia ', 'Gaia', 1)
    if newname.startswith('Gaia'):
        newname = 'Gaia' + newname[4:].lower()
    if newname.startswith('GRB'):
        newname = newname.replace('GRB', 'GRB ', 1)
    if newname.startswith('GRB ') and is_number(newname[4:].strip()):
        newname = 'GRB ' + newname[4:].strip() + 'A'
    if newname.startswith('ESSENCE '):
        newname = newname.replace('ESSENCE ', 'ESSENCE', 1)
    if newname.startswith('LSQ '):
        newname = newname.replace('LSQ ', 'LSQ', 1)
    if newname.startswith('LSQ') and is_number(newname[3]):
        newname = newname[:3] + newname[3:].lower()
    if newname.startswith('DES') and is_number(newname[3]):
        newname = newname[:7] + newname[7:].lower()
    if newname.startswith('SNSDF '):
        newname = newname.replace(' ', '')
    if newname.startswith('SNSDF'):
        namesp = newname.split('.')
        if len(namesp[0]) == 9:
            newname = namesp[0] + '-' + namesp[1].zfill(2)
    if newname.startswith('HFF '):
        newname = newname.replace(' ', '')
    if newname.startswith('SN HST'):
        newname = newname.replace('SN HST', 'HST', 1)
    if newname.startswith('HST ') and newname[4] != 'J':
        newname = newname.replace('HST ', 'HST J', 1)
    if newname.startswith('SNLS') and newname[4] != '-':
        newname = newname.replace('SNLS', 'SNLS-', 1)
    if newname.startswith('SNLS- '):
        newname = newname.replace('SNLS- ', 'SNLS-', 1)
    if newname.startswith('CRTS CSS'):
        newname = newname.replace('CRTS CSS', 'CSS', 1)
    if newname.startswith('CRTS MLS'):
        newname = newname.replace('CRTS MLS', 'MLS', 1)
    if newname.startswith('CRTS SSS'):
        newname = newname.replace('CRTS SSS', 'SSS', 1)
    if newname.startswith(('CSS', 'MLS', 'SSS')):
        newname = newname.replace(' ', ':').replace('J', '')
    if newname.startswith('SN HFF'):
        newname = newname.replace('SN HFF', 'HFF', 1)
    if newname.startswith('SN GND'):
        newname = newname.replace('SN GND', 'GND', 1)
    if newname.startswith('SN SCP'):
        newname = newname.replace('SN SCP', 'SCP', 1)
    if newname.startswith('SN UDS'):
        newname = newname.replace('SN UDS', 'UDS', 1)
    if newname.startswith('SCP') and newname[3] != '-':
        newname = newname.replace('SCP', 'SCP-', 1)
    if newname.startswith('SCP- '):
        newname = newname.replace('SCP- ', 'SCP-', 1)
    if newname.startswith('SCP-') and is_integer(newname[7:]):
        newname = 'SCP-' + newname[4:7] + str(int(newname[7:]))
    if newname.startswith('PS 1'):
        newname = newname.replace('PS 1', 'PS1', 1)
    if newname.startswith('PS1 SN PS'):
        newname = newname.replace('PS1 SN PS', 'PS', 1)
    if newname.startswith('PS1 SN'):
        newname = newname.replace('PS1 SN', 'PS1', 1)
    if newname.startswith('PS1') and is_number(newname[3]):
        newname = newname[:3] + newname[3:].lower()
    elif newname.startswith('PS1-') and is_number(newname[4]):
        newname = newname[:4] + newname[4:].lower()
    if newname.startswith('PSN K'):
        newname = newname.replace('PSN K', 'K', 1)
    if newname.startswith('K') and is_number(newname[1:5]):
        namesp = newname.split('-')
        if len(namesp[0]) == 5:
            newname = namesp[0] + '-' + namesp[1].zfill(3)
    if newname.startswith('Psn'):
        newname = newname.replace('Psn', 'PSN', 1)
    if newname.startswith('PSNJ'):
        newname = newname.replace('PSNJ', 'PSN J', 1)
    if newname.startswith('TCPJ'):
        newname = newname.replace('TCPJ', 'TCP J', 1)
    if newname.startswith('SMTJ'):
        newname = newname.replace('SMTJ', 'SMT J', 1)
    if newname.startswith('PSN20J'):
        newname = newname.replace('PSN20J', 'PSN J', 1)
    if newname.startswith('SN ASASSN'):
        newname = newname.replace('SN ASASSN', 'ASASSN', 1)
    if newname.startswith('ASASSN-20') and is_number(newname[9]):
        newname = newname.replace('ASASSN-20', 'ASASSN-', 1)
    if newname.startswith('ASASSN '):
        newname = newname.replace('ASASSN ', 'ASASSN-', 1).replace('--', '-')
    if newname.startswith('ASASSN') and newname[6] != '-':
        newname = newname.replace('ASASSN', 'ASASSN-', 1)
    if newname.startswith('ASASSN-') and is_number(newname[7]):
        newname = newname[:7] + newname[7:].lower()
    if newname.startswith('ROTSE3J'):
        newname = newname.replace('ROTSE3J', 'ROTSE3 J', 1)
    if newname.startswith('MACSJ'):
        newname = newname.replace('MACSJ', 'MACS J', 1)
    if newname.startswith('MWSNR'):
        newname = newname.replace('MWSNR', 'MWSNR ', 1)
    if newname.startswith('SN HUNT'):
        newname = newname.replace('SN HUNT', 'SNhunt', 1)
    if newname.startswith('SN Hunt'):
        newname = newname.replace(' ', '')
    if newname.startswith('SNHunt'):
        newname = newname.replace('SNHunt', 'SNhunt', 1)
    if newname.startswith('SNhunt '):
        newname = newname.replace('SNhunt ', 'SNhunt', 1)
    if newname.startswith('ptf'):
        newname = newname.replace('ptf', 'PTF', 1)
    if newname.startswith('SN PTF'):
        newname = newname.replace('SN PTF', 'PTF', 1)
    if newname.startswith('PTF '):
        newname = newname.replace('PTF ', 'PTF', 1)
    if newname.startswith('PTF') and is_number(newname[3]):
        newname = newname[:3] + newname[3:].lower()
    if newname.startswith('IPTF'):
        newname = newname.replace('IPTF', 'iPTF', 1)
    if newname.startswith('iPTF '):
        newname = newname.replace('iPTF ', 'iPTF', 1)
    if newname.startswith('iPTF') and is_number(newname[4]):
        newname = newname[:4] + newname[4:].lower()
    if newname.startswith('PESSTOESO'):
        newname = newname.replace('PESSTOESO', 'PESSTO ESO ', 1)
    if newname.startswith('snf'):
        newname = newname.replace('snf', 'SNF', 1)
    if newname.startswith('SNF '):
        newname = newname.replace('SNF ', 'SNF', 1)
    if (newname.startswith('SNF') and is_number(newname[3:]) and
            len(newname) >= 12):
        newname = 'SNF' + newname[3:11] + '-' + newname[11:]
    if newname.startswith(('MASTER OT J', 'ROTSE3 J')):
        prefix = newname.split('J')[0]
        coords = newname.split('J')[-1].strip()
        decsign = '+' if '+' in coords else '-'
        coordsplit = coords.replace('+', '-').split('-')
        if ('.' not in coordsplit[0] and len(coordsplit[0]) > 6 and
                '.' not in coordsplit[1] and len(coordsplit[1]) > 6):
            newname = (
                prefix + 'J' + coordsplit[0][:6] + '.' + coordsplit[0][6:] +
                decsign + coordsplit[1][:6] + '.' + coordsplit[1][6:])
    if (newname.startswith('Gaia ') and is_number(newname[3:4]) and
            len(newname) > 5):
        newname = newname.replace('Gaia ', 'Gaia', 1)
    if (newname.startswith('AT ') and is_number(newname[3:7]) and
            len(newname) > 7):
        newname = newname.replace('AT ', 'AT', 1)
    if len(newname) <= 4 and is_number(newname):
        newname = 'SN' + newname + 'A'
    if (len(newname) > 4 and is_number(newname[:4]) and
            not is_number(newname[4:])):
        newname = 'SN' + newname
    if (newname.startswith('Sn ') and is_number(newname[3:7]) and
            len(newname) > 7):
        newname = newname.replace('Sn ', 'SN', 1)
    if (newname.startswith('sn') and is_number(newname[2:6]) and
            len(newname) > 6):
        newname = newname.replace('sn', 'SN', 1)
    if (newname.startswith('SN ') and is_number(newname[3:7]) and
            len(newname) > 7):
        newname = newname.replace('SN ', 'SN', 1)
    if (newname.startswith('SN') and is_number(newname[2:6]) and
            len(newname) == 7 and newname[6].islower()):
        newname = 'SN' + newname[2:6] + newname[6].upper()
    elif (newname.startswith('SN') and is_number(newname[2:6]) and
          (len(newname) == 8 or len(newname) == 9) and newname[6:].isupper()):
        newname = 'SN' + newname[2:6] + newname[6:].lower()
    if (newname.startswith('AT') and is_number(newname[2:6]) and
            len(newname) == 7 and newname[6].islower()):
        newname = 'AT' + newname[2:6] + newname[6].upper()
    elif (newname.startswith('AT') and is_number(newname[2:6]) and
          (len(newname) == 8 or len(newname) == 9) and newname[6:].isupper()):
        newname = 'AT' + newname[2:6] + newname[6:].lower()

    newname = (' '.join(newname.split())).strip()
    return newname


def radec_clean(svalue, quantity, unit=''):
    svalue = svalue.strip()
    if unit == 'floatdegrees':
        if not is_number(svalue):
            return (svalue, unit)
        deg = float('%g' % Decimal(svalue))
        sig = get_sig_digits(svalue)
        if 'ra' in quantity:
            flhours = deg / 360.0 * 24.0
            hours = floor(flhours)
            minutes = floor((flhours - hours) * 60.0)
            seconds = (flhours * 60.0 - (hours * 60.0 + minutes)) * 60.0
            hours = 0 if hours < 1.e-6 else hours
            minutes = 0 if minutes < 1.e-6 else minutes
            seconds = 0.0 if seconds < 1.e-6 else seconds
            if seconds > 60.0:
                raise (ValueError('Invalid seconds value for ' + quantity))
            svalue = str(hours).zfill(2) + ':' + str(minutes).zfill(2) + \
                ':' + zpad(pretty_num(seconds, sig=sig - 1))
        elif 'dec' in quantity:
            fldeg = abs(deg)
            degree = floor(fldeg)
            minutes = floor((fldeg - degree) * 60.0)
            seconds = (fldeg * 60.0 - (degree * 60.0 + minutes)) * 60.0
            minutes = 0 if minutes < 1.e-6 else minutes
            seconds = 0.0 if seconds < 1.e-6 else seconds
            if seconds > 60.0:
                raise (ValueError('Invalid seconds value for ' + quantity))
            svalue = (
                ('+' if deg >= 0.0 else '-') + str(degree).strip('+-').zfill(2)
                + ':' + str(minutes).zfill(2) + ':' +
                zpad(pretty_num(
                    seconds, sig=sig - 1)))
    elif unit == 'nospace' and 'ra' in quantity:
        svalue = svalue[:2] + ':' + svalue[2:4] + \
            ((':' + zpad(svalue[4:])) if len(svalue) > 4 else '')
    elif unit == 'nospace' and 'dec' in quantity:
        if svalue.startswith(('+', '-')):
            svalue = svalue[:3] + ':' + svalue[3:5] + \
                ((':' + zpad(svalue[5:])) if len(svalue) > 5 else '')
        else:
            svalue = '+' + svalue[:2] + ':' + svalue[2:4] + \
                ((':' + zpad(svalue[4:])) if len(svalue) > 4 else '')
    else:
        svalue = svalue.replace(' ', ':')
        if 'dec' in quantity:
            valuesplit = svalue.split(':')
            svalue = (('-' if valuesplit[0].startswith('-') else '+'
                       ) + valuesplit[0].strip('+-').zfill(2) +
                      (':' + valuesplit[1].zfill(2)
                       if len(valuesplit) > 1 else '') +
                      (':' + zpad(valuesplit[2])
                       if len(valuesplit) > 2 else ''))

    if 'ra' in quantity:
        sunit = 'hours'
    elif 'dec' in quantity:
        sunit = 'degrees'

    # Correct case of arcseconds = 60.0.
    valuesplit = svalue.split(':')
    if len(valuesplit) == 3 and valuesplit[-1] in ["60.0", "60.", "60"]:
        svalue = valuesplit[0] + ':' + str(
            Decimal(valuesplit[1]) + Decimal(1.0)) + ':' + "00.0"

    # Strip trailing dots.
    svalue = svalue.rstrip('.')

    return (svalue, sunit)


def host_clean(name):
    newname = name.strip(' ;,*')

    # Handle some special cases
    hostcases = {'M051a': 'M51A', 'M051b': 'M51B'}
    for k in hostcases:
        if newname == k:
            newname = hostcases[k]

    # Some general cases
    newname = newname.strip("()").replace('  ', ' ', 1)
    newname = newname.replace("ABELL", "Abell", 1)
    newname = newname.replace("Abell", "Abell ", 1)
    newname = newname.replace("APMUKS(BJ)", "APMUKS(BJ) ", 1)
    newname = newname.replace("ARP", "ARP ", 1)
    newname = newname.replace("CGCG", "CGCG ", 1)
    newname = newname.replace("HOLM", "HOLM ", 1)
    newname = newname.replace("ESO", "ESO ", 1)
    newname = newname.replace("IC", "IC ", 1)
    newname = newname.replace("Intergal.", "Intergalactic", 1)
    newname = newname.replace("MCG+", "MCG +", 1)
    newname = newname.replace("MCG-", "MCG -", 1)
    newname = newname.replace("M+", "MCG +", 1)
    newname = newname.replace("M-", "MCG -", 1)
    newname = newname.replace("MGC ", "MCG ", 1)
    newname = newname.replace("Mrk", "MRK", 1)
    newname = newname.replace("MRK", "MRK ", 1)
    newname = newname.replace("NGC", "NGC ", 1)
    newname = newname.replace("PGC", "PGC ", 1)
    newname = newname.replace("SDSS", "SDSS ", 1)
    newname = newname.replace("UGC", "UGC ", 1)
    if newname.startswith('MESSIER '):
        newname = newname.replace('MESSIER ', 'M', 1)
    if newname.startswith('M ') and is_number(newname[2:]):
        newname = newname.replace('M ', 'M', 1)
    if newname.startswith('M') and is_number(newname[1:]):
        newname = 'M' + newname[1:].lstrip(" 0")
    if len(newname) > 4 and newname.startswith("PGC "):
        newname = newname[:4] + newname[4:].lstrip(" 0")
    if len(newname) > 4 and newname.startswith("UGC "):
        newname = newname[:4] + newname[4:].lstrip(" 0")
    if len(newname) > 5 and newname.startswith(("MCG +", "MCG -")):
        newname = newname[:5] + '-'.join(
            [x.zfill(2) for x in newname[5:].strip().split("-")])
    if len(newname) > 5 and newname.startswith("CGCG "):
        newname = newname[:5] + '-'.join(
            [x.zfill(3) for x in newname[5:].strip().split("-")])
    if ((len(newname) > 1 and newname.startswith("E")) or
        (len(newname) > 3 and newname.startswith('ESO'))):
        if newname[0] == "E":
            esplit = newname[1:].split("-")
        else:
            esplit = newname[3:].split("-")
        if len(esplit) == 2 and is_number(esplit[0].strip()):
            if esplit[1].strip()[0] == 'G':
                parttwo = esplit[1][1:].strip()
            else:
                parttwo = esplit[1].strip()
            if is_number(parttwo.strip()):
                newname = 'ESO ' + \
                    esplit[0].lstrip('0') + '-G' + parttwo.lstrip('0')
    newname = ' '.join(newname.split())
    return newname


def clean_snname(string):
    newstring = string.replace(' ', '').upper()
    if (newstring[:2] == "SN"):
        head = newstring[:6]
        tail = newstring[6:]
        if len(tail) >= 2 and tail[1] != '?':
            tail = tail.lower()
        newstring = head + tail

    return newstring
