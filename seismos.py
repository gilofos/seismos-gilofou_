import matplotlib.pyplot as plt
from obspy.clients.fdsn import Client
from obspy import UTCDateTime
import matplotlib.dates as mdates
import numpy as np
import matplotlib
matplotlib.use('Agg')

def get_seismo():
    client = Client("NOA")
    now_utc = UTCDateTime.now()
    greece_time_now = now_utc + 7200
    
    # Σταθμός Θεσσαλονίκης (HL.THE..HHZ)
    station_code = "THE"
    
    try:
        # Λήψη τελευταίων 10 λεπτών
        st = client.get_waveforms("HL", station_code, "", "HHZ", now_utc - 600, now_utc)
        st.detrend('demean')
        # Φίλτρο bandpass για να καθαρίσει το σήμα και να φαίνεται η δόνηση
        st.filter('bandpass', freqmin=0.5, freqmax=5.0)
        data = st[0].data
        times = [(t + 7200).datetime for t in st[0].times("utcdatetime")]
        title_status = "LIVE ΣΤΑΘΜΟΣ: ΘΕΣΣΑΛΟΝΙΚΗ"
    except Exception as e:
        # Αν υπάρξει σφάλμα σύνδεσης
        data = np.zeros(100)
        times = [(now_utc - 600 + i*6 + 7200).datetime for i in range(100)]
        title_status = "ΑΝΑΜΟΝΗ ΣΗΜΑΤΟΣ (STATION OFFLINE)"

    fig, ax = plt.subplots(figsize=(12, 5))
    
    # Σχεδίαση με έντονο κόκκινο χρώμα
    ax.plot(times, data, color='#FF0000', linewidth=0.8)
    
    # Μορφοποίηση άξονα Χ
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
    ax.set_title(f"{title_status}\nΤελευταία ενημέρωση: {greece_time_now.strftime('%H:%M:%S')}")
    ax.grid(True, alpha=0.2, linestyle='--')
    
    # Προσαρμογή ορίων για να φαίνεται η κυματομορφή
    if np.max(np.abs(data)) > 0:
        limit = np.max(np.abs(data)) * 1.1
        ax.set_ylim([-limit, limit])
    
    ax.set_xlim([times[0], times[-1]])

    plt.savefig('seismo_live.png', dpi=100)
    plt.close()

if __name__ == "__main__":
    get_seismo()
