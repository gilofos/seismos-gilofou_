import matplotlib.pyplot as plt
from obspy.clients.fdsn import Client
from obspy import UTCDateTime
import matplotlib
import datetime

matplotlib.use('Agg') 

def get_seismo():
    client = Client("EARTHSCOPE")
    try:
        # Παίρνουμε την τωρινή ώρα σε UTC
        # Αφαιρούμε 30 δευτερόλεπτα για να είμαστε σίγουροι ότι ο σέρβερ έχει προλάβει να τα γράψει
        now_utc = UTCDateTime.now() - 30 
        
        # Ζητάμε τα τελευταία 10 λεπτά (600 δευτερόλεπτα)
        st = client.get_waveforms("IU", "ANTO", "00", "BHZ", now_utc - 600, now_utc)
        
        st.detrend('demean')
        st.filter('bandpass', freqmin=0.5, freqmax=5.0)
        
        fig, ax = plt.subplots(figsize=(12, 5))
        
        # Μετατροπή σε ώρα Ελλάδος (+2 ώρες τώρα τον Μάρτιο)
        times = st[0].times("utcdatetime")
        times_greek = [(t + 7200).datetime for t in times]
        
        ax.plot(times_greek, st[0].data, color='red', linewidth=1)
        
        # Εμφάνιση της τελευταίας ώρας ενημέρωσης στο γράφημα
        last_time = (now_utc + 7200).strftime('%H:%M:%S')
        ax.set_title(f"LIVE ΣΕΙΣΜΟΓΡΑΦΟΣ ΓΗΛΟΦΟΥ\nΤελευταία ενημέρωση: {last_time}")
        ax.set_ylabel("Ένταση (Counts)")
        ax.set_xlabel("Ώρα Ελλάδος")
        ax.grid(True, alpha=0.3)
        
        # ΣΗΜΑΝΤΙΚΟ: Αποθήκευση με dpi για καθαρότητα
        plt.tight_layout()
        plt.savefig('seismo_live.png', dpi=100)
        plt.close()
        
        print(f"Η εικόνα δημιουργήθηκε επιτυχώς για την ώρα: {last_time}")
        
    except Exception as e:
        print(f"Σφάλμα κατά τη λήψη δεδομένων: {e}")

if __name__ == "__main__":
    get_seismo()
