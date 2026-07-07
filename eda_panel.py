from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QButtonGroup, QLabel, QLineEdit
import pyqtgraph as pg
import numpy as np


class EDAPanel(QWidget):

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

        # Filter Cutoff manual input
        self.lbl_cutoff = QLabel("Filter Cutoff (Hz):")
        self.lbl_cutoff.setStyleSheet("color: #ffffff; font-size: 13px; font-weight: bold; margin-left: 15px;")
        
        self.cutoff_input = QLineEdit("2.0")
        self.cutoff_input.setStyleSheet("""
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

        btn_layout.addWidget(self.lbl_cutoff)
        btn_layout.addWidget(self.cutoff_input)
        btn_layout.addStretch()

        layout.addLayout(btn_layout)

        # ====================================
        # PLOTS SETUP (EDA Time Domain & EDA FFT)
        # ====================================
        self.eda_plot = pg.PlotWidget(title="Electrodermal Activity (EDA)")
        self.fft_plot = pg.PlotWidget(title="EDA FFT Spectrum")

        # Configure time domain EDA plot
        plot_item = self.eda_plot.getPlotItem()
        view_box = plot_item.getViewBox()
        plot_item.showGrid(x=True, y=True, alpha=0.3)
        plot_item.addLegend()
        plot_item.setLabel('left', 'EDA (µS)')
        plot_item.setLabel('bottom', 'Samples')
        # pyrefly: ignore [bad-keyword-argument]
        plot_item.setXRange(0, 300, padding=0)
        plot_item.setClipToView(True)
        view_box.setMouseEnabled(x=True, y=True)
        view_box.enableAutoRange(axis=pg.ViewBox.YAxis, enable=False)

        # Configure frequency domain FFT plot
        fft_plot_item = self.fft_plot.getPlotItem()
        fft_view_box = fft_plot_item.getViewBox()
        fft_plot_item.showGrid(x=True, y=True, alpha=0.3)
        fft_plot_item.addLegend()
        fft_plot_item.setLabel('left', 'PSD (µS²/Hz)')
        fft_plot_item.setLabel('bottom', 'Frequency (Hz)')
        # pyrefly: ignore [bad-keyword-argument]
        fft_plot_item.setXRange(0, 5.0, padding=0)
        fft_plot_item.setClipToView(True)
        fft_view_box.setMouseEnabled(x=True, y=True)
        fft_view_box.enableAutoRange(axis=pg.ViewBox.YAxis, enable=False)

        # ====================================
        # 10 OVERLAY SEGMENTS SPANNING 300 SAMPLES
        # ====================================
        self.eda_regions = []
        for i in range(10):
            region = pg.LinearRegionItem(
                values=[i * 30, (i + 1) * 30],
                brush=pg.mkBrush(150, 150, 150, 40),
                pen=pg.mkPen(color=(150, 150, 150, 100), width=1),
                movable=False
            )
            plot_item.addItem(region)
            self.eda_regions.append(region)

        # ====================================
        # RAW CURVE (Thin, red)
        # ====================================
        self.eda_raw_curve = plot_item.plot(
            pen=pg.mkPen('r', width=1),
            name='EDA Raw'
        )

        # ====================================
        # FILTERED CURVE (Thick, bright yellow)
        # ====================================
        self.eda_curve = plot_item.plot(
            pen=pg.mkPen('y', width=2),
            name='EDA Filter'
        )

        # ====================================
        # FFT SPECTRUM CURVE
        # ====================================
        self.fft_curve = fft_plot_item.plot(
            pen=pg.mkPen('y', width=2),
            name='EDA FFT'
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
        plots_layout.addWidget(self.eda_plot, stretch=7)
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
            self.eda_plot.addItem(region)
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
        self.eda_plot.addItem(self.motion_label)

    def update_fft(self, eda_filtered):
        try:
            n = len(eda_filtered)
            if n < 2:
                return
            fs = 15.0  # EDA sampling rate is 15Hz
            
            # Calculate PSD
            fft_vals = np.fft.rfft(eda_filtered)
            fft_freqs = np.fft.rfftfreq(n, d=1.0/fs)
            psd = (np.abs(fft_vals) ** 2) / (fs * n)
            psd[1:-1] *= 2
            
            # Update FFT curve
            self.fft_curve.setData(fft_freqs, psd)
            
            # Auto zoom Y-axis excluding the DC component at index 0
            if len(psd) > 1:
                max_val = np.max(psd[1:])
                if max_val <= 0:
                    max_val = 1.0
                self.fft_plot.getPlotItem().setYRange(0, max_val * 1.1, padding=0)
        except Exception as e:
            print("Error updating EDA FFT spectrum:", e)

    def set_raw_mode(self):
        self.show_mode = "raw"
        # Hide filtered curve
        self.eda_curve.setVisible(False)
        # Show raw curve
        self.eda_raw_curve.setVisible(True)

    def set_filtered_mode(self):
        self.show_mode = "filtered"
        # Show both curves
        self.eda_curve.setVisible(True)
        self.eda_raw_curve.setVisible(True)

    # ====================================
    # 🔥 AUTO ZOOM FUNCTION (USED BY SIGNAL_PANEL)
    # ====================================
    def update_auto_zoom(self, raw_signal, filt_signal):

        try:
            if self.show_mode == "raw":
                all_data = raw_signal
            else:
                all_data = np.concatenate([raw_signal, filt_signal])

            all_data_clean = all_data[np.isfinite(all_data)]
            if len(all_data_clean) == 0:
                return

            ymin = np.min(all_data_clean)
            ymax = np.max(all_data_clean)

            # prevent flat-line crash
            if ymin == ymax:
                ymin -= 0.005
                ymax += 0.005

            margin = (ymax - ymin) * 0.15

            if margin < 0.001:
                margin = 0.001

            self.eda_plot.getPlotItem().setYRange(
                ymin - margin,
                ymax + margin
            )

        except Exception as e:
            print("EDA auto zoom error:", e)

    def update_region_color(self, status_list):
        if status_list is None:
            status_list = ["N/A"] * 10
        elif isinstance(status_list, str):
            status_list = [status_list] * 10
            
        for i in range(10):
            if i < len(status_list):
                status = status_list[i]
            else:
                status = "N/A"
                
            if status == "Good":
                brush = pg.mkBrush(0, 200, 0, 70)
                pen = pg.mkPen(color=(0, 200, 0, 180), width=2)
            elif status == "Fair":
                brush = pg.mkBrush(200, 200, 0, 70)
                pen = pg.mkPen(color=(200, 200, 0, 180), width=2)
            elif status == "Poor":
                brush = pg.mkBrush(200, 0, 0, 70)
                pen = pg.mkPen(color=(200, 0, 0, 180), width=2)
            else:
                brush = pg.mkBrush(150, 150, 150, 40)
                pen = pg.mkPen(color=(150, 150, 150, 100), width=1)
                
            if i < len(self.eda_regions):
                self.eda_regions[i].setBrush(brush)
                for line in self.eda_regions[i].lines:
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
            view_box = self.eda_plot.getViewBox()
            y_range = view_box.viewRange()[1]
            ymax = y_range[1]
            ymin = y_range[0]
            self.motion_label.setPos(len(is_moving) / 2, ymax - (ymax - ymin) * 0.12)
        else:
            self.motion_label.setText("")
            self.motion_label.setVisible(False)