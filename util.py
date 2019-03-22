import io
import threading


def start_thread(func, *args):
    thread = threading.Thread(target=func, args=args)
    thread.setDaemon(True)
    thread.start()
    return thread


class MyBytesIO(io.BytesIO):
    """BytesIO wrapper to keep buffer after close() is called."""

    def __init__(self) -> None:
        super().__init__()

    def close(self):
        pass

    def real_close(self):
        io.BytesIO.close(self)
