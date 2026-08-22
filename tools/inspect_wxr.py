#!/usr/bin/env python3
"""Inspect the WordPress WXR export to understand post structure."""
import re
import os

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
XML = os.path.join(BASE, "serenity.WordPress.2026-08-22.xml")

data = open(XML, encoding="utf-8").read()

# Split into items. The actual separator used in this file inside <channel>:
items = re.split(r"<item>", data)
items = items[1:]  # drop the channel header part before first <item>

for it in items:
    title = re.search(r"<title><!\[CDATA\[([^]]*)\]\]></title>", it)
    ptype = re.search(r"<wp:post_type><!\[CDATA\[([^]]*)\]\]></wp:post_type>", it)
    link = re.search(r"<link>([^<]*)</link>", it)
    status = re.search(r"<wp:status><!\[CDATA\[([^]]*)\]\]></wp:status>", it)
    date = re.search(r"<wp:post_date><!\[CDATA\[([^]]*)\]\]></wp:post_date>", it)
    name = re.search(r"<wp:post_name><!\[CDATA\[([^]]*)\]\]></wp:post_name>", it)
    t = title.group(1) if title else "?"
    pt = ptype.group(1) if ptype else "?"
    st = status.group(1) if status else "?"
    dt = date.group(1) if date else "?"
    lk = link.group(1) if link else "?"
    nm = name.group(1) if name else "?" if False else (name.group(1) if name else "?")
    print(f"[{pt:18}] {st:8} {dt} | {t!r}")
    print(f"    link={lk}")
    print(f"    name={nm!r}")
