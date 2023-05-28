#! /usr/bin/env python3
import requests, time, configparser
from datetime import datetime

# Load config
CONFIG_FNAME = 'server.cfg'
config = configparser.ConfigParser()
config.read(CONFIG_FNAME)
config_d = config["DEFAULT"]
server_name = config_d["ServerName"]
userId = config_d["UserId"]
token = config_d["Token"]
batch_interval = int(config_d["BatchInterval"])
note_interval = int(config_d["NoteInterval"])
batch_size = int(config_d["BatchSize"])

# Define endpoints
base_url = f"https://{server_name}/api"
endpoint_local = f"{base_url}/notes/local-timeline"
endpoint_rxn = f"{base_url}/notes/reactions"

# Load saved reaction coounts
rxn_counts = {}
csvname = f"{server_name}.csv"
with open(csvname, "a+") as f:
    f.seek(0)
    lines = f.read().splitlines()
    for line in lines:
        rxn_type, count = line.split(",")
        rxn_counts[rxn_type] = int(count)

# Load initial measurement time
time_fname = "current_time"
with open(time_fname, "r") as f:
    epoch_sec = int(f.read().splitlines()[0])

# Prepare note id storages
previous_note_ids = []
current_note_ids = []

while True:

    # Initialize current note ids
    previous_note_ids = current_note_ids
    current_note_ids = []

    # Request notes in the local timeline
    res_loc = requests.post(
            endpoint_local, 
            json={
                "i": token,
                "userId": userId,
                "sinceDate": epoch_sec,
                "limit": batch_size
            }
    )
    
    # Check response normality
    if res_loc.status_code != 200:
        print(f"Unsuccessful response from {endpoint_local}: {res_loc}")
        batch_interval *= 2
        time.sleep(batch_interval)
        continue
    
    notes = res_loc.json()
    for i, note in enumerate(notes):
        
        # Append note ID to the current note id list
        note_id = note["id"]
        current_note_ids.append(note_id)
        
        # Check note duplication
        if note_id in previous_note_ids:
            print(f"Got Existing ID {i + 1}: {note_id}")
            time.sleep(note_interval)
            continue
        print(f"Got NEW ID {i + 1}: {note_id}")

        # Request reactions on a note  
        res_rxn = requests.post(
            endpoint_rxn,
            json={"noteId": note_id}
        )
        
        # Check response normality
        if res_rxn.status_code != 200:
            print(f"Unsuccessful response from {endpoint_rxn}: {res_rxn}")
            note_interval *= 2
            time.sleep(note_interval)
            continue

        # Get type of a reaction
        rxns = res_rxn.json()
        for rxn in rxns:
            rxn_type = rxn["type"]
            print(f"Found reaction: {rxn_type}")
            if rxn_type in rxn_counts:
                rxn_counts[rxn_type] = rxn_counts[rxn_type] + 1
            else:
                rxn_counts[rxn_type] = 1
            
        # Wait for the next note request
        note_interval = int(config_d["NoteInterval"])
        time.sleep(note_interval)

    # Sort and save
    reacitons = sorted(rxn_counts.items(), key=lambda x : x[1], reverse=True)
    with open(csvname, "w") as f:
        for rxn_type, count in reacitons:
            f.write(f"{rxn_type},{count}\n")
    print("Saved")

    # Wait for the next batch
    batch_interval = int(config_d["BatchInterval"])
    time.sleep(batch_interval)

    # Set measurement time
    epoch_sec = epoch_sec - 3600
    with open(time_fname, "w") as f:
        f.write(str(epoch_sec))
    meas_time = datetime.fromtimestamp(epoch_sec)
    print("Measurement time: " + meas_time.strftime("%m/%d/%Y, %H:%M:%S"))