import matplotlib
matplotlib.use('Agg') 
import matplotlib.pyplot as plt
from obspy.clients.fdsn import Client
from obspy import UTCDateTime
import time

# Σύνδεση με το παγκόσμιο δίκτυο
client = Client("EARTHSCOPE") 

print("Ο ΣΕΙΣΜΟΓΡΑΦΟΣ ΓΗΛΟΦΟΥ ΞΕΚΙΝΗΣΕ (ΕΠΑΓΓΕΛΜΑΤΙΚΗ ΕΚΔΟΣΗ)...")

while True:
    try:
        # Παίρνουμε την ώρα (UTC για το σύστημα, θα τη μετατρέψουμε στο γράφημα)
        now = UTCDateTime.now()
        
        # Λήψη δεδομένων (Σταθμός ANTO - Άγκυρα, πολύ σταθερός για την περιοχή μας)
        st = client.get_waveforms("IU", "ANTO", "00", "BHZ", now - 600, now)
        
        # --- ΕΠΕΞΕΡΓΑΣΙΑ ΣΗΜΑΤΟΣ ---
        st.detrend('demean') # Φέρνει τη γραμμή στο ΜΗΔΕΝ (κεντράρισμα)
        st.filter('bandpass', freqmin=0.5, freqmax=5.0) # Καθαρίζει τον θόρυβο
        
        # --- ΣΧΕΔΙΑΣΗ ---
        plt.close('all')
        fig, ax = plt.subplots(figsize=(12, 5))
        
        # Μετατροπή των δευτερολέπτων σε πραγματική ώρα Ελλάδος
        # Προσθέτουμε 2 ώρες (ή 3 ανάλογα την εποχή) για ώρα Ελλάδος
        times = st[0].times("utcdatetime") 
        times_greek = [(t + 7200).datetime for t in times] # +2 ώρες
        
        ax.plot(times_greek, st[0].data, color='red', linewidth=1)
        
        ax.set_title(f"LIVE ΣΕΙΣΜΟΓΡΑΦΟΣ ΓΗΛΟΦΟΥ\nΤελευταία ενημέρωση: {(now + 7200).strftime('%H:%M:%S')}", fontsize=14)
        ax.set_ylabel("Ένταση (Counts)")
        ax.set_xlabel("Ώρα Ελλάδος")
        ax.grid(True, alpha=0.3)
        
        # Αποθήκευση
        plt.savefig('seismo_live.png')
        plt.close(fig)
        
        print(f"ΕΠΙΤΥΧΙΑ! Το γράφημα ενημερώθηκε στις: {(now + 7200).strftime('%H:%M:%S')}")
        time.sleep(300) 
        
    except Exception as e:
        print(f"Αναμονή... ({e})")
        time.sleep(60)