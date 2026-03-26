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

# Χρήση Agg για να τρέχει στο GitHub Actions χωρίς περιβάλλον οθόνης
matplotlib.use('Agg')

# --- ΣΥΝΑΡΤΗΣΗ ΕΥΡΕΣΗΣ ΤΟΠΟΘΕΣΙΑΣ (ΠΑΓΚΟΣΜΙΑ ΑΠΟ EMSC) ---
def get_location_global(event_time_utc):
    try:
        # URL για παγκόσμιους σεισμούς από το EMSC (Seismic Portal)
        url = "https://www.seismicportal.eu/fdsnws/event/1/query?limit=50&format=text"
        response = requests.get(url, timeout=15)
        
        if response.status_code == 200:
            df = pd.read_csv(io.StringIO(response.text), sep='|')
            df['Time'] = df['Time'].apply(lambda x: UTCDateTime(x))
            
            # Ψάχνουμε τον σεισμό σε ένα παράθυρο 15 λεπτών (για μακρινούς σεισμούς)
            time_diffs = np.abs(df['Time'] - event_time_utc)
            closest_event_idx = time_diffs.idxmin()
            
            if time_diffs[closest_event_idx] < 900: # 15 λεπτά παράθυρο
                region = df.iloc[closest_event_idx]['Description']
                mag = df.iloc[closest_event_idx]['Magnitude']
                # Καθαρισμός ονόματος
                clean_region = region.split(',')[0].strip()
                return f"{clean_region} ({mag}R)"
            else:
                return "Περιοχή: Μη Ταυτοποιημένη"
        else:
            return "Εκτός Δικτύου (Global Feed)"
    except Exception as e:
        print(f"Error fetching location: {e}")
        return "Άγνωστη Τοποθεσία"

def get_seismo():
    client = Client("NOA")
    now_utc = UTCDateTime.now()
    
    # 10 λεπτά καθυστέρηση για σίγουρη λήψη δεδομένων
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

            max_amp_m = np.max(np.abs(data))
            if max_amp_m > 1.5e-7: # Ελαφρώς πιο ευαίσθητο
                amp_mm = max_amp_m * 1000 
                richter_val = math.log10(amp_mm * 1000) + 1.8 
                richter_text = f"ΕΚΤΙΜΗΣΗ: {max(0, round(richter_val, 1))} Richter"
                
                if richter_val >= 4.0: color_box = '#FF0000'
                elif richter_val >= 2.5: color_box = '#FF8C00'

                # Καταγραφή στο ιστορικό αν είναι πάνω από 1.8R
                if richter_val >= 1.8:
                    location = get_location_global(end_time)
                    time_str = times[-1].strftime('%d/%m %H:%M')
                    log_entry = f"{time_str} | {round(richter_val, 1)}R | {location}\n"
                    
                    try:
                        with open("seismos_history.txt", "a", encoding="utf-8") as f:
                            f.write(log_entry)
                    except Exception as e:
                        print(f"Error: {e}")
            else:
                richter_text = "Φυσιολογική Δραστηριότητα"
        except Exception as e:
            richter_text = "Σφάλμα Επεξεργασίας"

    fig, ax = plt.subplots(figsize=(12, 7))
    ax.plot(times, data, color='red', linewidth=1.2)
    
    limit = max(np.max(np.abs(data)) * 1.5, 2e-6)
    ax.set_ylim([-limit, limit])
    if len(times) > 0:
        ax.set_xlim([times[0], times[-1]])

    # Σχεδίαση P, S, L μόνο αν έχουμε αξιόλογο σήμα
    if len(times) > 10 and richter_val >= 1.8:
        y_pos = limit * 0.80 
        idx_p, idx_s, idx_l = int(len(times)*0.15), int(len(times)*0.45), int(len(times)*0.75)
        for label, idx in zip(['P', 'S', 'L'], [idx_p, idx_s, idx_l]):
            ax.text(times[idx], y_pos, label, color='black', fontsize=9, fontweight='bold', 
                    ha='center', bbox=dict(facecolor='white', alpha=0.6, edgecolor='none'))

    header_msg = f"{richter_text} | Σταθμός: {active_station}"
    plt.figtext(0.5, 0.88, header_msg, ha="center", fontsize=14, color="white", fontweight='bold', 
                bbox=dict(facecolor=color_box, alpha=0.9, edgecolor='none', pad=10))

    # Ιστορικό
    recent_events = []
    try:
        with open("seismos_history.txt", "r", encoding="utf-8") as f:
            all_lines = f.readlines()
            recent_events = all_lines[-3:]
            recent_events.reverse()
    except:
        recent_events = ["Αναμονή για την πρώτη καταγραφή (>1.8R)"]

    y_history = 0.16
    plt.figtext(0.5, 0.21, "ΠΡΟΣΦΑΤΗ ΔΡΑΣΤΗΡΙΟΤΗΤΑ (3 Τελευταίοι >1.8 Richter)", 
                ha="center", fontsize=10, color="black", fontweight='bold')
    
    for event in recent_events:
        plt.figtext(0.5, y_history, event.strip(), ha="center", fontsize=9, 
                    color="#CC0000", fontweight='bold', 
                    bbox=dict(facecolor='white', alpha=0.8, edgecolor='#DDDDDD', pad=3))
        y_history -= 0.04

    ax.set_ylabel("ΜΕΤΑΤΟΠΙΣΗ ΕΔΑΦΟΥΣ (m)", fontsize=9, fontweight='bold')
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
    ax.set_title("ΣΕΙΣΜΟΓΡΑΦΟΣ ΓΗΛΟΦΟΥ - LIVE (Global Edition)", fontsize=15, fontweight='bold', pad=60)
    
    current_time_greek = (now_utc + 7200).strftime('%d/%m/%Y %H:%M:%S')
    plt.figtext(0.5, 0.02, f"Τελευταία Ενημέρωση: {current_time_greek} | Δεδομένα: HL Network & EMSC", 
                ha="center", fontsize=8, style='italic', color='#666666')

    ax.grid(True, alpha=0.15, linestyle='--')
    plt.tight_layout(rect=[0, 0.06, 1, 0.96])
    plt.savefig('seismo_live.png', dpi=110)
    plt.close()

if __name__ == "__main__":
    get_seismo()
