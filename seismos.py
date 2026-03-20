import matplotlib.pyplot as plt
from obspy.clients.fdsn import Client
from obspy import UTCDateTime
import matplotlib.dates as mdates
import numpy as np
import matplotlib
import math
import datetime

# Χρήση Agg για να τρέχει στο GitHub Actions χωρίς περιβάλλον οθόνης
matplotlib.use('Agg')

def get_seismo():
    client = Client("NOA")
    now_utc = UTCDateTime.now()
    
    # 10 λεπτά καθυστέρηση για σίγουρη λήψη δεδομένων από τον server
    end_time = now_utc - 600
    start_time = end_time - 600
    
    # Λίστα σταθμών για backup (Ήπειρος και κοντινοί)
    stations = ["JAN", "LKD2", "EVR", "PRK"]
    
    st = None
    active_station = "N/A"

    # 1. ΑΝΑΖΗΤΗΣΗ ΕΝΕΡΓΟΥ ΣΤΑΘΜΟΥ
    for sta in stations:
        try:
            print(f"Δοκιμή σύνδεσης με: {sta}...")
            st = client.get_waveforms("HL", sta, "", "HHZ", start_time, end_time)
            if len(st) > 0:
                active_station = sta
                print(f"Επιτυχία! Χρήση σταθμού: {sta}")
                break
        except Exception:
            continue

    # Προετοιμασία μεταβλητών
    richter_text = "Αναμονή Δεδομένων"
    richter_val = 0.0
    data = np.zeros(100)
    times = [datetime.datetime.now() - datetime.timedelta(seconds=i) for i in range(100)]
    color_box = '#555555' # Γκρι για ησυχία

    # 2. ΕΠΕΞΕΡΓΑΣΙΑ ΔΕΔΟΜΕΝΩΝ
    if st:
        try:
            tr = st[0] # Παίρνουμε το πρώτο Trace του Stream
            inv = client.get_stations(network="HL", station=active_station, level="response", 
                                     starttime=start_time, endtime=end_time)
            
            tr.detrend('demean')
            tr.remove_response(inventory=inv, output="DISP") # Μετατροπή σε μέτρα (Displacement)
            tr.filter('bandpass', freqmin=0.5, freqmax=10.0)
            
            data = tr.data
            # Μετατροπή UTC σε Python datetime + 2 ώρες για ώρα Ελλάδος
            times = [(t + 7200).datetime for t in tr.times("utcdatetime")]

            # Υπολογισμός Ρίχτερ (ML - Τοπικό Μέγεθος)
            max_amp_m = np.max(np.abs(data))
            if max_amp_m > 1e-7: # Threshold για να ξεχωρίζει τον σεισμό από τον θόρυβο
                amp_mm = max_amp_m * 1000 
                richter_val = math.log10(amp_mm * 1000) + 1.2
                richter_text = f"ΕΚΤΙΜΗΣΗ: {max(0, round(richter_val, 1))} Richter"
                
                # Χρώμα ανάλογα με την ένταση
                if richter_val >= 4.0: color_box = '#FF0000' # Κόκκινο
                elif richter_val >= 2.5: color_box = '#FF8C00' # Πορτοκαλί
            else:
                richter_text = "Φυσιολογική Δραστηριότητα"
        except Exception as e:
            richter_text = "Σφάλμα Επεξεργασίας"
            print(f"Error: {e}")

    # 3. ΣΧΕΔΙΑΣΗ ΓΡΑΦΗΜΑΤΟΣ
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.plot(times, data, color='red', linewidth=1.2)
    
    # Σταθεροποίηση ορίων Υ (δυναμικά)
    limit = max(np.max(np.abs(data)) * 1.5, 1e-6)
    ax.set_ylim([-limit, limit])
    if len(times) > 0:
        ax.set_xlim([times[0], times[-1]])

    # --- ΤΟΠΟΘΕΤΗΣΗ P, S, L (Εκεί που τα ήθελες!) ---
    if len(times) > 10:
        y_pos = limit * 0.75 # Στο 75% του ύψους για να μην "πατάει" τη γραμμή
        idx_p, idx_s, idx_l = int(len(times)*0.2), int(len(times)*0.5), int(len(times)*0.8)
        
        for label, idx in zip(['P', 'S', 'L'], [idx_p, idx_s, idx_l]):
            ax.text(times[idx], y_pos, label, color='black', fontsize=11, fontweight='bold', 
                    ha='center', bbox=dict(facecolor='white', alpha=0.7, edgecolor='none'))

    # Πλαίσιο Ρίχτερ και Σταθμού
    header_msg = f"{richter_text} | Σταθμός: {active_station}"
    plt.figtext(0.5, 0.83, header_msg, ha="center", fontsize=14, 
                color="white", fontweight='bold', 
                bbox=dict(facecolor=color_box, alpha=0.9, edgecolor='none', pad=8))

    # Άξονες και Τίτλοι
    ax.set_ylabel("ΜΕΤΑΤΟΠΙΣΗ ΕΔΑΦΟΥΣ (m)", fontsize=9, fontweight='bold')
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
    ax.set_title("ΣΕΙΣΜΟΓΡΑΦΟΣ ΓΗΛΟΦΟΥ - LIVE", fontsize=13, fontweight='bold', pad=45)
    
    # Footer
    current_time = (now_utc + 7200).strftime('%H:%M:%S')
    plt.figtext(0.5, 0.02, f"Ενημέρωση: {current_time} | Αυτόματη επιλογή ενεργού σταθμού σε περίπτωση βλάβης", 
                ha="center", fontsize=8, style='italic', color='#666666')

    ax.grid(True, alpha=0.15, linestyle='--')
    plt.tight_layout(rect=[0, 0.05, 1, 0.95])
    
    # Αποθήκευση εικόνας
    plt.savefig('seismo_live.png', dpi=110)
    plt.close()

if __name__ == "__main__":
    get_seismo()
