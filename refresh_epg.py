#!/usr/bin/env python3
"""Renew a rolling 21-day XMLTV schedule without changing channel IDs or metadata."""
from copy import deepcopy
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo
import xml.etree.ElementTree as ET

EPG = Path(__file__).resolve().parent / 'sky_store-epg_xml.xml'
DAYS = 21
TZ = ZoneInfo('Europe/Warsaw')


def xmltv_time(dt):
    return dt.strftime('%Y%m%d%H%M%S %z')


def main():
    tree = ET.parse(EPG)
    root = tree.getroot()
    originals = root.findall('programme')
    if not originals:
        raise RuntimeError('No programmes found; refusing to overwrite the EPG.')
    by_channel = {}
    for program in originals:
        channel = program.get('channel')
        if channel and channel not in by_channel:
            by_channel[channel] = deepcopy(program)
    channels = [c.get('id') for c in root.findall('channel')]
    if not channels or any(ch not in by_channel for ch in channels):
        raise RuntimeError('Missing channel programme; refusing to overwrite the EPG.')
    for program in originals:
        root.remove(program)
    today = datetime.now(TZ).date()
    for day in range(DAYS):
        start = datetime.combine(today + timedelta(days=day), datetime.min.time(), TZ)
        stop = datetime.combine(today + timedelta(days=day + 1), datetime.min.time(), TZ)
        for channel in channels:
            program = deepcopy(by_channel[channel])
            program.set('start', xmltv_time(start))
            program.set('stop', xmltv_time(stop))
            root.append(program)
    ET.indent(tree, space='  ')
    tree.write(EPG, encoding='utf-8', xml_declaration=True)
    print(f'Updated {len(channels)} channels for {DAYS} days starting {today}.')


if __name__ == '__main__':
    main()
