import matplotlib
matplotlib.use('Agg') 
import matplotlib.pyplot as plt
from obspy.clients.fdsn import Client
from obspy import UTCDateTime

# Σύνδεση με το δίκτυο
client = Client("EARTHSCOPE") 

def run_seismo():
    print("Ξεκινάω την ανανέωση...")
    try:
        # Παίρνουμε τα τελευταία 10 λεπτά (600 δευτερόλεπτα)
        now = UTCDateTime.now() - 15
        st = client.get_waveforms("IU", "ANTO", "00", "BHZ", now - 600, now)
        
        # --- ΕΠΕΞΕΡΓΑΣΙΑ ΓΙΑ ΤΑΧΥΤΗΤΑ ---
        st.detrend('demean')
        st.filter('bandpass', freqmin=0.5, freqmax=5.0)
        st.decimate(5, strict_length=False) # Κάνει το γράφημα 5 φορές πιο γρήγορο!
        
        # --- ΣΧΕΔΙΑΣΗ ---
        plt.close('all')
        fig, ax = plt.subplots(figsize=(12, 5), dpi=90)
        
        # Ώρα Ελλάδος (+2 ώρες)
        times = st.times("utcdatetime") 
        times_greek = [(t + 7200).datetime for t in times] 
        
        ax.plot(times_greek, st.data, color='#d62828', linewidth=0.8)
        
        update_time = (now + 7200).strftime('%H:%M:%S')
        ax.set_title(f"LIVE ΣΕΙΣΜΟΓΡΑΦΟΣ ΓΗΛΟΦΟΥ\nΤελευταία ενημέρωση: {update_time}", fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig('seismo_live.png') # Η εικόνα που θα βλέπουμε
        print(f"ΕΠΙΤΥΧΙΑ! Ενημερώθηκε στις {update_time}")

    except Exception as e:
        print(f"Σφάλμα: {e}")

if __name__ == "__main__":
    run_seismo()
