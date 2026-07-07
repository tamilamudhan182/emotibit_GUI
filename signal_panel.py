from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QFileDialog

import numpy as np
from scipy.signal import butter, filtfilt
import pandas as pd
import time

from emotibit_worker import EmotiBitWorker


class SignalPanel:

    def __init__(self, dashboard):

        self.dashboard = dashboard

        self.worker = None

        self.connected = False
        self.streaming = False
        self.recording = False

        # ===============================
        # RECORDING SYSTEM
        # ===============================
        self.record_data_list = []

        self.record_start_time = None
        self.record_end_time = None

        # Last values for recording alignment
        self.last_acc_x = 0.0
        self.last_acc_y = 0.0
        self.last_acc_z = 0.0
        self.last_gyro_x = 0.0
        self.last_gyro_y = 0.0
        self.last_gyro_z = 0.0
        self.last_ppg_ir = 0.0
        self.last_ppg_red = 0.0
        self.last_ppg_green = 0.0
        self.last_eda = 0.0
        self.last_temp1 = 0.0
        self.last_temp2 = 0.0

        # Signal Quality Control variables
        self.latest_ppg_sqi_status = "N/A"
        self.latest_ppg_sqi_kurtosis = 0.0
        self.latest_ppg_sqi_skewness = 0.0
        self.latest_eda_sqi_status = "N/A"
        self.latest_eda_sqi_kurtosis = 0.0
        self.latest_eda_sqi_skewness = 0.0
        self.latest_ppg_ir_segment_statuses = ["N/A"] * 6
        self.latest_ppg_red_segment_statuses = ["N/A"] * 6
        self.latest_ppg_green_segment_statuses = ["N/A"] * 6
        self.latest_eda_segment_statuses = ["N/A"] * 10
        self.ppg_ir_segment_history = []
        self.ppg_red_segment_history = []
        self.ppg_green_segment_history = []
        self.eda_segment_history = []
        self.latest_ir_filtered = None
        self.latest_eda_filtered = None
        self.sqi_running = False
        self.last_sqi_time = 0.0

        self.motion_threshold = 0.12  # Dynamic acceleration threshold in g
        self.latest_is_moving = np.array([], dtype=bool)

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_data)

    # ==================================================
    # CONNECT DEVICE
    # ==================================================
    def connect_device(self):

        if self.connected:
            print("Already connected")
            return

        try:
            print("Connecting to EmotiBit...")

            self.worker = EmotiBitWorker()
            self.worker.connect()

            self.connected = True

            try:
                self.dashboard.status_panel.connection_label.setText(
                    "Connection : 🟢 Connected"
                )
            except:
                pass

            print("Connected successfully")

        except Exception as e:
            print("Connection failed:", e)

    # ==================================================
    # DISCONNECT DEVICE
    # ==================================================
    def disconnect_device(self):

        self.timer.stop()

        if self.worker:
            try:
                self.worker.disconnect()
            except:
                pass

        self.worker = None

        self.connected = False
        self.streaming = False
        self.recording = False

        self.record_data_list = []
        self.record_start_time = None
        self.record_end_time = None

        try:
            self.dashboard.status_panel.connection_label.setText(
                "Connection : 🔴 Disconnected"
            )
            self.dashboard.status_panel.streaming_label.setText(
                "Streaming : ⚪ Idle"
            )
            self.dashboard.status_panel.recording_label.setText(
                "Recording : ⚪ Not Recording"
            )
        except:
            pass

        # Terminate SQI persistent process
        if hasattr(self, "sqi_process") and self.sqi_process is not None:
            try:
                self.sqi_process.terminate()
                self.sqi_process.wait(timeout=1.0)
            except:
                pass
            self.sqi_process = None

        print("Disconnected")

    # ==================================================
    # STREAM CONTROL
    # ==================================================
    def start_stream(self):

        if not self.connected:
            print("Connect EmotiBit first")
            return

        self.timer.start(40)
        self.streaming = True

        try:
            self.dashboard.status_panel.streaming_label.setText(
                "Streaming : 🟢 Active"
            )
        except:
            pass

        print("Streaming started")

    def stop_stream(self):

        self.timer.stop()
        self.streaming = False

        try:
            self.dashboard.status_panel.streaming_label.setText(
                "Streaming : ⚪ Idle"
            )
        except:
            pass

        print("Streaming stopped")

    def pause_stream(self):

        if self.timer.isActive():
            self.timer.stop()
            try:
                self.dashboard.status_panel.streaming_label.setText(
                    "Streaming : 🟡 Paused"
                )
            except:
                pass
        else:
            self.timer.start(40)
            try:
                self.dashboard.status_panel.streaming_label.setText(
                    "Streaming : 🟢 Active"
                )
            except:
                pass

    # ==================================================
    # RECORD TOGGLE + TIMER
    # ==================================================
    def start_recording(self):

        if not self.streaming:
            print("Must be streaming to start recording")
            return

        self.recording = True
        self.record_data_list = []

        self.record_start_time = time.time()
        self.record_end_time = None

        try:
            self.dashboard.status_panel.recording_label.setText(
                "Recording : 🔴 Recording (0.0s)"
            )
        except:
            pass

        print("Recording Started")

    def stop_recording(self):

        if not self.recording:
            print("Not currently recording")
            return

        self.recording = False
        self.record_end_time = time.time()
        duration = self.get_recording_duration()

        try:
            self.dashboard.status_panel.recording_label.setText(
                f"Recording : ⚪ Stopped ({duration:.1f}s)"
            )
        except:
            pass

        print("Recording Stopped")

    # ==================================================
    # DURATION
    # ==================================================
    def get_recording_duration(self):

        if self.record_start_time is None:
            return 0

        end = self.record_end_time or time.time()
        return round(end - self.record_start_time, 2)

    # ==================================================
    # SAVE CSV
    # ==================================================
    def save_data(self):

        if self.recording:
            print("Please stop recording first")
            return

        if len(self.record_data_list) == 0:
            print("No data recorded")
            return

        path, _ = QFileDialog.getSaveFileName(
            None,
            "Save EmotiBit Data",
            "emotibit_record.csv",
            "CSV Files (*.csv)"
        )

        if not path:
            return

        duration = self.get_recording_duration()

        df = pd.DataFrame(
            self.record_data_list,
            columns=[
                "AccX",
                "AccY",
                "AccZ",
                "GyroX",
                "GyroY",
                "GyroZ",
                "PPG_IR",
                "PPG_Red",
                "PPG_Green",
                "EDA",
                "Temp1",
                "Temp2",
                "PPG_Quality",
                "PPG_Kurtosis",
                "PPG_Skewness",
                "EDA_Quality",
                "EDA_Kurtosis",
                "EDA_Skewness"
            ]
        )

        df["SessionDuration_sec"] = duration

        df.to_csv(path, index=False)

        print("Saved:", path)

                    # ==================================================
    # FILTER
    # ==================================================
    def butter_bandpass(self, lowcut=0.5, highcut=8.0, fs=25, order=4):

        nyq = 0.5 * fs
        b, a = butter(
            order,
            [lowcut / nyq, highcut / nyq],
            btype='band'
        )

        return b, a

    def filter_ppg(self, signal):

        if len(signal) < 50:
            return signal

        try:
            lowcut = 0.5
            highcut = 5.0
            
            try:
                ppg_panel = self.dashboard.ppg_panel
                low_str = ppg_panel.lowcut_input.text().strip()
                high_str = ppg_panel.highcut_input.text().strip()
                if low_str:
                    lowcut = float(low_str)
                if high_str:
                    highcut = float(high_str)
            except Exception as e:
                print("Error reading PPG filter inputs:", e)

            fs = 25.0
            nyq = 0.5 * fs
            
            if lowcut <= 0:
                lowcut = 0.01
            if highcut >= nyq * 0.9:
                highcut = nyq * 0.9
            if lowcut >= highcut:
                lowcut = highcut * 0.1

            b, a = self.butter_bandpass(lowcut=lowcut, highcut=highcut, fs=fs)

            res = filtfilt(
                b,
                a,
                signal
            )
            return np.nan_to_num(res)

        except Exception as e:
            # Fallback
            try:
                b, a = self.butter_bandpass(lowcut=0.5, highcut=5.0, fs=25)
                res = filtfilt(b, a, signal)
                return np.nan_to_num(res)
            except:
                return np.nan_to_num(signal)

    def filter_eda(self, signal):

        if len(signal) < 30:
            return np.nan_to_num(signal)

        try:
            fs = 15.0
            cutoff = 2.0
            nyq = 0.5 * fs

            try:
                eda_panel = self.dashboard.eda_panel
                cutoff_str = eda_panel.cutoff_input.text().strip()
                if cutoff_str:
                    cutoff = float(cutoff_str)
            except Exception as e:
                print("Error reading EDA filter input:", e)

            if cutoff <= 0:
                cutoff = 0.01
            if cutoff >= nyq * 0.9:
                cutoff = nyq * 0.9

            b, a = butter(
                4,
                cutoff / nyq,
                btype='low'
            )

            res = filtfilt(
                b,
                a,
                signal
            )
            return np.nan_to_num(res)

        except Exception as e:
            # Fallback
            try:
                b, a = butter(4, 2.0 / 7.5, btype='low')
                res = filtfilt(b, a, signal)
                return np.nan_to_num(res)
            except:
                return np.nan_to_num(signal)


    # ==================================================
    # MAIN UPDATE LOOP
    # ==================================================
    def update_data(self):

        if self.worker is None:
            return

        try:

            board = self.worker.board

            data_default = board.get_current_board_data(
                300
            )

            data_aux = board.get_current_board_data(
                300,
                preset=1
            )

            data_anc = board.get_current_board_data(
                300,
                preset=2
            )

            # =========================
            # MOTION
            # =========================
            motion = self.dashboard.motion_panel

            if data_default.shape[1] > 0:

                # Remove baseline/mean offset for visualization so the curves auto-zoom on fluctuations
                acc_x = data_default[1] - np.mean(data_default[1])
                acc_y = data_default[2] - np.mean(data_default[2])
                acc_z = data_default[3] - np.mean(data_default[3])

                gyro_x = data_default[4] - np.mean(data_default[4])
                gyro_y = data_default[5] - np.mean(data_default[5])
                gyro_z = data_default[6] - np.mean(data_default[6])

                motion.acc_x_curve.setData(acc_x)
                motion.acc_y_curve.setData(acc_y)
                motion.acc_z_curve.setData(acc_z)

                motion.gyro_x_curve.setData(gyro_x)
                motion.gyro_y_curve.setData(gyro_y)
                motion.gyro_z_curve.setData(gyro_z)

                # Keep absolute raw values for CSV recording
                self.last_acc_x = data_default[1][-1]
                self.last_acc_y = data_default[2][-1]
                self.last_acc_z = data_default[3][-1]
                self.last_gyro_x = data_default[4][-1]
                self.last_gyro_y = data_default[5][-1]
                self.last_gyro_z = data_default[6][-1]

                # Compute dynamic acceleration magnitude and rolling RMS
                window_size = 15
                mag_sq = acc_x**2 + acc_y**2 + acc_z**2
                if len(mag_sq) >= window_size:
                    rolling_var = np.convolve(mag_sq, np.ones(window_size) / window_size, mode='same')
                else:
                    rolling_var = mag_sq
                rms = np.sqrt(rolling_var)
                self.latest_is_moving = rms > self.motion_threshold

                # Update accelerometer plot highlights/badges
                motion.update_motion_regions(self.latest_is_moving)

            # =========================
            # PPG
            # =========================
            ppg = self.dashboard.ppg_panel

            if data_aux.shape[1] > 0:

                ir_raw = np.array(
                    data_aux[1],
                    dtype=float
                )

                red_raw = np.array(
                    data_aux[2],
                    dtype=float
                )

                green_raw = np.array(
                    data_aux[3],
                    dtype=float
                )

                # Keep the original raw values as baseline reference
                ir_mean = np.mean(ir_raw)
                red_mean = np.mean(red_raw)
                green_mean = np.mean(green_raw)

                # Remove DC component (baseline) for raw signals so they can be plotted on the same scale
                ir_raw -= ir_mean
                red_raw -= red_mean
                green_raw -= green_mean

                # Filter signals to create filtered signals
                ir_filtered = self.filter_ppg(ir_raw)
                self.latest_ir_filtered = ir_filtered
                red_filtered = self.filter_ppg(red_raw)
                self.latest_red_filtered = red_filtered
                green_filtered = self.filter_ppg(green_raw)
                self.latest_green_filtered = green_filtered

                # Update the recording targets based on show_mode:
                if ppg.show_mode == "filtered":
                    # Add back the DC baseline so the recorded filtered data is on the same scale/unit range as raw data,
                    # preventing a sudden drop to zero (which would break analysis and visual continuity in the CSV).
                    self.last_ppg_ir = ir_filtered[-1] + ir_mean
                    self.last_ppg_red = red_filtered[-1] + red_mean
                    self.last_ppg_green = green_filtered[-1] + green_mean
                else:
                    self.last_ppg_ir = data_aux[1][-1]
                    self.last_ppg_red = data_aux[2][-1]
                    self.last_ppg_green = data_aux[3][-1]

                # Update raw curves
                ppg.ppg_ir_raw_curve.setData(ir_raw)
                ppg.ppg_red_raw_curve.setData(red_raw)
                ppg.ppg_green_raw_curve.setData(green_raw)

                # Update filtered curves
                ppg.ppg_ir_curve.setData(ir_filtered)
                ppg.ppg_red_curve.setData(red_filtered)
                ppg.ppg_green_curve.setData(green_filtered)

                # Update FFT plot with the filtered signals
                ppg.update_fft(ir_filtered, red_filtered, green_filtered)

                # Auto zoom passing both raw and filtered sets
                ppg.update_auto_zoom(
                    ir_raw,
                    red_raw,
                    green_raw,
                    ir_filtered,
                    red_filtered,
                    green_filtered
                )

                # Align and update motion regions in PPG panel (both are 25Hz, 1:1 match)
                ppg_is_moving = np.zeros(len(ir_raw), dtype=bool)
                if len(self.latest_is_moving) > 0:
                    n_ppg = len(ir_raw)
                    n_acc = len(self.latest_is_moving)
                    if n_acc >= n_ppg:
                        ppg_is_moving = self.latest_is_moving[-n_ppg:]
                    else:
                        ppg_is_moving[-n_acc:] = self.latest_is_moving
                ppg.update_motion_regions(ppg_is_moving)

            # =========================
            # EDA
            # =========================
            eda = self.dashboard.eda_panel

            if data_anc.shape[1] > 0:

                eda_raw = np.array(
                    data_anc[1],
                    dtype=float
                )

                eda_raw = np.nan_to_num(
                    eda_raw
                )

                # Low-pass filter to get filtered EDA
                eda_filtered = self.filter_eda(eda_raw)
                self.latest_eda_filtered = eda_filtered

                # Subtract mean baseline for high-resolution graphing fluctuations
                eda_raw_centered = eda_raw - np.mean(eda_raw)
                eda_filtered_centered = eda_filtered - np.mean(eda_filtered)

                # Update raw curve with centered data
                eda.eda_raw_curve.setData(
                    eda_raw_centered
                )

                # Update filtered curve with centered data
                eda.eda_curve.setData(
                    eda_filtered_centered
                )

                # Update FFT plot with the filtered signals
                eda.update_fft(eda_filtered_centered)

                # Auto zoom passing both centered sets
                eda.update_auto_zoom(
                    eda_raw_centered,
                    eda_filtered_centered
                )

                # Align and update motion regions in EDA panel (resample from 25Hz to 15Hz)
                eda_is_moving = np.zeros(len(eda_raw), dtype=bool)
                if len(self.latest_is_moving) > 0 and len(eda_raw) > 0:
                    n_eda = len(eda_raw)
                    n_acc = len(self.latest_is_moving)
                    eda_indices = np.arange(n_eda)
                    t_from_end = (n_eda - 1 - eda_indices) / 15.0
                    acc_indices_float = (n_acc - 1) - t_from_end * 25.0
                    acc_indices = np.round(acc_indices_float).astype(int)
                    valid_mask = (acc_indices >= 0) & (acc_indices < n_acc)
                    eda_is_moving[valid_mask] = self.latest_is_moving[acc_indices[valid_mask]]
                eda.update_motion_regions(eda_is_moving)

                # Update the recording targets based on show_mode:
                if eda.show_mode == "filtered" and len(eda_filtered) > 0:
                    self.last_eda = eda_filtered[-1]
                else:
                    self.last_eda = data_anc[1][-1]

            # =========================
            # TEMPERATURE
            # =========================
            temp = self.dashboard.temp_panel

            if data_anc.shape[1] > 0:

                temp1 = np.array(
                    data_anc[2],
                    dtype=float
                )

                temp2 = np.array(
                    data_anc[3],
                    dtype=float
                )

                temp.temp1_curve.setData(
                    temp1
                )

                temp.temp2_curve.setData(
                    temp2
                )

                self.last_temp1 = data_anc[2][-1]
                self.last_temp2 = data_anc[3][-1]

            # Periodically trigger SQI calculation (every 0.5 seconds) in background
            current_time = time.time()
            if current_time - self.last_sqi_time > 0.5:
                ir_buf = getattr(self, "latest_ir_filtered", None)
                red_buf = getattr(self, "latest_red_filtered", None)
                green_buf = getattr(self, "latest_green_filtered", None)
                eda_buf = getattr(self, "latest_eda_filtered", None)
                if (ir_buf is not None and len(ir_buf) >= 300 and
                    red_buf is not None and len(red_buf) >= 300 and
                    green_buf is not None and len(green_buf) >= 300 and
                    eda_buf is not None and len(eda_buf) >= 300):
                    self.last_sqi_time = current_time
                    self.update_sqi_async(
                        ir_buf[-300:].tolist(),
                        red_buf[-300:].tolist(),
                        green_buf[-300:].tolist(),
                        eda_buf[-300:].tolist()
                    )

            # =========================
            # RECORD DATA
            # =========================
            if self.recording:
                self.record_data_list.append([
                    self.last_acc_x,
                    self.last_acc_y,
                    self.last_acc_z,
                    self.last_gyro_x,
                    self.last_gyro_y,
                    self.last_gyro_z,
                    self.last_ppg_ir,
                    self.last_ppg_red,
                    self.last_ppg_green,
                    self.last_eda,
                    self.last_temp1,
                    self.last_temp2,
                    self.latest_ppg_sqi_status,
                    self.latest_ppg_sqi_kurtosis,
                    self.latest_ppg_sqi_skewness,
                    self.latest_eda_sqi_status,
                    self.latest_eda_sqi_kurtosis,
                    self.latest_eda_sqi_skewness
                ])

                duration = self.get_recording_duration()
                try:
                    self.dashboard.status_panel.recording_label.setText(
                        f"Recording : 🔴 Recording ({duration:.1f}s)"
                    )
                except:
                    pass

            # Update quality badge on UI
            status_text = "Signal Quality: PPG "
            if self.latest_ppg_sqi_status == "Good":
                status_text += "🟢 Good"
            elif self.latest_ppg_sqi_status == "Fair":
                status_text += "🟡 Fair"
            elif self.latest_ppg_sqi_status == "Poor":
                status_text += "🔴 Poor"
            else:
                status_text += "⚪ N/A"
            if self.latest_ppg_sqi_status in ["Good", "Fair", "Poor"]:
                status_text += f" (K:{self.latest_ppg_sqi_kurtosis:.1f})"
                
            status_text += " | EDA "
            if self.latest_eda_sqi_status == "Good":
                status_text += "🟢 Good"
            elif self.latest_eda_sqi_status == "Fair":
                status_text += "🟡 Fair"
            elif self.latest_eda_sqi_status == "Poor":
                status_text += "🔴 Poor"
            else:
                status_text += "⚪ N/A"
            if self.latest_eda_sqi_status in ["Good", "Fair", "Poor"]:
                status_text += f" (K:{self.latest_eda_sqi_kurtosis:.1f})"
                
            try:
                self.dashboard.status_panel.quality_label.setText(status_text)
                self.dashboard.ppg_panel.update_region_color(
                    self.latest_ppg_ir_segment_statuses,
                    self.latest_ppg_red_segment_statuses,
                    self.latest_ppg_green_segment_statuses
                )
                self.dashboard.eda_panel.update_region_color(self.latest_eda_segment_statuses)
            except Exception as e:
                print("Error updating UI quality status/colors:", e)

        except Exception as e:

            print(
                "Update error:",
                e
            )

    def update_sqi_async(self, ir_buffer, red_buffer, green_buffer, eda_buffer):
        if getattr(self, "sqi_running", False):
            return
        self.sqi_running = True
        import threading
        threading.Thread(
            target=self._run_sqi_subprocess,
            args=(ir_buffer, red_buffer, green_buffer, eda_buffer),
            daemon=True
        ).start()

    def _run_sqi_subprocess(self, ir_buffer, red_buffer, green_buffer, eda_buffer):
        import subprocess
        import json
        import os
        import sys
        
        try:
            payload = json.dumps({
                "ppg_ir_signal": ir_buffer,
                "ppg_red_signal": red_buffer,
                "ppg_green_signal": green_buffer,
                "eda_signal": eda_buffer,
                "fs_ppg": 25,
                "fs_eda": 15
            })
            
            # Resolve script directory and run_sqi.py path
            script_dir = os.path.dirname(os.path.abspath(__file__))
            run_sqi_path = os.path.join(script_dir, "run_sqi.py")
            
            # Start persistent process if not running or if exited
            if not hasattr(self, "sqi_process") or self.sqi_process is None or self.sqi_process.poll() is not None:
                # Dynamically look for Python interpreter in virtual environment
                venv_python = os.path.join(script_dir, ".venv_sqi", "Scripts", "python.exe")
                if not os.path.exists(venv_python):
                    # Try unix-like path just in case
                    venv_python = os.path.join(script_dir, ".venv_sqi", "bin", "python")
                if not os.path.exists(venv_python):
                    # Fallback to hardcoded absolute path
                    venv_python = r"d:\EMOTI\.venv_sqi\Scripts\python.exe"
                if not os.path.exists(venv_python):
                    # Fallback to current running Python
                    venv_python = sys.executable
                    
                self.sqi_process = subprocess.Popen(
                    [venv_python, run_sqi_path],
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    bufsize=1
                )
                
            # Write payload to stdin and flush
            self.sqi_process.stdin.write(payload + "\n")
            self.sqi_process.stdin.flush()
            
            # Read single-line output
            stdout = self.sqi_process.stdout.readline()
            if not stdout:
                # Subprocess exited or failed
                stderr_content = ""
                if self.sqi_process.stderr:
                    try:
                        stderr_content = self.sqi_process.stderr.read()
                    except:
                        pass
                print(f"SQI subprocess EOF. Return code: {self.sqi_process.poll()}. Stderr: {stderr_content}")
                self.sqi_process = None
                return
                
            results = json.loads(stdout)
            
            ppg_res = results.get("ppg", {})
            self.latest_ppg_sqi_status = ppg_res.get("status", "Unknown")
            self.latest_ppg_sqi_kurtosis = ppg_res.get("kurtosis", 0.0)
            self.latest_ppg_sqi_skewness = ppg_res.get("skewness", 0.0)
            
            eda_res = results.get("eda", {})
            self.latest_eda_sqi_status = eda_res.get("status", "Unknown")
            self.latest_eda_sqi_kurtosis = eda_res.get("kurtosis", 0.0)
            self.latest_eda_sqi_skewness = eda_res.get("skewness", 0.0)
            raw_ir_segs = results.get("ppg_ir_segments", ["N/A"] * 6)
            raw_red_segs = results.get("ppg_red_segments", ["N/A"] * 6)
            raw_green_segs = results.get("ppg_green_segments", ["N/A"] * 6)
            raw_eda_segs = results.get("eda_segments", ["N/A"] * 10)
            
            self.latest_ppg_ir_segment_statuses = self._smooth_segment_statuses(self.ppg_ir_segment_history, raw_ir_segs)
            self.latest_ppg_red_segment_statuses = self._smooth_segment_statuses(self.ppg_red_segment_history, raw_red_segs)
            self.latest_ppg_green_segment_statuses = self._smooth_segment_statuses(self.ppg_green_segment_history, raw_green_segs)
            self.latest_eda_segment_statuses = self._smooth_segment_statuses(self.eda_segment_history, raw_eda_segs)
                
        except Exception as e:
            print("SQI calculation thread error:", e)
        finally:
            self.sqi_running = False

    def _smooth_segment_statuses(self, history, new_statuses):
        history.append(new_statuses)
        if len(history) > 3:
            history.pop(0)
        smoothed = []
        for i in range(len(new_statuses)):
            seg_hist = [h[i] for h in history]
            poors = seg_hist.count("Poor")
            fairs = seg_hist.count("Fair")
            goods = seg_hist.count("Good")
            if poors >= 2:
                smoothed.append("Poor")
            elif fairs >= 2:
                smoothed.append("Fair")
            elif goods >= 2:
                smoothed.append("Good")
            else:
                smoothed.append(seg_hist[-1])
        return smoothed