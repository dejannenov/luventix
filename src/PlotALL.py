import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import mplcursors

#Parameters
input_file = "Aligned_SIBO_Test_Set.tsv"
metadata_cols = 1  # number of metadata columns before features

# === Load Data ===
df = pd.read_csv(input_file, sep='\t')
features_df = df.iloc[:, metadata_cols:]
features_df.columns = features_df.columns.str.strip()
features_df.columns = features_df.columns.astype(int)

#Plot
plt.figure(figsize=(14, 7))
lines = []

for idx, row in df.iterrows():
    sample_id = row['sampleID']
    intensities = pd.to_numeric(features_df.iloc[idx], errors='coerce')
    
    line, = plt.plot(
        features_df.columns,
        intensities,
        label=sample_id,
        linewidth=1
    )
    line.set_gid(sample_id)
    lines.append(line)

plt.xlabel("Scan Index")
plt.ylabel("Intensity")
plt.title("Plot Samples")
#plt.legend(fontsize='small', ncol=3)
plt.grid(True)
plt.tight_layout()

#Interactive tooltip on hover
cursor = mplcursors.cursor(lines, hover=True)

@cursor.connect("add")
def on_add(sel):
    x, y = sel.target
    sample_name = sel.artist.get_gid()
    sel.annotation.set_text(f"{sample_name}\nScan: {int(x)}\nIntensity: {y:.2f}")
    sel.annotation.get_bbox_patch().set(alpha=0.9)

plt.show()
