class MpdAckError(Exception):
    def __init__(self, msg):
        self.msg = msg

class MpdNotImplemented(MpdAckError):
    def __init__(self):
        super(MpdNotImplemented, self).__init__(u'Not implemented')
