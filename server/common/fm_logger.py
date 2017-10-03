import logging
import inspect
import traceback

from server.common import constants

class Logging():
    
    def __init__(self):
        logging.basicConfig(filename=constants.LOG_FILE_NAME,
                            level=logging.DEBUG, filemode='a',
                            format='%(asctime)s %(message)s',
                            datefmt='%m/%d/%Y %I:%M:%S %p')
        self.logger = logging.getLogger("CloudARK")

    # http://stackoverflow.com/questions/10973362/python-logging-function-name-file-name-line-number-using-a-single-file
    def info(self, message):
        # Get the previous frame in the stack, otherwise it would
        # be this function!!!
        try:
            func = inspect.currentframe().f_back.f_code
            # Dump the message + the name of this function to the log.
            self.logger.info("<%s>: %s() %s:%i" % (
                message,
                func.co_name,
                func.co_filename,
                func.co_firstlineno
            ))
        except IOError as e:
            if e.errno == 28:
                print("-- Disk full -- (most likely this also won't get printed.")

    def debug(self, message):
        # Get the previous frame in the stack, otherwise it would
        # be this function!!!
        try:
            func = inspect.currentframe().f_back.f_code
            # Dump the message + the name of this function to the log.
            self.logger.debug("<%s>: %s() %s:%i" % (
                message,
                func.co_name,
                func.co_filename,
                func.co_firstlineno
            ))
        except IOError as e:
            if e.errno == 28:
                print("-- Disk full -- (most likely this also won't get printed.")

    def error(self, message):

        # Get the previous frame in the stack, otherwise it would
        # be this function!!!

        try:
            func = inspect.currentframe().f_back.f_code
            # Dump the message + the name of this function to the log.
            self.logger.error("<%s>: %s() %s:%i" % (
                message,
                func.co_name,
                func.co_filename,
                func.co_firstlineno
            ))

            self.logger.error(message, exc_info=1)

        except IOError as e:
            if e.errno == 28:
                print("-- Disk full -- (most likely this also won't get printed.")
