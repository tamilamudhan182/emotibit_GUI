import pandas as pd
import numpy as np
import mne

# =========================
# Load EDA file
# =========================
file_path = r"C:\AJU\Internship\Processing\Public Dataset\Subjects\subject_01\EDA.csv"

df = pd.read_csv(file_path)

eda = df["0"].astype(float).values

# Change if your EDA sampling rate is different
fs = 64

# =========================
# Paper thresholds
# =========================
EDA_THRESHOLD = 0.05      # µS
RAC_THRESHOLD = 0.2       # 20%
RAC_WINDOW_SEC = 2

rac_window = int(RAC_WINDOW_SEC * fs)

# =========================
# EDA threshold check
# =========================
eda_threshold_good = eda >= EDA_THRESHOLD

# =========================
# RAC check
# =========================
rac_good = np.ones(len(eda), dtype=bool)

for start in range(0, len(eda), rac_window):
    end = min(start + rac_window, len(eda))
    segment = eda[start:end]

    if len(segment) < 2:
        continue

    max_idx = np.argmax(segment)
    min_idx = np.argmin(segment)

    max_val = segment[max_idx]
    min_val = segment[min_idx]

    if max_idx < min_idx:
        first_val = max_val
    else:
        first_val = min_val

    if first_val == 0:
        rac = np.inf
    else:
        rac = abs(max_val - min_val) / abs(first_val)

    if rac >= RAC_THRESHOLD:
        rac_good[start:end] = False

# =========================
# Final good/bad labels
# =========================
good = eda_threshold_good & rac_good
bad = ~good

print("Total samples:", len(eda))
print("Good samples:", np.sum(good))
print("Bad samples:", np.sum(bad))
print("EDA quality score:", np.mean(good))

# =========================
# Function to create MNE Raw
# =========================
def create_mne_raw(signal, fs, ch_name):
    info = mne.create_info(
        ch_names=[ch_name],
        sfreq=fs,
        ch_types=["misc"]
    )

    raw = mne.io.RawArray(
        signal.reshape(1, -1),
        info
    )

    return raw

# =========================
# 1. MNE plot: Raw EDA signal
# =========================
raw_eda = create_mne_raw(eda, fs, "Raw_EDA")

raw_eda.plot(
    duration=60,
    scalings={"misc": "auto"},
    color={"misc": "black"},
    title="Raw EDA Signal",
    block=True
)

# =========================
# 2. MNE plot: Raw EDA with bad labelled
# =========================
raw_bad_labelled = create_mne_raw(eda, fs, "EDA_bad_labelled")

annotations = []

in_bad = False
bad_start = 0

for i in range(len(bad)):
    if bad[i] and not in_bad:
        bad_start = i
        in_bad = True

    if in_bad and ((not bad[i]) or i == len(bad) - 1):
        bad_end = i
        onset = bad_start / fs
        duration = (bad_end - bad_start) / fs

        annotations.append(
            mne.Annotations(
                onset=[onset],
                duration=[duration],
                description=["BAD_EDA"]
            )
        )

        in_bad = False

if len(annotations) > 0:
    final_annotations = annotations[0]
    for ann in annotations[1:]:
        final_annotations += ann

    raw_bad_labelled.set_annotations(final_annotations)

raw_bad_labelled.plot(
    duration=60,
    scalings={"misc": "auto"},
    color={"misc": "black"},
    title="EDA Signal with Bad Segments Labelled",
    block=True
)

# =========================
# 3. MNE plot: Only good EDA signal
# Bad signal completely removed
# =========================
eda_good_only = eda[good]

raw_good_only = create_mne_raw(eda_good_only, fs, "Good_EDA_only")

raw_good_only.plot(
    duration=60,
    scalings={"misc": "auto"},
    color={"misc": "green"},
    title="Only Good EDA Signal - Bad Signal Removed",
    block=True
)