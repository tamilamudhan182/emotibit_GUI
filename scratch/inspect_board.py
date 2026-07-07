import brainflow
from brainflow.board_shim import BoardShim, BoardIds

board_id = BoardIds.EMOTIBIT_BOARD.value
print("Board ID:", board_id)

try:
    print("Accel channels:", BoardShim.get_accel_channels(board_id))
except Exception as e:
    print("Error getting Accel channels:", e)

try:
    print("Gyro channels:", BoardShim.get_gyro_channels(board_id))
except Exception as e:
    print("Error getting Gyro channels:", e)

try:
    print("EDA channel:", BoardShim.get_analog_channels(board_id))
except Exception as e:
    print("Error getting Analog channels:", e)

try:
    print("Temperature channels:", BoardShim.get_temperature_channels(board_id))
except Exception as e:
    print("Error getting Temperature channels:", e)
