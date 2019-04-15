import io
import threading

import wx

PROGRESS_STYLE = wx.PD_SMOOTH | wx.PD_APP_MODAL | wx.PD_ELAPSED_TIME | wx.PD_CAN_ABORT | wx.PD_AUTO_HIDE


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
