import sys
import json
import numpy as np
import importlib.resources
from scipy.signal import butter, filtfilt, detrend
from scipy.stats import skew, kurtosis

# Monkeypatch importlib.resources.files to fix the nolds datasets path checking bug on Python 3.11+
orig_files = importlib.resources.files
def patched_files(package):
    if package == "nolds.datasets":
        return orig_files("nolds")
    return orig_files(package)
importlib.resources.files = patched_files

# Try-except block to handle vital_sqi imports gracefully
try:
    from vital_sqi.sqi.standard_sqi import kurtosis_sqi, skewness_sqi
    VITAL_SQI_AVAILABLE = True
except Exception as e:
    VITAL_SQI_AVAILABLE = False
    IMPORT_ERROR = str(e)

# ==========================================================
# ROLLING HISTORY FOR DYNAMIC QUANTILE THRESHOLDS
# ==========================================================
class RollingHistory:
    def __init__(self, max_size=500):
        self.max_size = max_size
        self.td_skew = []
        self.td_kurt = []
        self.fd_kurt = []

    def append(self, skew_val, kurt_val, fd_kurt_val):
        if np.isnan(skew_val) or np.isinf(skew_val):
            return
        if np.isnan(kurt_val) or np.isinf(kurt_val):
            return
        if np.isnan(fd_kurt_val) or np.isinf(fd_kurt_val):
            return

        self.td_skew.append(skew_val)
        self.td_kurt.append(kurt_val)
        self.fd_kurt.append(fd_kurt_val)

        if len(self.td_skew) > self.max_size:
            self.td_skew.pop(0)
            self.td_kurt.pop(0)
            self.fd_kurt.pop(0)

    def get_thresholds(self):
        # Fallbacks when history is small (less than 30 points)
        if len(self.td_skew) < 30:
            return 1.0, 3.0, 1.5

        # Calculate percentiles dynamically:
        # TD skewness: 80th percentile
        # TD kurtosis: 80th percentile
        # FD kurtosis: 20th percentile
        td_skew_th = np.percentile(self.td_skew, 80)
        td_kurt_th = np.percentile(self.td_kurt, 80)
        fd_kurt_th = np.percentile(self.fd_kurt, 20)

        return td_skew_th, td_kurt_th, fd_kurt_th

# Instantiate histories for the three PPG channels (IR, Red, Green)
# Keep separate histories for overall window (300 samples) and local segments (50 samples)
histories = {
    "ppg_ir": {
        "overall": RollingHistory(),
        "segments": RollingHistory()
    },
    "ppg_red": {
        "overall": RollingHistory(),
        "segments": RollingHistory()
    },
    "ppg_green": {
        "overall": RollingHistory(),
        "segments": RollingHistory()
    }
}

# ==========================================================
# PREPROCESSING & QUALITY CHECK FUNCTIONS
# ==========================================================
def bandpass_filter(x, fs, low=0.3, high=12.0, order=4):
    nyq = fs / 2
    b, a = butter(order, [low / nyq, high / nyq], btype="bandpass")
    return filtfilt(b, a, x)

def process_ppg_channel(signal_raw, fs, history_dict):
    if len(signal_raw) == 0:
        return {
            "overall": {"status": "N/A", "kurtosis": 0.0, "skewness": 0.0},
            "segments": ["N/A"] * 6
        }

    std_val = np.std(signal_raw)
    if std_val < 0.01:
        # Flatline / disconnected lead
        return {
            "overall": {"status": "Poor", "kurtosis": 0.0, "skewness": 0.0},
            "segments": ["Poor"] * 6
        }

    # 1. Preprocessing: Bandpass and Detrend
    try:
        filtered = bandpass_filter(signal_raw, fs, low=0.3, high=12.0)
        filtered = detrend(filtered)
    except Exception:
        filtered = detrend(signal_raw)

    # 2. Compute overall metrics
    overall_td_skew = float(skew(filtered))
    overall_td_kurt = float(kurtosis(filtered, fisher=True))

    overall_spec = np.abs(np.fft.rfft(filtered))
    if len(overall_spec) > 1:
        overall_spec = overall_spec[1:]  # remove DC
        overall_fd_kurt = float(kurtosis(overall_spec, fisher=True))
    else:
        overall_fd_kurt = 0.0

    # Log and fetch overall thresholds
    history_dict["overall"].append(overall_td_skew, overall_td_kurt, overall_fd_kurt)
    ov_skew_th, ov_kurt_th, ov_fd_kurt_th = history_dict["overall"].get_thresholds()

    # Overall decision rule (majority voting)
    d1 = overall_td_skew >= ov_skew_th
    d2 = overall_td_kurt >= ov_kurt_th
    d3 = overall_fd_kurt <= ov_fd_kurt_th

    ov_votes = int(d1) + int(d2) + int(d3)
    if ov_votes >= 2:
        overall_status = "Poor"
    elif ov_votes == 1:
        overall_status = "Fair"
    else:
        overall_status = "Good"

    # 3. Process segments (6 segments of 50 samples each)
    segments_status = []
    for i in range(6):
        segment = filtered[i * 50 : (i + 1) * 50]
        if len(segment) < 2:
            segments_status.append("N/A")
            continue

        seg_std = np.std(segment)
        if seg_std < 0.01:
            segments_status.append("Poor")
            continue

        segment = detrend(segment)
        seg_td_skew = float(skew(segment))
        seg_td_kurt = float(kurtosis(segment, fisher=True))

        seg_spec = np.abs(np.fft.rfft(segment))
        if len(seg_spec) > 1:
            seg_spec = seg_spec[1:]  # remove DC
            seg_fd_kurt = float(kurtosis(seg_spec, fisher=True))
        else:
            seg_fd_kurt = 0.0

        # Log and fetch segment thresholds
        history_dict["segments"].append(seg_td_skew, seg_td_kurt, seg_fd_kurt)
        seg_skew_th, seg_kurt_th, seg_fd_kurt_th = history_dict["segments"].get_thresholds()

        sd1 = seg_td_skew >= seg_skew_th
        sd2 = seg_td_kurt >= seg_kurt_th
        sd3 = seg_fd_kurt <= seg_fd_kurt_th

        seg_votes = int(sd1) + int(sd2) + int(sd3)
        if seg_votes >= 2:
            seg_status = "Poor"
        elif seg_votes == 1:
            seg_status = "Fair"
        else:
            seg_status = "Good"
        segments_status.append(seg_status)

    return {
        "overall": {"status": overall_status, "kurtosis": overall_td_kurt, "skewness": overall_td_skew},
        "segments": segments_status
    }

