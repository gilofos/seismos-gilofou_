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

# --- ΣΥΝΑΡΤΗΣΗ ΕΥΡΕΣΗΣ ΤΟΠΟΘΕΣΙΑΣ ΑΠΟ ΝΟΑ ---
def get_noa_location(event_time_utc):
    try:
        # URL για τους πρόσφατους σεισμούς του Γεωδυναμικού (τελευταίοι 50)
        url = "http://eida.gein.noa.gr/fdsnws/event/1/query?limit=50&format=text"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            # Διάβασμα των δεδομένων σε Pandas DataFrame
            # Το format είναι Text, χωρισμένο με '|'
            df = pd.read_csv(io.StringIO(response.text), sep='|')
            
            # Μετατροπή της στήλης Time σε UTCDateTime για σύγκριση
            df['Time'] = df['Time'].apply(lambda x: UTCDateTime(x))
            
            # Εύρεση του σεισμού που έγινε πιο κοντά χρονικά (μέσα σε 5 λεπτά απόκλιση)
            # γιατί η δόνηση φτάνει αργότερα στον σταθμό μας
            time_diffs = np.abs(df['Time'] - event_time_utc)
            closest_event_idx = time_diffs.idxmin()
            
            if time_diffs[closest_event_idx] < 300: # 300 δευτερόλεπτα (5 λεπτά)
                region = df.iloc[closest_event_idx]['Description']
                # Καθαρισμός κειμένου (αφαίρεση 'Greece', κλπ αν χρειάζεται)
                clean_region = region.split(',')[0].strip()
                return clean_region
            else:
                return "Τοποθεσία: Εκτός Δικτύου ΝΟΑ"
        else:
            return "Σφάλμα Σύνδεσης με ΝΟΑ"
    except Exception as e:
        print(f"Error fetching location: {e}")
        return "Άγνωστη Τοποθεσία"

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
    # Ώρα Ελλάδος για τα αρχικά κενά δεδομένα (UTC + 2 ώρες)
    now_greek = datetime.datetime.now()
    times = [now_greek - datetime.timedelta(seconds=i) for i in range(100)]
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

            # Υπολογισμός Ρίχτερ (ML - Τοπικό Μέγεθος - Προσέγγιση)
            max_amp_m = np.max(np.abs(data))
            if max_amp_m > 2e-7: # Threshold λίγο πιο ψηλό για να ξεχωρίζει από θόρυβο
                amp_mm = max_amp_m * 1000 
                # Εμπειρικός τύπος για ML (απαιτεί απόσταση, εδώ είναι προσέγγιση)
                richter_val = math.log10(amp_mm * 1000) + 1.8 
                richter_text = f"ΕΚΤΙΜΗΣΗ: {max(0, round(richter_val, 1))} Richter"
                
                # Χρώμα ανάλογα με την ένταση
                if richter_val >= 4.0: color_box = '#FF0000' # Κόκκινο
                elif richter_val >= 2.5: color_box = '#FF8C00' # Πορτοκαλί

                # --- ΣΥΣΤΗΜΑ ΙΣΤΟΡΙΚΟΥ ΚΑΙ ΤΟΠΟΘΕΣΙΑΣ ---
                # Καταγράφουμε μόνο αν είναι πάνω από 2.0 Ρίχτερ
                if richter_val >= 2.0:
                    # Βρίσκουμε την τοποθεσία από το ΝΟΑ (χρησιμοποιούμε end_time_utc)
                    location = get_noa_location(end_time)
                    
                    time_str = times[-1].strftime('%d/%m %H:%M') # Ώρα Ελλάδος
                    log_entry = f"{time_str} | {round(richter_val, 1)}R | {location}\n"
                    
                    # Αποθήκευση στο αρχείο ιστορικού
                    try:
                        with open("seismos_history.txt", "a", encoding="utf-8") as f:
                            f.write(log_entry)
                        print(f"Νέος σεισμός καταγράφηκε: {log_entry}")
                    except Exception as e:
                        print(f"Error writing to history file: {e}")

            else:
                richter_text = "Φυσιολογική Δραστηριότητα"
        except Exception as e:
            richter_text = "Σφάλμα Επεξεργασίας"
            print(f"Error processing data: {e}")

    # 3. ΣΧΕΔΙΑΣΗ ΓΡΑΦΗΜΑΤΟΣ
    fig, ax = plt.subplots(figsize=(12, 7)) # Λίγο πιο ψηλό για να χωράει το ιστορικό
    ax.plot(times, data, color='red', linewidth=1.2)
    
    # Σταθεροποίηση ορίων Υ (δυναμικά αλλά με minimum)
    limit = max(np.max(np.abs(data)) * 1.5, 2e-6)
    ax.set_ylim([-limit, limit])
    if len(times) > 0:
        ax.set_xlim([times[0], times[-1]])

    # --- ΤΟΠΟΘΕΤΗΣΗ P, S, L ---
    if len(times) > 10 and richter_val >= 2.0:
        y_pos = limit * 0.80 
        idx_p = int(len(times)*0.15)
        idx_s = int(len(times)*0.45)
        idx_l = int(len(times)*0.75)
        
        for label, idx in zip(['P (Primary)', 'S (Secondary)', 'L (Surface)'], [idx_p, idx_s, idx_l]):
            ax.text(times[idx], y_pos, label, color='black', fontsize=9, fontweight='bold', 
                    ha='center', bbox=dict(facecolor='white', alpha=0.6, edgecolor='none', pad=2))

    # Πλαίσιο Ρίχτερ και Σταθμού (Πάνω μέρος)
    header_msg = f"{richter_text} | Σταθμός: {active_station}"
    plt.figtext(0.5, 0.88, header_msg, ha="center", fontsize=14, 
                color="white", fontweight='bold', 
                bbox=dict(facecolor=color_box, alpha=0.9, edgecolor='none', pad=10))

    # --- ΕΜΦΑΝΙΣΗ ΙΣΤΟΡΙΚΟΥ (3 Τελευταίοι) ---
    recent_events = []
    try:
        with open("seismos_history.txt", "r", encoding="utf-8") as f:
            all_lines = f.readlines()
            # Παίρνουμε τις 3 τελευταίες γραμμές και τις αντιστρέφουμε (πιο πρόσφατος πάνω)
            recent_events = all_lines[-3:]
            recent_events.reverse()
    except:
        recent_events = ["Δεν υπάρχει πρόσφατη καταγραφή (>2.0R)"]

    # Σχεδίαση της ταμπέλας ιστορικού στο κάτω μέρος
    y_history = 0.16
    plt.figtext(0.5, 0.21, "ΠΡΟΣΦΑΤΗ ΔΡΑΣΤΗΡΙΟΤΗΤΑ (3 Τελευταίοι >2.0 Richter)", 
                ha="center", fontsize=10, color="black", fontweight='bold')
    
    for event in recent_events:
        plt.figtext(0.5, y_history, event.strip(), ha="center", fontsize=9, 
                    color="#CC0000", fontweight='bold', 
                    bbox=dict(facecolor='white', alpha=0.8, edgecolor='#DDDDDD', pad=3))
        y_history -= 0.04

    # Άξονες και Τίτλοι
    ax.set_ylabel("ΜΕΤΑΤΟΠΙΣΗ ΕΔΑΦΟΥΣ (m)", fontsize=9, fontweight='bold')
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
    ax.set_title("ΣΕΙΣΜΟΓΡΑΦΟΣ ΓΗΛΟΦΟΥ - LIVE", fontsize=15, fontweight='bold', pad=60)
    
    # Footer (Ώρα Ελλάδος: UTC + 2)
    current_time_greek = (now_utc + 7200).strftime('%d/%m/%Y %H:%M:%S')
    plt.figtext(0.5, 0.02, f"Τελευταία Ενημέρωση: {current_time_greek} (Ώρα Ελλάδος) | Δεδομένα: HL Network (NOA)", 
                ha="center", fontsize=8, style='italic', color='#666666')

    ax.grid(True, alpha=0.15, linestyle='--')
    # Προσαρμογή layout για να χωρέσουν όλα
    plt.tight_layout(rect=[0, 0.06, 1, 0.96])
    
    # Αποθήκευση εικόνας
    plt.savefig('seismo_live.png', dpi=110)
    plt.close()

if __name__ == "__main__":
    get_seismo()
