#!/usr/bin/env python3
"""Analyze HTML tags used in post content."""
import re, os
from collections import Counter

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
XML = os.path.join(BASE, "serenity.WordPress.2026-08-22.xml")
data = open(XML, encoding="utf-8").read()

items = re.split(r"<item>", data)[1:]
for it in items:
    if "<wp:post_type><![CDATA[post]]></wp:post_type>" not in it:
        continue
    m = re.search(r"<content:encoded><!\[CDATA\[(.*?)\]\]></content:encoded>", it, re.S)
    if not m:
        continue
    content = m.group(1)
    tags = re.findall(r"</([a-zA-Z0-9]+)>", content)
    print("---", len(content), "chars, closing tags:", dict(Counter(tags)))