def process_eda_signal(signal_raw, fs):
    if len(signal_raw) == 0:
        return {
            "overall": {"status": "N/A", "kurtosis": 0.0, "skewness": 0.0},
            "segments": ["N/A"] * 10
        }

    # 1. Level check and RAC check per segment (10 segments of 30 samples)
    segments_status = []
    for i in range(10):
        segment = signal_raw[i * 30 : (i + 1) * 30]
        if len(segment) < 2:
            segments_status.append("N/A")
            continue

        seg_std = np.std(segment)
        if seg_std < 1e-5:
            # flatline
            segments_status.append("Poor")
            continue

        mean_val = np.mean(segment)
        if mean_val < 0.01:
            segments_status.append("Poor")
        elif mean_val < 0.05:
            segments_status.append("Fair")
        else:
            # Relative Amplitude Change (RAC) check
            max_idx = np.argmax(segment)
            min_idx = np.argmin(segment)
            max_val = segment[max_idx]
            min_val = segment[min_idx]

            first_val = max_val if max_idx < min_idx else min_val
            rac = abs(max_val - min_val) / abs(first_val) if first_val != 0 else np.inf

            if rac >= 0.20:
                segments_status.append("Poor")
            elif rac >= 0.10:
                segments_status.append("Fair")
            else:
                segments_status.append("Good")

    # 2. Overall Status
    std_overall = np.std(signal_raw)
    if std_overall < 1e-5:
        overall_status = "Poor"
        k_val = 0.0
        s_val = 0.0
    else:
        k_val = float(kurtosis(signal_raw, fisher=True))
        s_val = float(skew(signal_raw))

        valid_segs = [s for s in segments_status if s != "N/A"]
        if "Poor" in valid_segs:
            overall_status = "Poor"
        elif "Fair" in valid_segs:
            overall_status = "Fair"
        else:
            overall_status = "Good"

    return {
        "overall": {"status": overall_status, "kurtosis": k_val, "skewness": s_val},
        "segments": segments_status
    }

# ==========================================================
# MAIN EXECUTION LOOP
# ==========================================================
def main():
    try:
        while True:
            line = sys.stdin.readline()
            if not line:
                break
            line = line.strip()
            if not line:
                continue

            try:
                input_data = json.loads(line)

                ppg_ir = np.array(input_data.get("ppg_ir_signal", []), dtype=float)
                ppg_red = np.array(input_data.get("ppg_red_signal", []), dtype=float)
                ppg_green = np.array(input_data.get("ppg_green_signal", []), dtype=float)
                eda = np.array(input_data.get("eda_signal", []), dtype=float)
                fs_ppg = int(input_data.get("fs_ppg", 25))
                fs_eda = int(input_data.get("fs_eda", 15))

                # Fallback for legacy key
                if len(ppg_ir) == 0 and "ppg_signal" in input_data:
                    ppg_ir = np.array(input_data.get("ppg_signal", []), dtype=float)

                # Process all PPG channels
                ir_res = process_ppg_channel(ppg_ir, fs_ppg, histories["ppg_ir"])
                red_res = process_ppg_channel(ppg_red, fs_ppg, histories["ppg_red"])
                green_res = process_ppg_channel(ppg_green, fs_ppg, histories["ppg_green"])

                # Process EDA channel
                eda_res = process_eda_signal(eda, fs_eda)

                results = {
                    "ppg": green_res["overall"],  # Overall PPG status represented by Green channel
                    "ppg_red_overall": red_res["overall"],
                    "ppg_green_overall": green_res["overall"],
                    "eda": eda_res["overall"],
                    "ppg_ir_segments": ir_res["segments"],
                    "ppg_red_segments": red_res["segments"],
                    "ppg_green_segments": green_res["segments"],
                    "eda_segments": eda_res["segments"],
                    "info": "Calculated using integrated majority-voting and RAC logic"
                }

                print(json.dumps(results), flush=True)

            except Exception as e:
                print(json.dumps({"status": "Error", "error": str(e)}), flush=True)

    except Exception as e:
        print(json.dumps({"status": "Error", "error": str(e)}), flush=True)

if __name__ == "__main__":
    main()
