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
        url = "https://www.seismicportal.eu/fdsnws/event/1/query?limit=50&format=text"
        response = requests.get(url, timeout=15)
        if response.status_code == 200:
            df = pd.read_csv(io.StringIO(response.text), sep='|')
            df['Time'] = df['Time'].apply(lambda x: UTCDateTime(x))
            time_diffs = np.abs(df['Time'] - event_time_utc)
            closest_event_idx = time_diffs.idxmin()
            if time_diffs[closest_event_idx] < 900: 
                region = df.iloc[closest_event_idx]['Description']
                mag = df.iloc[closest_event_idx]['Magnitude']
                clean_region = region.split(',')[0].strip()
                return f"{clean_region} ({mag}R)"
            else:
                return "Τοπική Δόνηση / Μη Ταυτοποιημένη"
        return "Εκτός Δικτύου"
    except Exception:
        return "Άγνωστη Τοποθεσία"

def get_seismo():
    client = Client("NOA")
    now_utc = UTCDateTime.now()
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
    richter_val = 0.1
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

            # Η ΔΙΟΡΘΩΜΕΝΗ ΓΡΑΜΜΗ 85
            max_amp_m = np.max(np.abs(data))
            
            amp_mm = max_amp_m * 1000 
            richter_val = math.log10(amp_mm * 1000) + 1.8 
            richter_val = max(0.1, round(richter_val, 1))
            
            richter_text = f"ΕΚΤΙΜΗΣΗ: {richter_val} Richter"
            if richter_val >= 4.0: color_box = '#FF0000'
            elif richter_val >= 2.5: color_box = '#FF8C00'

            location = get_location_global(end_time)
            time_str = times[-1].strftime('%H:%M')
            log_entry = f"{time_str} | {richter_val}R | {location}\n"
            
            try:
                if not os.path.exists("seismos_history.txt"):
                    with open("seismos_history.txt", "w", encoding="utf-8") as f: f.write("")
                
                with open("seismos_history.txt", "a", encoding="utf-8") as f:
                    f.write(log_entry)
            except: pass

        except Exception:
            richter_text = "Σφάλμα Επεξεργασίας"

    fig, ax = plt.subplots(figsize=(12, 7))
    ax.plot(times, data, color='red', linewidth=1.2)
    limit = max(np.max(np.abs(data)) * 1.5, 2e-6)
    ax.set_ylim([-limit, limit])
    if len(times) > 0: ax.set_xlim([times[0], times[-1]])

    header_msg = f"{richter_text} | Σταθμός: {active_station}"
    plt.figtext(0.5, 0.82, header_msg, ha="center", fontsize=14, color="white", fontweight='bold', 
                bbox=dict(facecolor=color_box, alpha=0.9, edgecolor='none', pad=10))

    recent_events = []
    if os.path.exists("seismos_history.txt"):
        with open("seismos_history.txt", "r", encoding="utf-8") as f:
            all_lines = f.readlines()
            recent_events = all_lines[-3:]
            recent_events.reverse()

    y_history = 0.16
    plt.figtext(0.5, 0.21, "ΠΡΟΣΦΑΤΗ ΔΡΑΣΤΗΡΙΟΤΗΤΑ (Live Feed)", ha="center", fontsize=10, color="black", fontweight='bold')
    for event in recent_events:
        plt.figtext(0.5, y_history, event.strip(), ha="center", fontsize=9, color="#CC0000", fontweight='bold', 
                    bbox=dict(facecolor='white', alpha=0.8, edgecolor='#DDDDDD', pad=3))
        y_history -= 0.04

    ax.set_ylabel("ΜΕΤΑΤΟΠΙΣΗ ΕΔΑΦΟΥΣ (m)", fontsize=9, fontweight='bold')
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
    ax.set_title("ΣΕΙΣΜΟΓΡΑΦΟΣ ΓΗΛΟΦΟΥ - LIVE (Global Edition)", fontsize=15, fontweight='bold', pad=60)
    current_time_greek = (now_utc + 7200).strftime('%d/%m/%Y %H:%M:%S')
    plt.figtext(0.5, 0.02, f"Τελευταία Ενημέρωση: {current_time_greek} | Δεδομένα: HL Network & EMSC", ha="center", fontsize=8, style='italic', color='#666666')
    ax.grid(True, alpha=0.15, linestyle='--')
    plt.tight_layout(rect=[0, 0.06, 1, 0.96])
    plt.savefig('seismo_live.png', dpi=110)
    plt.close()

if __name__ == "__main__":
    get_seismo()
