import io
import threading

import wx


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


def start_progress(progress_dialog, thread_func, *thread_args):
    """Start thread in background while managing progress dialog.
    Needed because Windows behaves differently, so we handle that case."""
    if wx.GetOsVersion()[0] & wx.OS_WINDOWS:
        # On Windows, the progress dialog ShowModal() returns immediately, so don't run in
        # separate thread.
        thread_func(progress_dialog, *thread_args)
    else:
        start_thread(thread_func, progress_dialog, *thread_args)
        # The following will only return once the thread destroys the dialog
        progress_dialog.ShowModal()
