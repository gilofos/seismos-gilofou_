import matplotlib.pyplot as plt
from obspy.clients.fdsn import Client
from obspy import UTCDateTime
import matplotlib
matplotlib.use('Agg')

def get_seismo():
    client = Client("NOA")
    # Παίρνουμε την ώρα τώρα και προσθέτουμε 2 ώρες για Ελλάδα
    now_utc = UTCDateTime.now()
    last_time = (now_utc + 7200).strftime('%H:%M:%S')
    
    try:
        # Δοκιμή για δεδομένα από Λιτόχωρο
        st = client.get_waveforms("HL", "LIT", "", "HHZ", now_utc - 600, now_utc - 30)
        st.detrend('demean')
        st.filter('bandpass', freqmin=1.0, freqmax=10.0)
        data = st[0].data
        times = [(t + 7200).datetime for t in st[0].times("utcdatetime")]
        title_status = "LIVE ΣΤΑΘΜΟΣ: ΛΙΤΟΧΩΡΟ"
    except Exception as e:
        # Αν αποτύχει ο σταθμός, δείξε κενή γραμμή αλλά με τη ΣΩΣΤΗ ΩΡΑ
        data = [0] * 100
        times = [now_utc.datetime] * 100
        title_status = "ΑΝΑΜΟΝΗ ΔΕΔΟΜΕΝΩΝ"

    fig, ax = plt.subplots(figsize=(12, 5))
    ax.plot(times, data, color='red', linewidth=0.8)
    
    # Εδώ θα φανεί αν το σύστημα δουλεύει
    ax.set_title(f"{title_status}\nΤελευταία ενημέρωση: {last_time}")
    ax.grid(True, alpha=0.3)
    
    plt.savefig('seismo_live.png', dpi=100)
    plt.close()
    print(f"Update Success: {last_time}")

if __name__ == "__main__":
    get_seismo()
