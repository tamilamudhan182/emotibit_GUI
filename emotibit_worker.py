from brainflow.board_shim import (
    BoardShim,
    BoardIds,
    BrainFlowInputParams
)


class EmotiBitWorker:

    def __init__(self):

        params = BrainFlowInputParams()

        self.board = BoardShim(
            BoardIds.EMOTIBIT_BOARD.value,
            params
        )

    def connect(self):

        print("Connecting to EmotiBit...")

        self.board.prepare_session()
        self.board.start_stream()

    def disconnect(self):

        self.board.stop_stream()
        self.board.release_session()