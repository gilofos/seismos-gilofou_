import matplotlib.pyplot as plt
from obspy.clients.fdsn import Client
from obspy import UTCDateTime
import matplotlib.dates as mdates
import numpy as np
import matplotlib
import math

# Χρήση Agg για να τρέχει στο GitHub Actions χωρίς γραφικό περιβάλλον
matplotlib.use('Agg')

def get_seismo():
    client = Client("NOA")
    now_utc = UTCDateTime.now()
    
    # Χρόνος: 4 λεπτά πίσω για σίγουρη λήψη δεδομένων
    end_time = now_utc - 240
    start_time = end_time - 600
    
    richter_text = "Ησυχία"
    richter_val = 0.0

    try:
        # 1. Λήψη δεδομένων ΚΑΙ της απόκρισης του σταθμού (Inventory)
        st = client.get_waveforms("HL", "JAN", "", "HHZ", start_time, end_time)
        inv = client.get_stations(network="HL", station="JAN", level="response", 
                                 starttime=start_time, endtime=end_time)
        
        st.detrend('demean')
        
        # 2. ΜΕΤΑΤΡΟΠΗ ΣΕ ΜΕΤΡΑ (Απαραίτητο για τον υπολογισμό Ρίχτερ)
        # Μετατρέπει τα "counts" σε πραγματική μετατόπιση εδάφους (DISP)
        st.remove_response(inventory=inv, output="DISP")
        st.filter('bandpass', freqmin=0.5, freqmax=10.0)
        
        tr = st[0]
        data = tr.data
        times = [(t + 7200).datetime for t in tr.times("utcdatetime")]

        # 3. ΑΛΓΟΡΙΘΜΟΣ ΥΠΟΛΟΓΙΣΜΟΥ ΡΙΧΤΕΡ (ML)
        # Βρίσκουμε το μέγιστο πλάτος (A) σε μέτρα
        max_amp_m = np.max(np.abs(data))
        
        if max_amp_m > 1e-9: # Αν υπάρχει κίνηση πάνω από το θόρυβο
            amp_mm = max_amp_m * 1000 # Μετατροπή σε χιλιοστά (mm)
            # Λογαριθμικός τύπος Richter: log10(πλάτος) + διόρθωση απόστασης
            # Χρησιμοποιούμε μια μέση διόρθωση (+1.2) για τοπική δραστηριότητα
            richter_val = math.log10(amp_mm * 1000) + 1.2
            richter_text = f"ΕΚΤΙΜΗΣΗ: {max(0, round(richter_val, 1))} Richter"
        else:
            richter_text = "Φυσιολογική Δραστηριότητα"

    except Exception as e:
        print(f"Σφάλμα λήψης: {e}")
        data = np.zeros(100)
        times = [(start_time + 7200 + i*6).datetime for i in range(100)]
        richter_text = "Σφάλμα Σύνδεσης"

    # ΣΧΕΔΙΑΣΗ ΓΡΑΦΗΜΑΤΟΣ
    fig, ax = plt.subplots(figsize=(12, 6))
    
    # Σχεδίαση της γραμμής (σε μέτρα πλέον)
    ax.plot(times, data, color='red', linewidth=1.1)
    
    # Εμφάνιση Ρίχτερ σε πλαίσιο
    color_box = 'red' if richter_val > 3.0 else '#333333'
    plt.figtext(0.5, 0.88, richter_text, ha="center", fontsize=16, 
                color="white", fontweight='bold', 
                bbox=dict(facecolor=color_box, alpha=0.8, edgecolor='none', pad=8))

    # Ρυθμίσεις αξόνων
    ax.set_ylabel("ΜΕΤΑΤΟΠΙΣΗ ΕΔΑΦΟΥΣ (m)", fontsize=10, fontweight='bold')
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
    
    # Τίτλος
       # Τίτλος
    ax.set_title("ΣΕΙΣΜΟΓΡΑΦΟΣ ΓΗΛΟΦΟΥ\n(Βασισμένος σε δεδομένα του σταθμού Ιωαννίνων)", 
              fontsize=13, fontweight='bold', pad=40)

    
    # Επεξήγηση κάτω
    current_update = (now_utc + 7200).strftime('%H:%M:%S')
    plt.figtext(0.5, 0.02, 
                f"Ενημέρωση: {current_update} | Τα Richter υπολογίζονται αυτόματα βάσει του πλάτους ταλάντωσης.", 
                ha="center", fontsize=9, color="#333333", style='italic', 
                bbox=dict(facecolor='#fefefe', alpha=0.9, edgecolor='#cccccc', boxstyle='round,pad=0.5'))

    ax.grid(True, alpha=0.2, linestyle='--')
    
    # Αυτόματη προσαρμογή ορίων Υ για να φαίνεται καλά η γραμμή
    limit = max(np.max(np.abs(data)) * 1.2, 1e-6)
    ax.set_ylim([-limit, limit])
    ax.set_xlim([times[0], times[-1]])
    
    plt.tight_layout(rect=[0, 0.08, 1, 0.95])
    plt.savefig('seismo_live.png', dpi=100)
    plt.close()

if __name__ == "__main__":
    get_seismo()
