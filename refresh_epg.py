#!/usr/bin/env python3
"""Generate 21-day XMLTV with one full-day programme per Sky Store channel."""
from datetime import datetime, timedelta, time
from pathlib import Path
from zoneinfo import ZoneInfo
import json
import xml.etree.ElementTree as ET

BASE = Path(__file__).resolve().parent
EPG = BASE / "sky_store-epg_xml.xml"
CFG = BASE / "movie_schedule.json"
TZ = ZoneInfo("Europe/Warsaw")
DAYS = 21

def stamp(dt):
    return dt.strftime("%Y%m%d%H%M%S %z")

def main():
    cfg = json.loads(CFG.read_text(encoding="utf-8"))["channels"]
    tree = ET.parse(EPG)
    root = tree.getroot()
    channel_ids = {ch.get("id") for ch in root.findall("channel")}
    if len(channel_ids) != 30 or len(cfg) != 30:
        raise RuntimeError("Expected 30 Sky Store channels.")
    for item in root.findall("programme"):
        root.remove(item)
    first = datetime.combine(datetime.now(TZ).date(), time.min, tzinfo=TZ)
    for n in range(1, 31):
        channel = f"skystorepremiere{n}.custom"
        if channel not in channel_ids:
            raise RuntimeError(f"Missing channel {channel}")
        movie = cfg[str(n)]["movie"]
        desc = movie["description"]
        if movie.get("director"):
            desc += "\n\nDirector: " + movie["director"]
        if movie.get("cast"):
            desc += "\nCast: " + movie["cast"]
        for d in range(DAYS):
            day = first.date() + timedelta(days=d)
            start = datetime.combine(day, time.min, tzinfo=TZ)
            stop = datetime.combine(day + timedelta(days=1), time.min, tzinfo=TZ)
            p = ET.SubElement(root, "programme", {
                "start": stamp(start), "stop": stamp(stop), "channel": channel
            })
            ET.SubElement(p, "title", {"lang": "en"}).text = movie["title"] + " (" + str(movie["year"]) + ")"
            ET.SubElement(p, "desc", {"lang": "en"}).text = desc
    ET.indent(tree, space="  ")
    tree.write(EPG, encoding="utf-8", xml_declaration=True)
    print(f"Generated {DAYS} days of all-day programmes for 30 channels.")

if __name__ == "__main__":
    main()
