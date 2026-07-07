from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QButtonGroup, QLabel, QLineEdit
import pyqtgraph as pg
import numpy as np


class PPGPanel(QWidget):

    def __init__(self):
        super().__init__()

        layout = QVBoxLayout()

        # ====================================
        # MODE SELECTION BUTTONS
        # ====================================
        btn_layout = QHBoxLayout()

        self.btn_raw = QPushButton("Raw Data")
        self.btn_filtered = QPushButton("Filter Data")

        self.btn_raw.setCheckable(True)
        self.btn_filtered.setCheckable(True)

        self.btn_group = QButtonGroup(self)
        self.btn_group.addButton(self.btn_raw)
        self.btn_group.addButton(self.btn_filtered)
        self.btn_group.setExclusive(True)

        # Default mode
        self.show_mode = "filtered"
        self.btn_filtered.setChecked(True)

        # Stylesheet for premium look
        button_style = """
            QPushButton {
                background-color: #2b2b2b;
                color: #ffffff;
                border: 1px solid #555555;
                padding: 6px 20px;
                border-radius: 4px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #3b3b3b;
                border-color: #888888;
            }
            QPushButton:checked {
                background-color: #007acc;
                border-color: #0098ff;
            }
        """
        self.btn_raw.setStyleSheet(button_style)
        self.btn_filtered.setStyleSheet(button_style)

        btn_layout.addWidget(self.btn_raw)
        btn_layout.addWidget(self.btn_filtered)

        # Filter Cutoffs manual inputs
        self.lbl_filter = QLabel("Filter Cutoffs (Hz):")
        self.lbl_filter.setStyleSheet("color: #ffffff; font-size: 13px; font-weight: bold; margin-left: 15px;")
        
        self.lowcut_input = QLineEdit("0.5")
        self.lowcut_input.setStyleSheet("""
            QLineEdit {
                background-color: #2b2b2b;
                color: #ffffff;
                border: 1px solid #555555;
                border-radius: 4px;
                padding: 4px 8px;
                font-size: 13px;
                max-width: 60px;
            }
            QLineEdit:focus {
                border-color: #007acc;
            }
        """)
        
        self.lbl_to = QLabel("to")
        self.lbl_to.setStyleSheet("color: #ffffff; font-size: 13px; font-weight: bold; margin-left: 5px; margin-right: 5px;")
        
        self.highcut_input = QLineEdit("5.0")
        self.highcut_input.setStyleSheet("""
            QLineEdit {
                background-color: #2b2b2b;
                color: #ffffff;
                border: 1px solid #555555;
                border-radius: 4px;
                padding: 4px 8px;
                font-size: 13px;
                max-width: 60px;
            }
            QLineEdit:focus {
                border-color: #007acc;
            }
        """)

        btn_layout.addWidget(self.lbl_filter)
        btn_layout.addWidget(self.lowcut_input)
        btn_layout.addWidget(self.lbl_to)
        btn_layout.addWidget(self.highcut_input)
        btn_layout.addStretch()

        layout.addLayout(btn_layout)

        # ====================================
        # PLOTS SETUP (PPG Time Domain & PPG FFT)
        # ====================================
        self.ppg_plot = pg.PlotWidget(title="PPG Signals")
        self.fft_plot = pg.PlotWidget(title="PPG FFT Spectrum")

        # Configure time domain PPG plot
        ppg_plot_item = self.ppg_plot.getPlotItem()
        ppg_view_box = ppg_plot_item.getViewBox()
        ppg_plot_item.showGrid(x=True, y=True, alpha=0.3)
        ppg_plot_item.addLegend()
        ppg_plot_item.setLabel('left', 'Amplitude')
        ppg_plot_item.setLabel('bottom', 'Samples')
        # pyrefly: ignore [bad-keyword-argument]
        ppg_plot_item.setXRange(0, 300, padding=0)
        ppg_plot_item.setClipToView(True)
        ppg_view_box.setMouseEnabled(x=True, y=True)
        ppg_view_box.enableAutoRange(axis=pg.ViewBox.YAxis, enable=False)

        # Configure frequency domain FFT plot
        fft_plot_item = self.fft_plot.getPlotItem()
        fft_view_box = fft_plot_item.getViewBox()
        fft_plot_item.showGrid(x=True, y=True, alpha=0.3)
        fft_plot_item.addLegend()
        fft_plot_item.setLabel('left', 'PSD (counts²/Hz)')
        fft_plot_item.setLabel('bottom', 'Frequency (Hz)')
        # pyrefly: ignore [bad-keyword-argument]
        fft_plot_item.setXRange(0, 10.0, padding=0)
        fft_plot_item.setClipToView(True)
        fft_view_box.setMouseEnabled(x=True, y=True)
        fft_view_box.enableAutoRange(axis=pg.ViewBox.YAxis, enable=False)

        # ====================================
        # 6 OVERLAY SEGMENTS SPANNING 300 SAMPLES
        # ====================================
        self.ppg_regions = []
        
        for i in range(6):
            val_range = [i * 50, (i + 1) * 50]
            
            reg = pg.LinearRegionItem(
                values=val_range,
                brush=pg.mkBrush(150, 150, 150, 40),
                pen=pg.mkPen(color=(150, 150, 150, 100), width=1),
                movable=False
            )
            ppg_plot_item.addItem(reg)
            self.ppg_regions.append(reg)

        # ====================================
        # RAW CURVES (Thin, medium-bright)
        # ====================================
        self.ppg_ir_raw_curve = ppg_plot_item.plot(
            pen=pg.mkPen('#00a6a6', width=1),
            name='IR Raw'
        )

        self.ppg_red_raw_curve = ppg_plot_item.plot(
            pen=pg.mkPen('#d94141', width=1),
            name='Red Raw'
        )

        self.ppg_green_raw_curve = ppg_plot_item.plot(
            pen=pg.mkPen('#41d941', width=1),
            name='Green Raw'
        )

        # ====================================
        # FILTERED CURVES (Thick, bright)
        # ====================================
        self.ppg_ir_curve = ppg_plot_item.plot(
            pen=pg.mkPen('c', width=2),
            name='IR Filter'
        )

        self.ppg_red_curve = ppg_plot_item.plot(
            pen=pg.mkPen('r', width=2),
            name='Red Filter'
        )

        self.ppg_green_curve = ppg_plot_item.plot(
            pen=pg.mkPen('g', width=2),
            name='Green Filter'
        )

        # ====================================
        # FFT SPECTRUM CURVES
        # ====================================
        self.fft_ir_curve = fft_plot_item.plot(
            pen=pg.mkPen('#00a6a6', width=2),
            name='IR FFT'
        )
        self.fft_red_curve = fft_plot_item.plot(
            pen=pg.mkPen('#d94141', width=2),
            name='Red FFT'
        )
        self.fft_green_curve = fft_plot_item.plot(
            pen=pg.mkPen('#41d941', width=2),
            name='Green FFT'
        )

        # Connect button click handlers
        self.btn_raw.clicked.connect(self.set_raw_mode)
        self.btn_filtered.clicked.connect(self.set_filtered_mode)

        # Apply default visibility
        self.set_filtered_mode()

        # ====================================
        # LAYOUT ASSEMBLY (Horizontal layout for plots)
        # ====================================
        plots_layout = QHBoxLayout()
        plots_layout.addWidget(self.ppg_plot, stretch=7)
        plots_layout.addWidget(self.fft_plot, stretch=3)
        
        layout.addLayout(plots_layout)
        self.setLayout(layout)

        # Motion regions pool (10 regions)
        self.motion_regions = []
        for _ in range(10):
            region = pg.LinearRegionItem(
                values=[0, 0],
                brush=pg.mkBrush(255, 69, 0, 45),  # Semi-transparent red-orange
                pen=pg.mkPen(color=(255, 69, 0, 100), width=1.5),
                movable=False
            )
            region.setVisible(False)
            self.ppg_plot.addItem(region)
            self.motion_regions.append(region)

        # Motion label TextItem
        self.motion_label = pg.TextItem(
            text="",
            color=(255, 69, 0),
            anchor=(0.5, 0),
            fill=(30, 30, 30, 200),
            border=pg.mkPen(255, 69, 0, 180)
        )
        font = self.motion_label.textItem.font()
        font.setPointSize(14)
        font.setBold(True)
        self.motion_label.setFont(font)
        self.motion_label.setVisible(False)
        self.ppg_plot.addItem(self.motion_label)

    def set_raw_mode(self):
        self.show_mode = "raw"
        # Hide filtered curves
        self.ppg_ir_curve.setVisible(False)
        self.ppg_red_curve.setVisible(False)
        self.ppg_green_curve.setVisible(False)
        # Show raw curves
        self.ppg_ir_raw_curve.setVisible(True)
        self.ppg_red_raw_curve.setVisible(True)
        self.ppg_green_raw_curve.setVisible(True)

    def set_filtered_mode(self):
        self.show_mode = "filtered"
        # Show all curves
        self.ppg_ir_curve.setVisible(True)
        self.ppg_red_curve.setVisible(True)
        self.ppg_green_curve.setVisible(True)
        
        self.ppg_ir_raw_curve.setVisible(True)
        self.ppg_red_raw_curve.setVisible(True)
        self.ppg_green_raw_curve.setVisible(True)

    # ====================================
    # 🔥 AUTO ZOOM FUNCTION (USED BY SIGNAL_PANEL)
    # ====================================
    def update_auto_zoom(self, ir_raw, red_raw, green_raw, ir_filt, red_filt, green_filt):
        try:
            if self.show_mode == "raw":
                all_data = np.concatenate([ir_raw, red_raw, green_raw])
            else:
                all_data = np.concatenate([ir_raw, red_raw, green_raw, ir_filt, red_filt, green_filt])

            all_data_clean = all_data[np.isfinite(all_data)]
            if len(all_data_clean) == 0:
                return

            ymin = np.min(all_data_clean)
            ymax = np.max(all_data_clean)

            # prevent flatline crash
            if ymin == ymax:
                ymin -= 1
                ymax += 1

            margin = (ymax - ymin) * 0.15

            self.ppg_plot.getPlotItem().setYRange(
                ymin - margin,
                ymax + margin,
                padding=0
            )

        except Exception as e:
            print("Auto zoom error in combined PPG plot:", e)

    def update_fft(self, ir_filtered, red_filtered, green_filtered):
        try:
            n = len(ir_filtered)
            if n < 2:
                return
            fs = 25.0  # PPG sampling rate is 25Hz
            
            fft_freqs = np.fft.rfftfreq(n, d=1.0/fs)
            
            # Calculate PSD for IR
            fft_ir_vals = np.fft.rfft(ir_filtered)
            psd_ir = (np.abs(fft_ir_vals) ** 2) / (fs * n)
            psd_ir[1:-1] *= 2
            self.fft_ir_curve.setData(fft_freqs, psd_ir)

            # Calculate PSD for Red
            fft_red_vals = np.fft.rfft(red_filtered)
            psd_red = (np.abs(fft_red_vals) ** 2) / (fs * n)
            psd_red[1:-1] *= 2
            self.fft_red_curve.setData(fft_freqs, psd_red)

            # Calculate PSD for Green
            fft_green_vals = np.fft.rfft(green_filtered)
            psd_green = (np.abs(fft_green_vals) ** 2) / (fs * n)
            psd_green[1:-1] *= 2
            self.fft_green_curve.setData(fft_freqs, psd_green)

            # Auto zoom FFT Y-axis excluding the DC component at index 0
            all_mags = []
            if len(psd_ir) > 1:
                all_mags.extend(psd_ir[1:])
            if len(psd_red) > 1:
                all_mags.extend(psd_red[1:])
            if len(psd_green) > 1:
                all_mags.extend(psd_green[1:])
                
            if len(all_mags) > 0:
                max_val = np.max(all_mags)
                # Avoid divide by zero/zero scaling
                if max_val <= 0:
                    max_val = 1.0
                self.fft_plot.getPlotItem().setYRange(0, max_val * 1.1, padding=0)
        except Exception as e:
            print("Error updating PPG FFT spectrum:", e)

    def update_region_color(self, ir_status_list, red_status_list, green_status_list):
        if green_status_list is None:
            green_status_list = ["N/A"] * 6
        elif isinstance(green_status_list, str):
            green_status_list = [green_status_list] * 6

        def get_brush_pen(status):
            if status == "Good":
                return pg.mkBrush(0, 200, 0, 70), pg.mkPen(color=(0, 200, 0, 180), width=2)
            elif status == "Fair":
                return pg.mkBrush(200, 200, 0, 70), pg.mkPen(color=(200, 200, 0, 180), width=2)
            elif status == "Poor":
                return pg.mkBrush(200, 0, 0, 70), pg.mkPen(color=(200, 0, 0, 180), width=2)
            else:
                return pg.mkBrush(150, 150, 150, 40), pg.mkPen(color=(150, 150, 150, 100), width=1)

        for i in range(6):
            combined_status = green_status_list[i] if i < len(green_status_list) else "N/A"

            brush, pen = get_brush_pen(combined_status)
            if i < len(self.ppg_regions):
                self.ppg_regions[i].setBrush(brush)
                for line in self.ppg_regions[i].lines:
                    line.setPen(pen)

    def update_motion_regions(self, is_moving):
        starts = []
        ends = []
        if len(is_moving) > 0:
            diff = np.diff(is_moving.astype(int))
            starts = np.where(diff == 1)[0] + 1
            ends = np.where(diff == -1)[0] + 1

            if is_moving[0]:
                starts = np.insert(starts, 0, 0)
            if is_moving[-1]:
                ends = np.append(ends, len(is_moving))

        # Position and display the required number of regions
        for idx, region in enumerate(self.motion_regions):
            if idx < len(starts):
                region.setRegion([starts[idx], ends[idx]])
                region.setVisible(True)
            else:
                region.setVisible(False)

        # Display the real-time "MOVING" badge at the top-center if hand is moving
        if len(is_moving) > 0 and is_moving[-1]:
            self.motion_label.setText("⚠️ MOVING")
            self.motion_label.setVisible(True)
            view_box = self.ppg_plot.getViewBox()
            y_range = view_box.viewRange()[1]
            ymax = y_range[1]
            ymin = y_range[0]
            self.motion_label.setPos(len(is_moving) / 2, ymax - (ymax - ymin) * 0.12)
        else:
            self.motion_label.setText("")
            self.motion_label.setVisible(False)