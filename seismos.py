import matplotlib.pyplot as plt
from obspy.clients.fdsn import Client
from obspy import UTCDateTime
import matplotlib.dates as mdates
import matplotlib
matplotlib.use('Agg')

def get_seismo():
    client = Client("NOA")
    now_utc = UTCDateTime.now()
    last_time = (now_utc + 7200).strftime('%H:%M:%S')
    
    # Ορίζουμε το παράθυρο χρόνου (τελευταία 10 λεπτά)
    start_time = now_utc - 600
    end_time = now_utc
    
    try:
        # Δοκιμή λήψης (HL.LIT..HHZ)
        st = client.get_waveforms("HL", "LIT", "", "HHZ", start_time, end_time)
        data = st[0].data
        times = [(t + 7200).datetime for t in st[0].times("utcdatetime")]
        title_status = "LIVE ΣΤΑΘΜΟΣ: ΛΙΤΟΧΩΡΟ"
    except:
        # Αν αποτύχει, φτιάχνουμε μια ευθεία γραμμή για το "Τώρα"
        data = [0] * 100
        times = [(start_time + 7200 + i*6).datetime for i in range(100)]
        title_status = "ΣΤΑΘΜΟΣ ΕΚΤΟΣ ΣΥΝΔΕΣΗΣ (ΑΝΑΜΟΝΗ)"

    fig, ax = plt.subplots(figsize=(12, 5))
    ax.plot(times, data, color='red', linewidth=1)
    
    # Ρύθμιση του άξονα Χ για να δείχνει μόνο την ώρα
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
    
    ax.set_title(f"{title_status}\nΤελευταία ενημέρωση: {last_time}")
    ax.grid(True, alpha=0.3)
    
    # Περιορίζουμε τον άξονα Χ στα όρια που θέλουμε
    ax.set_xlim([times[0], times[-1]])
    
    plt.savefig('seismo_live.png', dpi=100)
    plt.close()

if __name__ == "__main__":
    get_seismo()
