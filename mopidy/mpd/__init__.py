from mopidy import MopidyException

class MpdAckError(MopidyException):
    pass

class MpdNotImplemented(MpdAckError):
    def __init__(self):
        super(MpdNotImplemented, self).__init__(u'Not implemented')
