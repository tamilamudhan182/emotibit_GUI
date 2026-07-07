import brainflow
from brainflow.board_shim import BoardShim, BoardIds, BrainFlowPresets
import json

board_id = BoardIds.EMOTIBIT_BOARD.value

for preset in [BrainFlowPresets.DEFAULT_PRESET, BrainFlowPresets.AUXILIARY_PRESET, BrainFlowPresets.ANCILLARY_PRESET]:
    try:
        descr = BoardShim.get_board_descr(board_id, preset)
        print(f"Preset {preset} descriptor:")
        print(json.dumps(descr, indent=2))
    except Exception as e:
        print(f"Error getting preset {preset} descriptor:", e)
