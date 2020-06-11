#!/usr/bin/env python3

import logging.config
import sys

import app_config

ATTRIBUTION = 'Icon made by Freepik from www.flaticon.com'

LOG_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'simple': {
            'format': '%(asctime)s %(name)s:%(funcName)s:%(lineno)d %(threadName)s %(levelname)-7s %(message)s',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'level': 'DEBUG',
            'formatter': 'simple',
            'stream': 'ext://sys.stdout',
        },
        'info_file_handler': {
            'class': 'logging.handlers.RotatingFileHandler',
            'level': 'DEBUG',
            'formatter': 'simple',
            'filename': app_config.LOG_PATH,
            'maxBytes': 1048576,
            'backupCount': 5,
            'encoding': 'utf8',
        },
    },
    'loggers': {
        'classinvoices': {
            'level': 'DEBUG',
            'handlers': ['console', 'info_file_handler'],
            'propagate': False,
        },
    },
    'root': {
        'level': 'INFO',
        'handlers': ['console', 'info_file_handler'],
    },
}


class StreamToLogger(object):
    """
    Fake file-like stream object that redirects writes to a logger instance.
    """

    def __init__(self, logger, log_level=logging.INFO):
        self.logger = logger
        self.log_level = log_level
        self.linebuf = ''

    def write(self, buf):
        for line in buf.rstrip().splitlines():
            self.logger.log(self.log_level, line.rstrip())

    def flush(self):
        pass

def redirect_stdout_stderr():
    """Redirect stdout and stderr to the log."""
    stdout_logger = logging.getLogger('STDOUT')
    sys.stdout = StreamToLogger(stdout_logger, logging.INFO)

    stderr_logger = logging.getLogger('STDERR')
    sys.stderr = StreamToLogger(stderr_logger, logging.ERROR)


def main():
    # Set up logging before any other imports to have the best change of debugging
    # start up problems.
    logging.config.dictConfig(LOG_CONFIG)
    redirect_stdout_stderr()

    import wx
    app = wx.App()

    # Need to create config after wx.App() constructor
    app_config.create_config()

    import ui.MainFrame
    frame = ui.MainFrame(None,
                         title=app_config.APP_NAME,
                         size=ui.MainFrame.DEFAULT_SIZE)
    frame.Show()
    app.MainLoop()


if __name__ == '__main__':
    try:
        main()
    except Exception:
        logging.getLogger().exception('unhandled application error')
