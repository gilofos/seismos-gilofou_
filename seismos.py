import matplotlib
matplotlib.use('Agg') 
import matplotlib.pyplot as plt
from obspy.clients.fdsn import Client
from obspy import UTCDateTime
import os

# Χρησιμοποιούμε έναν πιο γρήγορο σέρβερ (GFZ - Γερμανία)
client = Client("GFZ") 

try:
    now = UTCDateTime.now()
    # Παίρνουμε δεδομένα από σταθμό στην Ελλάδα (Athens - AT)
    # Ζητάμε μόνο 5 λεπτά (300 δευτερόλεπτα) για να είναι γρήγορο
    st = client.get_waveforms("GE", "SANT", "", "BHZ", now - 300, now)
    
    st.detrend('demean')
    st.filter('bandpass', freqmin=0.5, freqmax=5.0)
    
    plt.figure(figsize=(10, 4))
    times = st[0].times("utcdatetime")
    # Μετατροπή σε ώρα Ελλάδος (+2 ώρες)
    plt.plot([(t + 7200).datetime for t in times], st[0].data, color='red')
    
    plt.title(f"ΣΕΙΣΜΟΓΡΑΦΟΣ ΓΗΛΟΦΟΥ - LIVE\n{(now + 7200).strftime('%d/%m/%Y %H:%M:%S')}")
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    
    # Αποθήκευση
    plt.savefig('seismo_live.png')
    print("Η εικόνα δημιουργήθηκε επιτυχώς!")

except Exception as e:
    print(f"Σφάλμα: {e}")
