#!/usr/bin/env python3
"""
Generate morphology graphs for PPG and EDA channels from a CSV file.
Usage:
  python morphology_ppg_eda.py path/to/emotibit_record3.csv

Saves: ppg_morphology.png, eda_morphology.png
"""
import argparse
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.signal import savgol_filter, find_peaks


def find_columns(df):
    cols = {c.lower(): c for c in df.columns}
    ppg_col = None
    eda_col = None
    for k, v in cols.items():
        if 'ppg' in k:
            ppg_col = v
        if 'eda' in k:
            eda_col = v
    return ppg_col, eda_col


def get_time_axis(df):
    # try common timestamp columns
    for name in ['timestamp', 'time', 'ts', 't']:
        if name in df.columns:
            try:
                t = pd.to_datetime(df[name], unit='ms', errors='coerce')
                if t.isnull().all():
                    # maybe it's seconds or numeric
                    return df[name].astype(float).to_numpy()
                else:
                    # convert to seconds relative
                    secs = (t - t.iloc[0]).dt.total_seconds().to_numpy()
                    return secs
            except Exception:
                continue
    # fallback to index as samples
    return np.arange(len(df))


def plot_ppg_morphology(t, x, out="ppg_morphology.png", fs=None):
    # smooth
    win = min(len(x) - 1, 101)
    if win % 2 == 0:
        win -= 1
    if win < 5:
        win = 5
    smooth = savgol_filter(x, win, 3)

    # estimate sampling frequency
    if fs is None:
        if len(t) > 1:
            dif = np.diff(t)
            median_dt = np.median(dif)
            if median_dt > 0:
                fs = 1.0 / median_dt
            else:
                fs = None
    # detect peaks (assume systolic peaks)
    distance = max(1, int(0.5 * fs)) if fs else 30
    peaks, _ = find_peaks(smooth, distance=distance)

    # compute average beat waveform
    half_win = max(1, int(0.6 * fs)) if fs else 50
    beats = []
    for p in peaks:
        start = p - half_win
        end = p + half_win
        if start >= 0 and end <= len(x):
            beats.append(smooth[start:end])
    if len(beats) > 0:
        beats = np.array(beats)
        mean_beat = np.mean(beats, axis=0)
        beat_t = np.linspace(-half_win / fs, half_win / fs, mean_beat.shape[0]) if fs else np.linspace(-half_win, half_win, mean_beat.shape[0])
    else:
        mean_beat = None
        beat_t = None

    plt.figure(figsize=(10, 6))
    plt.subplot(2, 1, 1)
    plt.plot(t, x, label='raw', alpha=0.5)
    plt.plot(t, smooth, label='smoothed', linewidth=1)
    plt.scatter(t[peaks], smooth[peaks], s=10, c='red', label='peaks')
    plt.title('PPG — Raw and Smoothed')
    plt.xlabel('Time (s)')
    plt.legend()

    plt.subplot(2, 1, 2)
    if mean_beat is not None:
        plt.plot(beat_t, mean_beat)
        plt.title('Average PPG Beat Morphology (aligned to peaks)')
        plt.xlabel('Time around peak (s)')
    else:
        plt.text(0.5, 0.5, 'Not enough detected beats for average morphology', ha='center')
        plt.title('Average PPG Beat Morphology')
    plt.tight_layout()
    plt.savefig(out)
    plt.close()
    print(f"Saved PPG morphology to {out}")


def plot_eda_morphology(t, x, out="eda_morphology.png", fs=None):
    # smooth strongly for EDA
    win = min(len(x) - 1, 301)
    if win % 2 == 0:
        win -= 1
    if win < 7:
        win = 7
    smooth = savgol_filter(x, win, 3)

    # derivative / phasic activity
    deriv = np.gradient(smooth, t) if len(t) == len(smooth) else np.gradient(smooth)

    plt.figure(figsize=(10, 6))
    plt.subplot(2, 1, 1)
    plt.plot(t, x, label='raw', alpha=0.5)
    plt.plot(t, smooth, label='smoothed', linewidth=1)
    plt.title('EDA — Raw and Smoothed')
    plt.xlabel('Time (s)')
    plt.legend()

    plt.subplot(2, 1, 2)
    plt.plot(t, deriv)
    plt.title('EDA derivative (phasic changes) — morphology view')
    plt.xlabel('Time (s)')
    plt.tight_layout()
    plt.savefig(out)
    plt.close()
    print(f"Saved EDA morphology to {out}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('csv', nargs='?', default=r"d:\\EMOTI\\emotibit_record3.csv", help='Path to CSV file')
    parser.add_argument('--ppg_out', default='ppg_morphology.png')
    parser.add_argument('--eda_out', default='eda_morphology.png')
    args = parser.parse_args()

    if not os.path.exists(args.csv):
        print('CSV not found:', args.csv)
        return

    df = pd.read_csv(args.csv)
    ppg_col, eda_col = find_columns(df)
    if ppg_col is None and eda_col is None:
        print('Could not find `ppg` or `eda` columns in CSV. Columns found:', list(df.columns))
        return

    t = get_time_axis(df)

    if ppg_col is not None:
        x_ppg = pd.to_numeric(df[ppg_col], errors='coerce').ffill().to_numpy()
        fs = None
        if len(t) > 1:
            dt = np.median(np.diff(t))
            if dt > 0:
                fs = 1.0 / dt
        plot_ppg_morphology(t, x_ppg, out=args.ppg_out, fs=fs)
    else:
        print('PPG column not found; skipping PPG plot')

    if eda_col is not None:
        x_eda = pd.to_numeric(df[eda_col], errors='coerce').ffill().to_numpy()
        fs = None
        if len(t) > 1:
            dt = np.median(np.diff(t))
            if dt > 0:
                fs = 1.0 / dt
        plot_eda_morphology(t, x_eda, out=args.eda_out, fs=fs)
    else:
        print('EDA column not found; skipping EDA plot')


if __name__ == '__main__':
    main()
