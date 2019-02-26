import logging

logging.basicConfig()
logger = logging.getLogger()


class Person(object):

    def __init__(self, data_row, column_idx_to_name):
        unknown_columns = []
        for n, column in enumerate(data_row):
            eval('self.{member} = {col}'.format(member=column_idx_to_name[n], col=column))
        if unknown_columns:
            logger.info("Unknown columns in data file: " + ', '.join(unknown_columns))
        self.validate()

    def validate(self):
        pass
