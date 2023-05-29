#! /usr/bin/env python3
import re
from os import path
from datetime import datetime

# URLs to be reffered not from the target server
ext_urls = {}

# basic
script_path = path.abspath(__file__)
server_name = path.basename(path.dirname(script_path))
pattern = r':(.*)@'
p2 = r'@(.*):'
baseurl = f"https://{server_name}/emoji/"

# open file
with open(f"{server_name}.csv", "r") as f:
    lines = f.read().splitlines()
emojis = [line.split(",") for line in lines]

with open(f"start_time", "r") as f:
    lines = f.read().splitlines()
ts_start = int(int(lines[0]) / 1000)
dt_start = datetime.fromtimestamp(ts_start)
dt_start_str = dt_start.strftime("%m/%d/%Y %H:%M:%S")

with open(f"current_time", "r") as f:
    lines = f.read().splitlines()
ts_end = int(int(lines[0]) / 1000)
dt_end = datetime.fromtimestamp(ts_end)
dt_end_str = dt_end.strftime("%m/%d/%Y %H:%M:%S")

# md str
with open("../template/README.md", "r") as f:
    text = f.read()

table_str = text

table_str = table_str.replace("misskey.io", server_name)
table_str = table_str.replace("2023/02/23 -", f"{dt_start_str} - {dt_end_str}")
table_str = table_str.replace("600 sec", "100 sec")
table_str += "|rank|image|signifier|type|frequency score|\n"
table_str += "|----|----|----|----|----|\n"

rank_no = min(len(emojis), 100)
for i in range(rank_no):
    emoji = emojis[i]
    signifier = emoji[0]
    point = emoji[1]
    rank = str(i + 1)
    if ":" in signifier:
        emoji_type = "custom"
        emoji_name = re.findall(pattern, signifier)[0]
        domain = re.findall(p2, signifier)[0]
        if domain == ".":
            signifier = signifier.replace(domain, "")
            signifier = signifier.replace("@", "")
        url_str = f"{baseurl}{emoji_name}.webp"
        if signifier in ext_urls:
            url_str = ext_urls[signifier]
        raw_str = f'|{rank}|<img height="24" src="{url_str}">|{signifier}|{emoji_type}|{point}|\n'
    else:
        emoji_type = "unicode"
        raw_str = f'|{rank}|{signifier}|{signifier}|{emoji_type}|{point}|\n'
    table_str += raw_str

with open("README.md", "w") as f:
    f.write(table_str)
