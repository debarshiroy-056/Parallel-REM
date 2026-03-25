import os
import numpy as np
import pandas as pd

# ==========================================
# CONFIGURATION
# ==========================================
N_SAMPLES = 200
N_SPECIES = 50
SPARSITY = 0.80  # 80% of the data will be zeros
STUDY_NAMES = ["Study_A", "Study_B", "Study_C", "Study_D"]

output_dir = "example_data"
os.makedirs(output_dir, exist_ok=True)

print(f"Generating synthetic microbiome dataset...")
print(f"Samples: {N_SAMPLES}, Species: {N_SPECIES}, Sparsity: {SPARSITY*100}%")

# ==========================================
# 1. GENERATE METADATA
# ==========================================
# Create sample IDs (e.g., Sample_001, Sample_002)
sample_ids = [f"Sample_{str(i).zfill(3)}" for i in range(1, N_SAMPLES + 1)]

# Randomly assign each sample to a study
np.random.seed(42) # For reproducibility
studies = np.random.choice(STUDY_NAMES, size=N_SAMPLES)

df_meta = pd.DataFrame({"study_name": studies}, index=sample_ids)

# ==========================================
# 2. GENERATE ABUNDANCE MATRIX
# ==========================================
# Microbiome data usually follows a skewed distribution (e.g., exponential)
abundance_values = np.random.exponential(scale=2.0, size=(N_SAMPLES, N_SPECIES))

# Apply the Sparsity Mask (inject zeros to mimic real biological drop-out)
zero_mask = np.random.rand(N_SAMPLES, N_SPECIES) < SPARSITY
abundance_values[zero_mask] = 0.0

# Create species names (e.g., sp_01, sp_02)
species_ids = [f"sp_{str(i).zfill(2)}" for i in range(1, N_SPECIES + 1)]

df_abundance = pd.DataFrame(abundance_values, index=sample_ids, columns=species_ids)

# Inject a fake strong correlation between sp_01 and sp_02 so the pipeline finds at least one valid edge
mask_cooccur = (~zero_mask[:, 0]) & (~zero_mask[:, 1])
df_abundance.loc[mask_cooccur, "sp_02"] = df_abundance.loc[mask_cooccur, "sp_01"] * 1.5 + np.random.normal(0, 0.1, size=mask_cooccur.sum())

# ==========================================
# 3. SAVE TO CSV
# ==========================================
abund_path = os.path.join(output_dir, "dummy_abundance.csv")
meta_path = os.path.join(output_dir, "dummy_metadata.csv")

df_abundance.to_csv(abund_path)
df_meta.to_csv(meta_path)

print(f"[✔] Saved abundance matrix to: {abund_path}")
print(f"[✔] Saved metadata to: {meta_path}")
print("Ready for testing!")
