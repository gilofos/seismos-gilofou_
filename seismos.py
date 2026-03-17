import matplotlib.pyplot as plt
from obspy.clients.fdsn import Client
from obspy import UTCDateTime
import matplotlib
matplotlib.use('Agg') 

def get_seismo():
    # Σύνδεση με το Αστεροσκοπείο Αθηνών
    client = Client("NOA") 
    try:
        # Παίρνουμε δεδομένα από το τελευταίο 10λεπτο
        now_utc = UTCDateTime.now() - 30
        
        # Σταθμός LIT (Λιτόχωρο) - Δίκτυο HL - Κανάλι HHZ
        st = client.get_waveforms("HL", "LIT", "", "HHZ", now_utc - 600, now_utc)
        
        st.detrend('demean')
        st.filter('bandpass', freqmin=1.0, freqmax=10.0)
        
        fig, ax = plt.subplots(figsize=(12, 5))
        
        # Μετατροπή σε ώρα Ελλάδος (+2 ώρες)
        times = st[0].times("utcdatetime")
        times_greek = [(t + 7200).datetime for t in times]
        
        ax.plot(times_greek, st[0].data, color='red', linewidth=0.8)
        
        last_time = (now_utc + 7200).strftime('%H:%M:%S')
        ax.set_title(f"LIVE ΣΕΙΣΜΟΓΡΑΦΟΣ ΓΗΛΟΦΟΥ (Σταθμός: Λιτόχωρο)\nΤελευταία ενημέρωση: {last_time}")
        ax.set_ylabel("Ταχύτητα Εδάφους")
        ax.set_xlabel("Ώρα Ελλάδος")
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig('seismo_live.png', dpi=100)
        plt.close()
        print(f"Update Success: {last_time}")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    get_seismo()
