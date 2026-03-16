import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from obspy.clients.fdsn import Client
from obspy import UTCDateTime
import sys

def create_status_image(message):
    """Φτιάχνει μια εικόνα με μήνυμα αν κάτι πάει στραβά"""
    plt.figure(figsize=(12, 5))
    plt.text(0.5, 0.5, message, ha='center', va='center', fontsize=12, color='red')
    plt.title("ΣΕΙΣΜΟΓΡΑΦΟΣ - ΚΑΤΑΣΤΑΣΗ")
    plt.savefig('seismo_live.png')
    plt.close()

try:
    # Σύνδεση με τον σέρβερ
    client = Client("IRIS")
    now = UTCDateTime.now()
    
    # Επιλογή σταθμού: HL (Δίκτυο), ASYG (Αθήνα), 00 (Location), BHZ (Κανάλι)
    # Παίρνουμε τα δεδομένα της τελευταίας 1 ώρας
    starttime = now - 3600
    endtime = now

    print(f"Λήψη δεδομένων για τον σταθμό ASYG ({now.strftime('%H:%M:%S')})...")
    
    st = client.get_waveforms("HL", "ASYG", "00", "BHZ", starttime, endtime)
    
    # Δημιουργία γραφήματος
    plt.figure(figsize=(12, 5))
    trace = st[0]
    plt.plot(trace.times("utcdatetime"), trace.data, color='#0047AB', lw=0.7)
    
    # Ρυθμίσεις εμφάνισης
    plt.title(f"ΣΕΙΣΜΟΓΡΑΦΟΣ ΑΘΗΝΑΣ (ASYG) - LIVE\nΕνημέρωση: {now.strftime('%d/%m/%Y %H:%M:%S')} UTC", fontsize=14)
    plt.xlabel("Ώρα (UTC)", fontsize=10)
    plt.ylabel("Ένταση (Counts)", fontsize=10)
    plt.grid(True, linestyle=':', alpha=0.6)
    
    # Αποθήκευση
    plt.tight_layout()
    plt.savefig('seismo_live.png')
    plt.close()
    print("Η εικόνα ανανεώθηκε επιτυχώς!")

except Exception as e:
    error_msg = f"Πρόβλημα σύνδεσης ή έλλειψη δεδομένων:\n{str(e)}"
    print(error_msg)
    create_status_image(error_msg)
