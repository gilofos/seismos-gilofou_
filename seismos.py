import matplotlib.pyplot as plt
from obspy.clients.fdsn import Client
from obspy import UTCDateTime
import matplotlib.dates as mdates
import numpy as np
import matplotlib
import math
import datetime

# Χρήση Agg για το GitHub Actions
matplotlib.use('Agg')

def get_seismo():
    client = Client("NOA")
    now_utc = UTCDateTime.now()
    
    # 10 λεπτά καθυστέρηση για να προλάβει ο server να έχει τα δεδομένα
    end_time = now_utc - 600
    start_time = end_time - 600
    
    # Λίστα σταθμών: Πρώτα τα Ιωάννινα, μετά εναλλακτικοί κοντά στην Ήπειρο
    stations = ["JAN", "LKD2", "EVR", "PRK"]
    
    st = None
    active_station = "N/A"

    # ΔΟΚΙΜΗ ΣΤΑΘΜΩΝ ΜΕΧΡΙ ΝΑ ΒΡΕΙ ΣΗΜΑ
    for sta in stations:
        try:
            print(f"Προσπάθεια σύνδεσης με: {sta}...")
            st = client.get_waveforms("HL", sta, "", "HHZ", start_time, end_time)
            if len(st) > 0:
                active_station = sta
                print(f"Επιτυχία! Χρήση σταθμού {sta}")
                break
        except Exception as e:
            print(f"Ο σταθμός {sta} είναι εκτός: {e}")
            continue

    # Προετοιμασία δεδομένων
    richter_text = "Αναμονή Δεδομένων"
    richter_val = 0.0
    data = np.zeros(100)
    times = [datetime.datetime.now() - datetime.timedelta(seconds=i) for i in range(100)]
    color_box = '#555555'

    if st:
        try:
            tr = st[0] # Παίρνουμε το πρώτο trace
            inv = client.get_stations(network="HL", station=active_station, level="response", 
                                     starttime=start_time, endtime=end_time)
            
            tr.detrend('demean')
            tr.remove_response(inventory=inv, output="DISP")
            tr.filter('bandpass', freqmin=0.5, freqmax=10.0)
            
            data = tr.data
            times = [(t + 7200).datetime for t in tr.times("utcdatetime")]

            # Υπολογισμός Richter (Προσέγγιση)
            max_amp_m = np.max(np.abs(data))
            if max_amp_m > 1e-7:
                amp_mm = max_amp_m * 1000 
                richter_val = math.log10(amp_mm * 1000) + 1.2
                richter_text = f"ΕΚΤΙΜΗΣΗ: {max(0, round(richter_val, 1))} Richter"
                if richter_val >= 4.0: color_box = '#FF0000'
                elif richter_val >= 2.5: color_box = '#FF8C00'
            else:
                richter_text = "Φυσιολογική Δραστηριότητα"
        except Exception as e:
            richter_text = "Σφάλμα Επεξεργασίας"
            print(f"Error processing: {e}")

    # --- ΣΧΕΔΙΑΣΗ ΓΡΑΦΗΜΑΤΟΣ ---
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.plot(times, data, color='red', linewidth=1.2)
    
    limit = max(np.max(np.abs(data)) * 1.5, 1e-6)
    ax.set_ylim([-limit, limit])
    if len(times) > 0:
        ax.set_xlim([times[0], times[-1]])

    # Πλαίσιο Richter & Σταθμού
    status_msg = f"{richter_text} | Σταθμός: {active_station}"
    plt.figtext(0.5, 0.82, status_msg, ha="center", fontsize=14, 
                color="white", fontweight='bold', 
                bbox=dict(facecolor=color_box, alpha=0.9, edgecolor='none', pad=8))

    ax.set_ylabel("ΜΕΤΑΤΟΠΙΣΗ ΕΔΑΦΟΥΣ (m)", fontsize=9, fontweight='bold')
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
    ax.set_title("ΣΕΙΣΜΟΓΡΑΦΟΣ ΓΗΛΟΦΟΥ - LIVE", fontsize=13, fontweight='bold', pad=40)
    
    update_time = (now_utc + 7200).strftime('%H:%M:%S')
    plt.figtext(0.5, 0.02, f"Τελευταία ενημέρωση: {update_time} | Αυτόματη εναλλαγή σταθμών σε περίπτωση βλάβης", 
                ha="center", fontsize=8, style='italic', color='#666666')

    ax.grid(True, alpha=0.15)
    plt.tight_layout(rect=[0, 0.05, 1, 0.95])
    
    plt.savefig('seismo_live.png', dpi=110)
    plt.close()

if __name__ == "__main__":
    get_seismo()
