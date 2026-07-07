import time
import pandas as pd
from brainflow.board_shim import BrainFlowPresets


def realtime_stream(board, save_csv=False):
    """
    Stream EmotiBit data continuously in real time.
    Press Ctrl+C to stop.
    """

    try:
        board.start_stream()

        print("\nStreaming EmotiBit data...\n")

        while True:
            # Get only newly available samples
            data_default = board.get_current_board_data(
                10, preset=BrainFlowPresets.DEFAULT_PRESET
            )

            data_aux = board.get_current_board_data(
                10, preset=BrainFlowPresets.AUXILIARY_PRESET
            )

            data_anc = board.get_current_board_data(
                10, preset=BrainFlowPresets.ANCILLARY_PRESET
            )

            # Check if data exists
            if data_default.shape[1] > 0:

                accel_x = data_default[1][-1]
                accel_y = data_default[2][-1]
                accel_z = data_default[3][-1]

                gyro_x = data_default[4][-1]
                gyro_y = data_default[5][-1]
                gyro_z = data_default[6][-1]

                print(
                    f"Accel: ({accel_x:.3f}, {accel_y:.3f}, {accel_z:.3f}) "
                    f"| Gyro: ({gyro_x:.3f}, {gyro_y:.3f}, {gyro_z:.3f})"
                )

            if data_aux.shape[1] > 0:
                ppg_ir = data_aux[1][-1]
                ppg_red = data_aux[2][-1]
                ppg_green = data_aux[3][-1]

                print(
                    f"PPG IR={ppg_ir:.0f}, "
                    f"RED={ppg_red:.0f}, "
                    f"GREEN={ppg_green:.0f}"
                )

            if data_anc.shape[1] > 0:
                eda = data_anc[1][-1]
                temp1 = data_anc[2][-1]

                print(
                    f"EDA={eda:.3f} | Temp={temp1:.2f}°C"
                )

            # Optional CSV logging
            if save_csv and data_default.shape[1] > 0:
                df = pd.DataFrame(data_default.T)
                df.to_csv(
                    "realtime_data.csv",
                    mode='a',
                    header=False,
                    index=False
                )

            time.sleep(0.1)

    except KeyboardInterrupt:
        print("\nStopping stream...")

    finally:
        board.stop_stream()
        board.release_session()
        print("Session closed.")