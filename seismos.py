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
    
    # Χρόνος: 4 λεπτά πίσω για σίγουρη λήψη δεδομένων
    end_time = now_utc - 240
    start_time = end_time - 600
    
    try:
        # Λήψη δεδομένων από τον σταθμό JAN (Ιωάννινα)
        st = client.get_waveforms("HL", "JAN", "", "HHZ", start_time, end_time)
        st.detrend('demean')
        st.filter('bandpass', freqmin=0.5, freqmax=10.0)
        data = st[0].data
        times = [(t + 7200).datetime for t in st[0].times("utcdatetime")]
    except:
        # Αν αποτύχει η σύνδεση
        data = np.zeros(100)
        times = [(start_time + 7200 + i*6).datetime for i in range(100)]

    fig, ax = plt.subplots(figsize=(12, 5))
    
    # Σχεδίαση της γραμμής
    ax.plot(times, data, color='red', linewidth=1.1)
    
    # --- ΕΔΩ ΕΙΝΑΙ ΟΙ ΑΛΛΑΓΕΣ ΓΙΑ ΤΟΥΣ ΑΡΙΘΜΟΥΣ ---
    # Εμφανίζουμε τους αριθμούς αριστερά (Counts)
    ax.tick_params(axis='y', labelleft=True, left=True, labelsize=9)
    ax.set_ylabel("ΠΛΑΤΟΣ (COUNTS)", fontsize=10, fontweight='bold')
    
    # --- ΠΡΟΣΘΗΚΗ P, S, L (Δείγματα) ---
    # Τα τοποθετούμε στο 20%, 50% και 80% του γραφήματος για να τα βλέπεις
    mid_idx_p = int(len(times) * 0.2)
    mid_idx_s = int(len(times) * 0.5)
    mid_idx_l = int(len(times) * 0.8)
    
    # Το limit βοηθάει να τα βάλουμε λίγο πιο πάνω από τη γραμμή
    limit = max(np.max(np.abs(data)) * 1.1, 400)
    
    ax.text(times[mid_idx_p], limit*0.7, 'P', color='black', fontsize=12, fontweight='bold', ha='center', bbox=dict(facecolor='white', alpha=0.5, edgecolor='none'))
    ax.text(times[mid_idx_s], limit*0.7, 'S', color='black', fontsize=12, fontweight='bold', ha='center', bbox=dict(facecolor='white', alpha=0.5, edgecolor='none'))
    ax.text(times[mid_idx_l], limit*0.7, 'L', color='black', fontsize=12, fontweight='bold', ha='center', bbox=dict(facecolor='white', alpha=0.5, edgecolor='none'))

    # Μορφοποίηση ώρας στον άξονα Χ
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
    
    # Τίτλος
    ax.set_title("Ο ΣΕΙΣΜΟΓΡΑΦΟΣ ΤΟΥ ΓΗΛΟΦΟΥ (Δίκτυο HL)\nΔεδομένα από σταθμό Ιωαννίνων", 
              fontsize=13, fontweight='bold', pad=15)
    
    # Επεξήγηση κάτω
    current_update = (now_utc + 7200).strftime('%H:%M:%S')
    plt.figtext(0.5, 0.02, 
                f"ΚΑΤΑΓΡΑΦΗ ΕΔΑΦΙΚΗΣ ΚΙΝΗΣΗΣ (ΣΕ ΠΡΑΓΜΑΤΙΚΟ ΧΡΟΝΟ)\nΕνημέρωση: {current_update} | Τα δεδομένα αφορούν την τοπική δόνηση του εδάφους.", 
                ha="center", fontsize=9, color="#333333", style='italic', 
                bbox=dict(facecolor='#fefefe', alpha=0.9, edgecolor='#cccccc', boxstyle='round,pad=0.5'))

    ax.grid(True, alpha=0.2, linestyle='--')
    
    # Σταθεροποίηση κλίμακας
    ax.set_ylim([-limit, limit])
    ax.set_xlim([times[0], times[-1]])
    
    plt.tight_layout(rect=[0, 0.08, 1, 0.95])
    plt.savefig('seismo_live.png', dpi=100)
    plt.close()

if __name__ == "__main__":
    get_seismo()
