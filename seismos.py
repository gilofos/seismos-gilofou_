import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from obspy.clients.fdsn import Client
from obspy import UTCDateTime
import os

def create_error_image(msg):
    plt.figure(figsize=(10, 4))
    plt.text(0.5, 0.5, f"Αναμονή για δεδομένα...\n({msg})", ha='center', va='center')
    plt.savefig('seismo_live.png')
    print("Δημιουργήθηκε εικόνα αναμονής.")

try:
    client = Client("IRIS")
    now = UTCDateTime.now()
    # Δοκιμάζουμε έναν πολύ σταθερό σταθμό στην Ισλανδία (BORG) που λειτουργεί πάντα
    st = client.get_waveforms("IU", "BORG", "00", "LHZ", now - 3600, now)
    
    plt.figure(figsize=(12, 5))
    plt.plot(st[0].times("utcdatetime"), st[0].data, color='red', lw=0.5)
    plt.title(f"ΣΕΙΣΜΟΓΡΑΦΟΣ - LIVE\nUTC: {now.strftime('%Y-%m-%d %H:%M:%S')}")
    plt.grid(True, alpha=0.3)
    plt.savefig('seismo_live.png')
    print("Η εικόνα δημιουργήθηκε επιτυχώς!")

except Exception as e:
    print(f"Σφάλμα: {e}")
    create_error_image(str(e))
