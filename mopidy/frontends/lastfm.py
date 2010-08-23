from mopidy.frontends.base import BaseFrontend

class LastfmFrontend(BaseFrontend):
    def __init__(self, *args, **kwargs):
        super(LastfmFrontend, self).__init__(*args, **kwargs)

    def start(self):
        pass

    def destroy(self):
        pass

    def process_message(self, message):
        pass
