from imapclient import IMAPClient

class StatefulIMAPClient(IMAPClient):
    def __init__(self, host, *args, **kwargs):
        super().__init__(host, *args, **kwargs)
        self._idle_active = False

    def idle(self):
        if not self._idle_active:
            self._idle_active = True
            super().idle()

    def idle_done(self):
        if self._idle_active:
            self._idle_active = False
            super().idle_done()

    def is_idle(self):
        return self._idle_active

    def is_connection_alive(self):
        try:
            self.noop()
            return True
        except Exception:
            return False