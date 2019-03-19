import threading


def start_thread(func, *args):
    thread = threading.Thread(target=func, args=args)
    thread.setDaemon(True)
    thread.start()
    return thread
