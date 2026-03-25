import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import find_peaks
from scipy.interpolate import interp1d
from scipy.signal import find_peaks


#Parameters
input_file = "SIBO_Test_Set.tsv"
metadata_cols = 3  # number of metadata columns before scan intensities
sample_id_to_plot = 'sibo-uk-6'  # specify sample ID


#Load Data
df = pd.read_csv(input_file, sep='\t')
features_df = df.iloc[:, metadata_cols:].copy()
features_df.columns = features_df.columns.astype(int)
scan_axis = features_df.columns.values


#Extract Raw Signal
row = df[df['sampleID'] == sample_id_to_plot]
if row.empty:
    print(f"Sample '{sample_id_to_plot}' not found")
signal = pd.to_numeric(features_df.loc[row.index[0]], errors='coerce').fillna(0)
ref_signal = signal.values


plt.figure(figsize=(16, 6))
plt.plot(scan_axis, ref_signal, label=sample_id_to_plot, lw=1)
plt.xlabel("Scan Number")
plt.ylabel("Intensity")
plt.title(f"Reference Sample: {sample_id_to_plot}")
plt.grid(True)
plt.legend()


peaks, _ = find_peaks(ref_signal, height=np.max(ref_signal) * 0.08, distance=50)
plt.plot(scan_axis[peaks], ref_signal[peaks], "rx", label="Detected Peaks")
for p in peaks:
    plt.annotate(str(scan_axis[p]), (scan_axis[p], ref_signal[p]), textcoords="offset points", xytext=(0,10), ha='center', fontsize=8)

plt.tight_layout()
plt.show()