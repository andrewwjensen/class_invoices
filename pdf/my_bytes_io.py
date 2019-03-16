import io


class MyBytesIO(io.BytesIO):
    """BytesIO wrapper to keep buffer after close() is called."""

    def __init__(self) -> None:
        super().__init__()

    def close(self):
        pass

    def real_close(self):
        io.BytesIO.close(self)