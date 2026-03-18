import datetime

class SystemTime:
    def __init__(self):
        self.current_time = datetime.datetime.now()
    
    def get_current_time(self):
        return self.current_time