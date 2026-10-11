#!/usr/bin/env python3
"""Regenerate 21-day XMLTV with independently repeating screenings on all 30 channels."""
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo
import json
import xml.etree.ElementTree as ET

BASE = Path(__file__).resolve().parent
EPG = BASE / 'sky_store-epg_xml.xml'
CONFIG = BASE / 'movie_schedule.json'
TZ = ZoneInfo('Europe/Warsaw')
DAYS = 21
GAP = timedelta(seconds=10)

def xmltv_time(dt):
    return dt.astimezone(TZ).strftime('%Y%m%d%H%M%S %z')

def main():
    cfg = json.loads(CONFIG.read_text(encoding='utf-8'))['channels']
    tree = ET.parse(EPG)
    root = tree.getroot()
    originals = root.findall('programme')
    templates = {}
    for item in originals:
        templates.setdefault(item.get('channel'), deepcopy(item))
    channel_ids = [x.get('id') for x in root.findall('channel')]
    if len(channel_ids) != 30 or len(cfg) != 30 or any(ch not in templates for ch in channel_ids):
        raise RuntimeError('Missing channel or template; refusing to overwrite.')
    for item in originals:
        root.remove(item)
    start_local = datetime.combine(datetime.now(TZ).date(), datetime.min.time(), TZ)
    end_local = datetime.combine(start_local.date() + timedelta(days=DAYS), datetime.min.time(), TZ)
    window_start = start_local.astimezone(timezone.utc)
    window_end = end_local.astimezone(timezone.utc)
    total = 0
    for n in range(1, 31):
        channel = f'skystorepremiere{n}.custom'
        entry = cfg[str(n)]
        runtime = timedelta(seconds=int(entry['runtime_seconds']))
        if runtime.total_seconds() < 1200:
            raise RuntimeError(f'Invalid runtime on channel {n}')
        period = runtime + GAP
        anchor = datetime.fromisoformat(entry['anchor']).astimezone(timezone.utc)
        steps = (window_start - anchor) // period
        cursor = anchor + steps * period
        while cursor + runtime <= window_start:
            cursor += period
        while cursor < window_end:
            program = deepcopy(templates[channel])
            program.set('start', xmltv_time(cursor))
            program.set('stop', xmltv_time(cursor + runtime))
            root.append(program)
            cursor += period
            total += 1
    ET.indent(tree, space='  ')
    tree.write(EPG, encoding='utf-8', xml_declaration=True)
    print(f'Generated {total} screenings for 30 channels over {DAYS} days.')

if __name__ == '__main__':
    main()
