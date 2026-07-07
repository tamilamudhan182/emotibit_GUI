import numpy as np
from collections import deque
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

from brainflow.board_shim import (
    BoardShim,
    BrainFlowInputParams,
    BoardIds,
    BrainFlowPresets
)

# ==========================================================
# Connect to EmotiBit
# ==========================================================
params = BrainFlowInputParams()
board = BoardShim(BoardIds.EMOTIBIT_BOARD.value, params)

print("Connecting to EmotiBit...")
board.prepare_session()

print("Starting stream...")
board.start_stream()

# ==========================================================
# Buffer size
# ==========================================================
BUFFER_SIZE = 200

# Accelerometer
ax_buf = deque([0]*BUFFER_SIZE, maxlen=BUFFER_SIZE)
ay_buf = deque([0]*BUFFER_SIZE, maxlen=BUFFER_SIZE)
az_buf = deque([0]*BUFFER_SIZE, maxlen=BUFFER_SIZE)

# Gyroscope
gx_buf = deque([0]*BUFFER_SIZE, maxlen=BUFFER_SIZE)
gy_buf = deque([0]*BUFFER_SIZE, maxlen=BUFFER_SIZE)
gz_buf = deque([0]*BUFFER_SIZE, maxlen=BUFFER_SIZE)

# PPG
ir_buf = deque([0]*BUFFER_SIZE, maxlen=BUFFER_SIZE)
red_buf = deque([0]*BUFFER_SIZE, maxlen=BUFFER_SIZE)
green_buf = deque([0]*BUFFER_SIZE, maxlen=BUFFER_SIZE)

# EDA
eda_buf = deque([0]*BUFFER_SIZE, maxlen=BUFFER_SIZE)

# Temperature
temp1_buf = deque([0]*BUFFER_SIZE, maxlen=BUFFER_SIZE)
temp2_buf = deque([0]*BUFFER_SIZE, maxlen=BUFFER_SIZE)

# ==========================================================
# Create figure
# ==========================================================
fig, axs = plt.subplots(
    5,
    1,
    figsize=(16, 11),
    sharex=True
)

fig.suptitle(
    "Real-Time EmotiBit Dashboard",
    fontsize=20,
    fontweight='bold'
)

# ==========================================================
# Accelerometer
# ==========================================================
line_ax, = axs[0].plot([], [], linewidth=2, label='Accel X')
line_ay, = axs[0].plot([], [], linewidth=2, label='Accel Y')
line_az, = axs[0].plot([], [], linewidth=2, label='Accel Z')

axs[0].set_title("Accelerometer")
axs[0].set_ylabel("g")
axs[0].legend(loc='upper right')

# ==========================================================
# Gyroscope
# ==========================================================
line_gx, = axs[1].plot([], [], linewidth=2, label='Gyro X')
line_gy, = axs[1].plot([], [], linewidth=2, label='Gyro Y')
line_gz, = axs[1].plot([], [], linewidth=2, label='Gyro Z')

axs[1].set_title("Gyroscope")
axs[1].set_ylabel("deg/s")
axs[1].legend(loc='upper right')

# ==========================================================
# PPG
# ==========================================================
line_ir, = axs[2].plot([], [], linewidth=2, label='IR')
line_red, = axs[2].plot([], [], linewidth=2, label='Red')
line_green, = axs[2].plot([], [], linewidth=2, label='Green')

axs[2].set_title("PPG Signals")
axs[2].set_ylabel("Amplitude")
axs[2].legend(loc='upper right')

# ==========================================================
# EDA
# ==========================================================
line_eda, = axs[3].plot([], [], linewidth=2, label='EDA')

axs[3].set_title("Electrodermal Activity")
axs[3].set_ylabel("µS")
axs[3].legend(loc='upper right')

# ==========================================================
# Temperature
# ==========================================================
line_t1, = axs[4].plot([], [], linewidth=2, label='Temp1')
line_t2, = axs[4].plot([], [], linewidth=2, label='Temp2')

axs[4].set_title("Temperature")
axs[4].set_ylabel("°C")
axs[4].set_xlabel("Samples")
axs[4].legend(loc='upper right')

# ==========================================================
# Add grids
# ==========================================================
for ax in axs:
    ax.grid(True, linestyle='--', alpha=0.4)


# ==========================================================
# Update function
# ==========================================================
def update(frame):

    # IMU data
    imu = board.get_current_board_data(
        1,
        preset=BrainFlowPresets.DEFAULT_PRESET
    )

    # PPG data
    ppg = board.get_current_board_data(
        1,
        preset=BrainFlowPresets.AUXILIARY_PRESET
    )

    # EDA + Temperature
    anc = board.get_current_board_data(
        1,
        preset=BrainFlowPresets.ANCILLARY_PRESET
    )

    # ---------------- IMU ----------------
    if imu.shape[1] > 0:

        s = imu[:, -1]

        ax_buf.append(s[1])
        ay_buf.append(s[2])
        az_buf.append(s[3])

        gx_buf.append(s[4])
        gy_buf.append(s[5])
        gz_buf.append(s[6])

    # ---------------- PPG ----------------
    if ppg.shape[1] > 0:

        s = ppg[:, -1]

        ir_buf.append(s[1])
        red_buf.append(s[2])
        green_buf.append(s[3])

    # ---------------- EDA + TEMP ----------------
    if anc.shape[1] > 0:

        s = anc[:, -1]

        eda_buf.append(s[1])

        temp1_buf.append(s[2])
        temp2_buf.append(s[3])

    x = np.arange(BUFFER_SIZE)

    # Accelerometer
    line_ax.set_data(x, ax_buf)
    line_ay.set_data(x, ay_buf)
    line_az.set_data(x, az_buf)

    # Gyroscope
    line_gx.set_data(x, gx_buf)
    line_gy.set_data(x, gy_buf)
    line_gz.set_data(x, gz_buf)

    # PPG
    line_ir.set_data(x, ir_buf)
    line_red.set_data(x, red_buf)
    line_green.set_data(x, green_buf)

    # EDA
    line_eda.set_data(x, eda_buf)

    # Temperature
    line_t1.set_data(x, temp1_buf)
    line_t2.set_data(x, temp2_buf)

    # Auto-scale all plots
    for ax in axs:
        ax.relim()
        ax.autoscale_view()

    return (
        line_ax, line_ay, line_az,
        line_gx, line_gy, line_gz,
        line_ir, line_red, line_green,
        line_eda,
        line_t1, line_t2
    )


# ==========================================================
# Start animation
# ==========================================================
ani = FuncAnimation(
    fig,
    update,
    interval=50,
    cache_frame_data=False
)

plt.tight_layout(rect=[0, 0, 1, 0.97])

try:
    plt.show()

finally:
    board.stop_stream()
    board.release_session()
    print("Session closed.")