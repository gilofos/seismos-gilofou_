import matplotlib.pyplot as plt
from obspy.clients.fdsn import Client
from obspy import UTCDateTime
import matplotlib
matplotlib.use('Agg') # Για να τρέχει στο GitHub χωρίς οθόνη

def get_seismo():
    client = Client("EARTHSCOPE")
    try:
        # Παίρνουμε τα τελευταία 10 λεπτά
        now = UTCDateTime.now()
        st = client.get_waveforms("IU", "ANTO", "00", "BHZ", now - 600, now)
        
        st.detrend('demean')
        st.filter('bandpass', freqmin=0.5, freqmax=5.0)
        
        fig, ax = plt.subplots(figsize=(12, 5))
        times = st[0].times("utcdatetime")
        # Μετατροπή σε ώρα Ελλάδος (+2 ώρες ή +3 ανάλογα την εποχή)
        times_greek = [(t + 7200).datetime for t in times]
        
        ax.plot(times_greek, st[0].data, color='red', linewidth=1)
        
        last_time = (now + 7200).strftime('%H:%M:%S')
        ax.set_title(f"LIVE ΣΕΙΣΜΟΓΡΑΦΟΣ ΓΗΛΟΦΟΥ\nΤελευταία ενημέρωση: {last_time}")
        ax.set_ylabel("Ένταση (Counts)")
        ax.set_xlabel("Ώρα Ελλάδος")
        ax.grid(True, alpha=0.3)
        
        plt.savefig('seismo_live.png', dpi=100)
        plt.close()
        print(f"Η εικόνα δημιουργήθηκε στις {last_time}")
    except Exception as e:
        print(f"Σφάλμα: {e}")

if __name__ == "__main__":
    get_seismo()
