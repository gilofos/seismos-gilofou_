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
    
    # 4 λεπτά καθυστέρηση για σίγουρη ροή
    end_time = now_utc - 240
    start_time = end_time - 600
    
    # Πρώτος σταθμός τα Ιωάννινα (JAN)
    test_stations = [
        {"id": "JAN", "loc": "ΙΩΑΝΝΙΝΑ"},
        {"id": "THE", "loc": "ΘΕΣΣΑΛΟΝΙΚΗ"},
        {"id": "LIT", "loc": "ΛΙΤΟΧΩΡΟ"}
    ]
    
    data = None
    active_name = ""

    for st_info in test_stations:
        try:
            st = client.get_waveforms("HL", st_info['id'], "", "HHZ", start_time, end_time)
            st.detrend('demean')
            st.filter('bandpass', freqmin=0.5, freqmax=10.0)
            data = st[0].data
            times = [(t + 7200).datetime for t in st[0].times("utcdatetime")]
            active_name = st_info['loc']
            break 
        except:
            continue

    if data is None:
        data = np.zeros(100)
        times = [(start_time + 7200 + i*6).datetime for i in range(100)]
        active_name = "OFFLINE"

    fig, ax = plt.subplots(figsize=(12, 5))
    ax.plot(times, data, color='red', linewidth=0.7)
    
    current_update = (now_utc + 7200).strftime('%H:%M:%S')
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
    ax.set_title(f"ΣΤΑΘΜΟΣ: {active_name} | ΕΝΗΜΕΡΩΣΗ: {current_update}")
    ax.grid(True, alpha=0.3)
    
    limit = max(np.max(np.abs(data)) * 1.1, 300)
    ax.set_ylim([-limit, limit])
    ax.set_xlim([times[0], times[-1]])
    
    plt.tight_layout()
    plt.savefig('seismo_live.png', dpi=100)
    plt.close()

if __name__ == "__main__":
    get_seismo()
