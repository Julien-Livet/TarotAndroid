from enum import Enum

class Contract(Enum):
    Little = 0
    Guard = 1
    GuardWithout = 2
    GuardAgainst = 3
    
    def __int__(self) -> int:
        return self.value
    
    def name(self) -> str:
        if (self.value == 0):
            return _("Little")
        elif (self.value == 1):
            return _("Guard")
        elif (self.value == 2):
            return _("Guard without")
        elif (self.value == 3):
            return _("Guard against")
        else:
            return ""

    def __str__(self) -> str:
        return self.name()
