import matplotlib.pyplot as plt
from obspy.clients.fdsn import Client
from obspy import UTCDateTime
import matplotlib.dates as mdates
import matplotlib
import numpy as np
matplotlib.use('Agg')

def get_seismo():
    client = Client("NOA")
    # Ώρα τώρα και ρύθμιση για Ελλάδα (+2 ώρες)
    now_utc = UTCDateTime.now()
    greece_time_now = now_utc + 7200
    last_time_str = greece_time_now.strftime('%H:%M:%S')
    
    # Παράθυρο χρόνου: Τελευταία 10 λεπτά
    start_time = now_utc - 600
    end_time = now_utc

    try:
        # Λήψη δεδομένων από σταθμό LIT (Λιτόχωρο)
        st = client.get_waveforms("HL", "LIT", "", "HHZ", start_time, end_time)
        st.detrend('demean')
        st.filter('bandpass', freqmin=1.0, freqmax=10.0)
        data = st[0].data
        times = [(t + 7200).datetime for t in st[0].times("utcdatetime")]
        title_status = "LIVE ΣΤΑΘΜΟΣ: ΛΙΤΟΧΩΡΟ"
    except Exception as e:
        # Αν ο σταθμός δεν απαντάει, φτιάχνουμε "τεχνητό" άξονα για να μη χαλάει η εικόνα
        print(f"Data Error: {e}")
        data = np.zeros(100)
        # Φτιάχνουμε 100 χρονικά σημεία για τα τελευταία 10 λεπτά
        times = [(start_time + 7200 + i*6).datetime for i in range(100)]
        title_status = "ΣΤΑΘΜΟΣ ΕΚΤΟΣ ΣΥΝΔΕΣΗΣ (ΑΝΑΜΟΝΗ)"

    # Δημιουργία Γραφήματος
    fig, ax = plt.subplots(figsize=(12, 5))
    ax.plot(times, data, color='red', linewidth=1)
    
    # Ρύθμιση άξονα Χ: Να δείχνει μόνο ώρα και λεπτά
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
    
    # Τίτλος με την τελευταία ενημέρωση
    ax.set_title(f"{title_status}\nΤελευταία ενημέρωση: {last_time_str}")
    ax.grid(True, alpha=0.3)
    
    # Επιβολή ορίων στον άξονα Χ για να μην "ξεχειλώνει"
    ax.set_xlim([times[0], times[-1]])
    
    # Αποθήκευση
    plt.savefig('seismo_live.png', dpi=100)
    plt.close()
    print(f"Η εικόνα ενημερώθηκε επιτυχώς: {last_time_str}")

if __name__ == "__main__":
    get_seismo()
