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
# Pilot: Fall 2 on Sky Store 3, observed 75 minutes into playback at 13:11 Warsaw time on 11 Oct 2026.
PILOT_CHANNEL = 'skystorepremiere3.custom'
PILOT_ANCHOR = datetime(2026, 10, 11, 11, 56, tzinfo=TZ)
PILOT_PERIOD = timedelta(minutes=98, seconds=10)
PILOT_RUNTIME = timedelta(minutes=98)
IDIOTS_CHANNEL = 'skystorepremiere7.custom'
IDIOTS_ANCHOR = datetime(2026, 10, 11, 12, 36, 30, tzinfo=TZ)
IDIOTS_PERIOD = timedelta(minutes=98, seconds=10)
IDIOTS_RUNTIME = timedelta(minutes=98)


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
    # Generate uninterrupted, individually timed screenings for the pilot channel.
    window_start = datetime.combine(today, datetime.min.time(), TZ)
    window_end = datetime.combine(today + timedelta(days=DAYS), datetime.min.time(), TZ)
    pilot = deepcopy(by_channel[PILOT_CHANNEL])
    cursor = PILOT_ANCHOR
    while cursor > window_start:
        cursor -= PILOT_PERIOD
    while cursor + PILOT_RUNTIME <= window_start:
        cursor += PILOT_PERIOD
    pilot_count = 0
    while cursor < window_end:
        program = deepcopy(pilot)
        program.set('start', xmltv_time(cursor))
        program.set('stop', xmltv_time(cursor + PILOT_RUNTIME))
        root.append(program)
        cursor += PILOT_PERIOD
        pilot_count += 1
    idiots = deepcopy(by_channel[IDIOTS_CHANNEL])
    cursor = IDIOTS_ANCHOR
    while cursor > window_start:
        cursor -= IDIOTS_PERIOD
    while cursor + IDIOTS_RUNTIME <= window_start:
        cursor += IDIOTS_PERIOD
    idiots_count = 0
    while cursor < window_end:
        program = deepcopy(idiots)
        program.set('start', xmltv_time(cursor))
        program.set('stop', xmltv_time(cursor + IDIOTS_RUNTIME))
        root.append(program)
        cursor += IDIOTS_PERIOD
        idiots_count += 1
    for day in range(DAYS):
        start = datetime.combine(today + timedelta(days=day), datetime.min.time(), TZ)
        stop = datetime.combine(today + timedelta(days=day + 1), datetime.min.time(), TZ)
        for channel in channels:
            if channel in (PILOT_CHANNEL, IDIOTS_CHANNEL):
                continue
            program = deepcopy(by_channel[channel])
            program.set('start', xmltv_time(start))
            program.set('stop', xmltv_time(stop))
            root.append(program)
    ET.indent(tree, space='  ')
    tree.write(EPG, encoding='utf-8', xml_declaration=True)
    print(f'Updated {len(channels)} channels for {DAYS} days starting {today}; {pilot_count} Fall 2 screenings, {idiots_count} Idiots screenings.')


if __name__ == '__main__':
    main()
