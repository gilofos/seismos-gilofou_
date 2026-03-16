import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from obspy.clients.fdsn import Client
from obspy import UTCDateTime

# Χρησιμοποιούμε τον σέρβερ IRIS (πολύ σταθερός)
client = Client("IRIS")

try:
    now = UTCDateTime.now()
    # Σταθμός στην Αθήνα (National Observatory of Athens)
    # Δίκτυο: HL, Σταθμός: ATMON (Πεντέλη)
    st = client.get_waveforms("HL", "ATMON", "", "HHZ", now - 600, now)
    
    st.detrend('demean')
    st.filter('bandpass', freqmin=0.5, freqmax=5.0)
    
    plt.figure(figsize=(12, 5))
    times = st[0].times("utcdatetime")
    # Μετατροπή σε ώρα Ελλάδος (+2 ώρες)
    plt.plot([(t + 7200).datetime for t in times], st[0].data, color='blue', linewidth=0.5)
    
    plt.title(f"ΣΕΙΣΜΟΓΡΑΦΟΣ ΓΗΛΟΦΟΥ (Σταθμός Πεντέλης) - LIVE\n{(now + 7200).strftime('%d/%m/%Y %H:%M:%S')}")
    plt.xlabel("Ώρα Ελλάδος")
    plt.ylabel("Ένταση")
    plt.grid(True, alpha=0.2)
    plt.tight_layout()
    
    plt.savefig('seismo_live.png')
    print("Η εικόνα δημιουργήθηκε επιτυχώς!")

except Exception as e:
    print(f"Σφάλμα: {e}")
