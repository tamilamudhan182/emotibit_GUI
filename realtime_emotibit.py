import time
from brainflow.board_shim import (
    BoardShim,
    BrainFlowInputParams,
    BoardIds,
    BrainFlowPresets
)

# Enable logs (optional)
BoardShim.enable_dev_board_logger()

# Create board
params = BrainFlowInputParams()
board = BoardShim(BoardIds.EMOTIBIT_BOARD.value, params)

try:
    print("Connecting to EmotiBit...")
    board.prepare_session()

    print("Starting stream...")
    board.start_stream()

    print("\nStreaming continuously...")
    print("Press Ctrl+C to stop.\n")

    while True:

        # IMU Data (Accelerometer + Gyroscope + Magnetometer)
        imu = board.get_current_board_data(
            1,
            preset=BrainFlowPresets.DEFAULT_PRESET
        )

        # PPG Data
        ppg = board.get_current_board_data(
            1,
            preset=BrainFlowPresets.AUXILIARY_PRESET
        )

        # EDA + Temperature
        anc = board.get_current_board_data(
            1,
            preset=BrainFlowPresets.ANCILLARY_PRESET
        )

        # Print latest IMU sample
        if imu.shape[1] > 0:
            sample = imu[:, -1]

            accel_x = sample[1]
            accel_y = sample[2]
            accel_z = sample[3]

            gyro_x = sample[4]
            gyro_y = sample[5]
            gyro_z = sample[6]

            mag_x = sample[7]
            mag_y = sample[8]
            mag_z = sample[9]

            print(
                f"ACCEL=({accel_x:.3f}, {accel_y:.3f}, {accel_z:.3f}) "
                f"GYRO=({gyro_x:.3f}, {gyro_y:.3f}, {gyro_z:.3f}) "
                f"MAG=({mag_x:.0f}, {mag_y:.0f}, {mag_z:.0f})"
            )

        # Print latest PPG sample
        if ppg.shape[1] > 0:
            sample = ppg[:, -1]

            ppg_ir = sample[1]
            ppg_red = sample[2]
            ppg_green = sample[3]

            print(
                f"PPG IR={ppg_ir:.0f} "
                f"RED={ppg_red:.0f} "
                f"GREEN={ppg_green:.0f}"
            )

        # Print latest EDA and Temperature sample
        if anc.shape[1] > 0:
            sample = anc[:, -1]

            eda = sample[1]
            temp1 = sample[2]
            temp2 = sample[3]

            print(
                f"EDA={eda:.3f} "
                f"TEMP1={temp1:.2f}°C "
                f"TEMP2={temp2:.2f}°C"
            )

        # Update rate
        time.sleep(0.1)

except KeyboardInterrupt:
    print("\nStopping stream...")

finally:
    try:
        board.stop_stream()
    except:
        pass

    board.release_session()
    print("Session closed.")