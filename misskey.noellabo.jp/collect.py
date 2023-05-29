#! /usr/bin/env python3
import requests, time, configparser
from datetime import datetime, timedelta

# Load config
CONFIG_FNAME = 'server.cfg'
TIME_FNAME = "current_time"
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

# Prepare note id storages
previous_note_ids = []
current_note_ids = []

while True:

    # Initialize current note ids
    previous_note_ids = current_note_ids
    current_note_ids = []

    # Set measurement time
    now = datetime.now()
    meas_time = now - timedelta(hours=2)
    meas_time_str = meas_time.strftime("%m/%d/%Y, %H:%M:%S")
    epoch_msec = int(meas_time.timestamp()) * 1000
    print(f"Measurement time: " + meas_time_str)

    # Request notes in the local timeline
    print(epoch_msec)
    res_loc = requests.post(
            endpoint_local, 
            json={
                "i": token,
                "userId": userId,
                "sinceDate": epoch_msec,
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
            continue
        print(f"Got NEW ID {i + 1}: {note_id}")

        # Request reactions on a note  
        res_rxn = requests.post(
            endpoint_rxn,
            json={
                "i": token,
                "userId": userId,
                "noteId": note_id
            }
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
    reacitons = sorted(
        rxn_counts.items(), 
        key=lambda x : x[1], 
        reverse=True
    )
    with open(csvname, "w") as f:
        for rxn_type, count in reacitons:
            f.write(f"{rxn_type},{count}\n")

    # Save current time
    with open(TIME_FNAME, "w") as f:
        f.write(str(epoch_msec))
    
    # Wait for the next batch
    finish_time = datetime.now().strftime("%m/%d/%Y, %H:%M:%S")
    print(f"Batch finished at {finish_time}") 
    batch_interval = int(config_d["BatchInterval"])
    time.sleep(batch_interval)
    