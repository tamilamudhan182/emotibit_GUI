import numpy as np
import pandas as pd
import mne
from scipy.signal import butter, filtfilt, detrend
from scipy.stats import skew, kurtosis

# =========================
# FILE
# =========================
file_path = r"C:\AJU\Internship\Processing\Public Dataset\Subjects\subject_01\BVP.csv"
fs = 64   # Empatica BVP sampling rate

df = pd.read_csv(file_path)
ppg = df.iloc[:, 0].dropna().values.astype(float)

# remove starting zeros if present
ppg = ppg[np.abs(ppg) > 1e-8]

# =========================
# PAPER PREPROCESSING
# Bandpass 0.3–12 Hz, 4th order, zero-phase
# =========================
def bandpass_filter(x, fs, low=0.3, high=12, order=4):
    nyq = fs / 2
    b, a = butter(order, [low / nyq, high / nyq], btype="bandpass")
    return filtfilt(b, a, x)

ppg_filt = bandpass_filter(ppg, fs)
ppg_filt = detrend(ppg_filt)

# =========================
# FRAME SETTINGS
# Paper says equal-length frames
# =========================
frame_sec = 10
frame_len = int(frame_sec * fs)

n_frames = len(ppg_filt) // frame_len
ppg_filt = ppg_filt[:n_frames * frame_len]

frames = ppg_filt.reshape(n_frames, frame_len)

# =========================
# HOS FEATURES
# =========================
features = []

for i, frame in enumerate(frames):
    frame = detrend(frame)

    # time-domain HOS
    td_skew = skew(frame)
    td_kurt = kurtosis(frame, fisher=True)

    # frequency-domain kurtosis
    spectrum = np.abs(np.fft.rfft(frame))
    spectrum = spectrum[1:]   # remove DC
    fd_kurt = kurtosis(spectrum, fisher=True)

    features.append([i, i * frame_sec, td_skew, td_kurt, fd_kurt])

features_df = pd.DataFrame(
    features,
    columns=["Frame", "Start_Time_s", "TD_Skew", "TD_Kurtosis", "FD_Kurtosis"]
)

# =========================
# DECISION RULE
# Paper logic:
# motion-corrupted frames have higher TD skew/kurtosis
# and lower FD kurtosis
# =========================

td_skew_th = features_df["TD_Skew"].quantile(0.80)
td_kurt_th = features_df["TD_Kurtosis"].quantile(0.80)
fd_kurt_th = features_df["FD_Kurtosis"].quantile(0.20)

bad_decisions = []

for _, row in features_df.iterrows():
    d1 = row["TD_Skew"] >= td_skew_th
    d2 = row["TD_Kurtosis"] >= td_kurt_th
    d3 = row["FD_Kurtosis"] <= fd_kurt_th

    # fused decision: majority voting
    bad = (d1 + d2 + d3) >= 2
    bad_decisions.append(bad)

features_df["Bad"] = bad_decisions
features_df["Quality"] = np.where(features_df["Bad"], "BAD", "GOOD")

print(features_df)

# =========================
# RECONSTRUCT GOOD-ONLY SIGNAL
# =========================
good_signal = []

for i, frame in enumerate(frames):
    if not features_df.loc[i, "Bad"]:
        good_signal.extend(frame)

good_signal = np.array(good_signal)

# =========================
# MNE PLOTTING
# =========================
info = mne.create_info(
    ch_names=["Filtered_PPG"],
    sfreq=fs,
    ch_types=["misc"]
)

raw = mne.io.RawArray(ppg_filt.reshape(1, -1), info)

annotations = []

for _, row in features_df.iterrows():
    if row["Bad"]:
        annotations.append(
            mne.Annotations(
                onset=[row["Start_Time_s"]],
                duration=[frame_sec],
                description=["BAD_motion"]
            )
        )

if annotations:
    raw.set_annotations(annotations[0])
    for ann in annotations[1:]:
        raw.set_annotations(raw.annotations + ann)

raw.plot(
    duration=30,
    scalings="auto",
    color={"misc": "black"},
    title="Paper-based HOS Motion Artifact Detection"
)

# =========================
# GOOD-ONLY MNE PLOT
# =========================
info_good = mne.create_info(
    ch_names=["Good_Only_PPG"],
    sfreq=fs,
    ch_types=["misc"]
)

raw_good = mne.io.RawArray(good_signal.reshape(1, -1), info_good)

raw_good.plot(
    duration=30,
    scalings="auto",
    color={"misc": "black"},
    title="Good-only PPG after HOS Detection"
)