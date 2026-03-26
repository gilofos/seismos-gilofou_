import matplotlib.pyplot as plt
from obspy.clients.fdsn import Client
from obspy import UTCDateTime
import matplotlib.dates as mdates
import numpy as np
import matplotlib
import math
import datetime
import pandas as pd
import requests
import io
import os

# Χρήση Agg για να τρέχει στο GitHub Actions
matplotlib.use('Agg')

# --- ΣΥΝΑΡΤΗΣΗ ΕΥΡΕΣΗΣ ΤΟΠΟΘΕΣΙΑΣ ---
def get_location_global(event_time_utc):
    try:
        # URL για παγκόσμιους σεισμούς από το EMSC
        url = "https://www.seismicportal.eu/fdsnws/event/1/query?limit=50&format=text"
        response = requests.get(url, timeout=15)
        
        if response.status_code == 200:
            df = pd.read_csv(io.StringIO(response.text), sep='|')
            df['Time'] = df['Time'].apply(lambda x: UTCDateTime(x))
            
            # Ψάχνουμε τον σεισμό σε ένα παράθυρο 15 λεπτών
            time_diffs = np.abs(df['Time'] - event_time_utc)
            closest_event_idx = time_diffs.idxmin()
            
            if time_diffs[closest_event_idx] < 900: 
                region = df.iloc[closest_event_idx]['Description']
                mag = df.iloc[closest_event_idx]['Magnitude']
                clean_region = region.split(',')[0].strip()
                return f"{clean_region} ({mag}R)"
            else:
                return "Τοπική Δόνηση / Μη Ταυτοποιημένη"
        else:
            return "Εκτός Δικτύου (Feed Error)"
    except Exception:
        return "Άγνωστη Τοποθεσία"

def get_seismo():
    client = Client("NOA")
    now_utc = UTCDateTime.now()
    
    # Καθυστέρηση για λήψη δεδομένων
    end_time = now_utc - 600
    start_time = end_time - 600
    
    stations = ["JAN", "LKD2", "EVR", "PRK"]
    st = None
    active_station = "N/A"

    for sta in stations:
        try:
            st = client.get_waveforms("HL", sta, "", "HHZ", start_time, end_time)
            if len(st) > 0:
                active_station = sta
                break
        except Exception:
            continue

    richter_text = "Αναμονή Δεδομένων"
    richter_val = 0.0
    data = np.zeros(100)
    now_greek = datetime.datetime.now()
    times = [now_greek - datetime.timedelta(seconds=i) for i in range(100)]
    color_box = '#555555'

    if st:
        try:
            tr = st[0]
            inv = client.get_stations(network="HL", station=active_station, level="response", 
                                     starttime=start_time, endtime=end_time)
            
            tr.detrend('demean')
            tr.remove_response(inventory=inv, output="DISP")
            tr.filter('bandpass', freqmin=0.5, freqmax=10.0)
            
            data = tr.data
            times = [(t + 7200).datetime for t in tr.times("utcdatetime")]

            max_amp_m = np.max(np
