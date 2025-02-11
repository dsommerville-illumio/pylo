import logging
import pylo

log = logging.getLogger('PYLO')


def init_logger():
    console_logger = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_logger.setFormatter(formatter)
    log.addHandler(console_logger)


init_logger()


def log_set_debug():
    log.setLevel(logging.DEBUG)


def log_set_info():
    log.setLevel(logging.INFO)


def log_set_warning():
    log.setLevel(logging.WARNING)


def get_logger():
    return log


def find_connector_or_die(obj):
    connector = obj.__dict__.get('connector')  # type: pylo.APIConnector
    if connector is None:
        owner = obj.__dict__.get('owner')
        if owner is None:
            raise Exception("Could not find a Connector object")
        return find_connector_or_die(owner)

    return connector


class IDTranslationTable:
    """docstring fo ID_TranslationTable."""

    def __init__(self):
        self.OldToNew = {}
        self.NewToOld = {}

        self.sourcesSorting = {}
        self.destSorting = {}

    def add_source(self, key, value):
        if key in self.sourcesSorting:
            raise Exception("Duplicate key '%s'" % key)
        self.sourcesSorting[key] = value

        find = self.destSorting.get(key)
        if find is None:
            return

        self.OldToNew[value] = find
        self.NewToOld[find] = value

    def add_destination(self, key, value):
        if key in self.destSorting:
            raise Exception("Duplicate key '%s'" % key)
        self.destSorting[key] = value

        find = self.sourcesSorting.get(key)
        if find is None:
            return

        self.OldToNew[find] = value
        self.NewToOld[value] = find

    def find_new(self, old):
        return self.OldToNew.get(old)

    def find_new_or_die(self, old):
        ret = self.OldToNew.get(old)
        if ret is None:
            raise Exception("Cannot find a match in the table for key '{}'".format(old))
        return ret

    def find_old(self, new):
        return self.NewToOld.get(new)

    def find_old_or_die(self, new):
        ret = self.NewToOld.get(new)
        if ret is None:
            raise Exception("Cannot find a match in the table for key {]".format(new))
        return ret

    def stats_to_str(self, padding = ''):
        msg = '{}source entries:{}\n{}destination entries:{}\n{}translation entries:{}'.\
            format( padding, len(self.sourcesSorting),
                    padding, len(self.destSorting),
                    padding, len(self.NewToOld))
        return msg

    def keys_old(self):
        return
