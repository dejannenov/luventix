import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from fastdtw import fastdtw
from scipy.interpolate import interp1d

#Parameters
input_file = "SIBO_Test_Set.tsv"
output_file = "Aligned_SIBO_Test_Set.tsv"
metadata_cols = 3
sample_ids_to_plot = ['sibo-uk-6', 'uk-0001-00360','uk-0001-00834']  #sample IDs - the first one is the reference
intensity_threshold = 0  # minimum intensity to keep

# Anchor peaks scan numbers for the reference
ref_peak1_scan = 9949
ref_peak2_scan = 32429

# Anchor peaks scan numbers in targets: map sampleID -> (peak1_scan, peak2_scan)
target_anchor_peaks = {
    'uk-0001-00360': (10168, 32856),
    'uk-0001-00834': (10040, 32603)
}


#LOAD DATA
df = pd.read_csv(input_file, sep='\t', low_memory=False)
features_df = df.iloc[:, metadata_cols:].copy()
features_df.columns = features_df.columns.astype(int)
scan_axis = features_df.columns.values

#EXTRACT SIGNALS
sample_signals = {}
for sample_id in sample_ids_to_plot:
    row = df[df['sampleID'] == sample_id]
    if row.empty:
        print(f"Sample '{sample_id}' not found")
        continue
    signal = pd.to_numeric(features_df.loc[row.index[0]], errors='coerce').fillna(0).to_numpy()
    signal = np.ravel(signal).astype(float)
    sample_signals[sample_id] = signal

#REFERENCE SIGNAL
ref_id = sample_ids_to_plot[0]
ref_signal = sample_signals[ref_id]


def variable_shift_signal(signal, ref_peaks, tgt_peaks):

    scan_indices = np.arange(len(signal))
    ref_peaks = np.array(ref_peaks)
    tgt_peaks = np.array(tgt_peaks)

    shift_function = interp1d(tgt_peaks, ref_peaks - tgt_peaks,
                              kind='linear', fill_value='extrapolate')
    variable_shifts = shift_function(scan_indices)

    f = interp1d(scan_indices, signal, kind='linear', bounds_error=False, fill_value=0)
    shifted_signal = f(scan_indices - variable_shifts)
    return shifted_signal

aligned_signals = {ref_id: ref_signal}

for sample_id, signal in sample_signals.items():
    if sample_id == ref_id:
        continue

    if sample_id not in target_anchor_peaks:
        print(f"No anchor peak info for '{sample_id}', skipping pre-shift")
        aligned_signals[sample_id] = signal
        continue

    tgt_peak1, tgt_peak2 = target_anchor_peaks[sample_id]

    print(f"Pre-shifting '{sample_id}' using variable shift based on anchor peaks")

    shifted_signal = variable_shift_signal(signal,
                                           ref_peaks=[ref_peak1_scan, ref_peak2_scan],
                                           tgt_peaks=[tgt_peak1, tgt_peak2])
    aligned_signals[sample_id] = shifted_signal

def align_with_dtw(ref, target):
    ref = np.ravel(ref).astype(float)
    target = np.ravel(target).astype(float)
    assert ref.ndim == 1, f"ref ndim={ref.ndim}"
    assert target.ndim == 1, f"target ndim={target.ndim}"

    def scalar_distance(a, b):
        return abs(a - b)

    distance, path = fastdtw(ref, target, dist=scalar_distance)
    ref_indices, target_indices = zip(*path)
    interp_func = interp1d(target_indices, target[np.array(target_indices)],
                           kind='linear', bounds_error=False, fill_value=0)
    aligned_target = interp_func(np.arange(len(ref)))
    return aligned_target

for sample_id, signal in aligned_signals.items():
    if sample_id == ref_id:
        continue
    print(f"DTW aligning '{sample_id}' with reference...")
    aligned = align_with_dtw(ref_signal, signal)
    aligned_signals[sample_id] = aligned


for sample_id in aligned_signals:
    aligned_signals[sample_id] = np.where(aligned_signals[sample_id] >= intensity_threshold,
                                          aligned_signals[sample_id], 0)


output_rows = []
for sample_id in sample_ids_to_plot:
    if sample_id not in aligned_signals:
        continue
    row = [sample_id] + list(aligned_signals[sample_id])
    output_rows.append(row)

output_df = pd.DataFrame(output_rows)
output_df.columns = ['sampleID'] + list(scan_axis[:len(ref_signal)])
output_df.to_csv(output_file, sep='\t', index=False)
print(f"Aligned matrix exported to: {output_file}")


plt.figure(figsize=(14, 7))
for sample_id in sample_ids_to_plot:
    if sample_id not in aligned_signals:
        continue
    plt.plot(scan_axis[:len(aligned_signals[sample_id])], aligned_signals[sample_id], label=sample_id)
plt.xlabel("Scan Number")
plt.ylabel("Intensity")
plt.title("FastDTW Aligned Samples")
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.show()
