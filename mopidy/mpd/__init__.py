class MpdAckError(Exception):
    pass

class MpdNotImplemented(MpdAckError):
    def __init__(self, *args):
        super(MpdNotImplemented, self).__init__(u'Not implemented', *args)
