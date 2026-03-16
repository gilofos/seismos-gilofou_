import matplotlib
matplotlib.use('Agg') 
import matplotlib.pyplot as plt
from obspy.clients.fdsn import Client
from obspy import UTCDateTime
import os

# Σύνδεση με το παγκόσμιο δίκτυο
client = Client("EARTHSCOPE") 

print("Ο ΣΕΙΣΜΟΓΡΑΦΟΣ ΓΗΛΟΦΟΥ ΞΕΚΙΝΗΣΕ...")

try:
    # Παίρνουμε την ώρα
    now = UTCDateTime.now()
    
    # Λήψη δεδομένων (Σταθμός ANTO - Άγκυρα)
    # Παίρνουμε τα τελευταία 10 λεπτά (600 δευτερόλεπτα)
    st = client.get_waveforms("IU", "ANTO", "00", "BHZ", now - 600, now)
    
    # --- ΕΠΕΞΕΡΓΑΣΙΑ ΣΗΜΑΤΟΣ ---
    st.detrend('demean') # Κεντράρισμα
    st.filter('bandpass', freqmin=0.5, freqmax=5.0) # Καθαρισμός θορύβου
    
    # --- ΣΧΕΔΙΑΣΗ ---
    plt.close('all')
    fig, ax = plt.subplots(figsize=(12, 5))
    
    # Μετατροπή σε ώρα Ελλάδος (+2 ώρες)
    times = st[0].times("utcdatetime") 
    times_greek = [(t + 7200).datetime for t in times] 
    
    ax.plot(times_greek, st[0].data, color='red', linewidth=1)
    
    ax.set_title(f"LIVE ΣΕΙΣΜΟΓΡΑΦΟΣ ΓΗΛΟΦΟΥ\nΤελευταία ενημέρωση: {(now + 7200).strftime('%H:%M:%S')}", fontsize=14)
    ax.set_ylabel("Ένταση (Counts)")
    ax.set_xlabel("Ώρα Ελλάδος")
    ax.grid(True, alpha=0.3)
    
    # Αποθήκευση
    plt.savefig('seismo_live.png')
    plt.close(fig)
    
    print(f"ΕΠΙΤΥΧΙΑ! Το γράφημα ενημερώθηκε στις: {(now + 7200).strftime('%H:%M:%S')}")

except Exception as e:
    print(f"Σφάλμα: {e}")
    # Δημιουργία εικόνας σφάλματος για να μη σταματάει το Action
    plt.figure(figsize=(10, 4))
    plt.text(0.5, 0.5, f"Αναμονή για δεδομένα...\n({e})", ha='center', va='center')
    plt.savefig('seismo_live.png')
