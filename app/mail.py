class EMail():
    def __init__(self, uid, msg):
        self.uid = uid
        self.msg = msg        

    def get_sender(self):
        return self.msg['From']
    
    def extract_recipient(self):
        """Versucht, die ursprüngliche Zieladresse aus der Mail zu extrahieren."""
        for header in ['X-Original-To', 'Delivered-To', 'Envelope-To', 'To']:
            value = self.msg.get(header)
            if value:
                return value.split(',')[0].strip()
        return None 
