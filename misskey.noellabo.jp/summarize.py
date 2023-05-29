#! /usr/bin/env python3
import re, configparser
from datetime import datetime

# Load config
config = configparser.ConfigParser()
config.read('server.cfg')
config_d = config["DEFAULT"]
server_name = config_d["ServerName"]
batch_interval = int(config_d["BatchInterval"])
note_interval = int(config_d["NoteInterval"])
batch_size = int(config_d["BatchSize"])
baseurl = f"https://{server_name}/emoji/"

# Prepare patterns
pattern = r':(.*)@'
p2 = r'@(.*):'

# Open data
with open(f"{server_name}.csv", "r") as f:
    lines = f.read().splitlines()
emojis = [line.split(",") for line in lines]

# Read start time
with open("start_time", "r") as f:
    lines = f.read().splitlines()
ts_start = int(int(lines[0]) / 1000)
dt_start = datetime.fromtimestamp(ts_start)
dt_start_str = dt_start.strftime("%Y/%m/%d %H:%M:%S")

# Read end time
with open("current_time", "r") as f:
    lines = f.read().splitlines()
ts_end = int(int(lines[0]) / 1000)
dt_end = datetime.fromtimestamp(ts_end)
dt_end_str = dt_end.strftime("%Y/%m/%d %H:%M:%S")

# Read md template
with open("../template/README.md", "r") as f:
    table_str = f.read()

# Replace words
table_str = table_str.replace(r"{{SERVER_NAME}}", server_name)
table_str = table_str.replace(r"{{START_TIME}}", dt_start_str)
table_str = table_str.replace(r"{{END_TIME}}", dt_end_str)
table_str = table_str.replace(r"{{BATCH_SIZE}}", str(batch_size))
table_str = table_str.replace(r"{{NOTE_REQ_INTERVAL}}", str(note_interval))
table_str = table_str.replace(
    r"{{TL_REQ_INTERVAL}}",
    str(batch_interval + note_interval * batch_size)
)

# Create the table headers
table_str += "|rank|image|signifier|type|frequency score|\n"
table_str += "|----|----|----|----|----|\n"

# Create the ranking table
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
        raw_str = f'|{rank}|<img height="24" src="{url_str}">|{signifier}|{emoji_type}|{point}|\n'
    else:
        emoji_type = "unicode"
        raw_str = f'|{rank}|{signifier}|{signifier}|{emoji_type}|{point}|\n'
    table_str += raw_str

with open("README.md", "w") as f:
    f.write(table_str)
