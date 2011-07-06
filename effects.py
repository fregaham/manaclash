
class Effect:
    pass

class ContinuousEffect(Effect):
    def __init__ (self, types):
        self.types = types
        self.timestamp = None

    def apply (self):
        pass


