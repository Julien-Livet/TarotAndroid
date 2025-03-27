from enum import Enum

class Head(Enum):
    Jack = 0
    Knight = 1
    Queen = 2
    King = 3

    def __int__(self) -> int:
        return self.value
    
    def name(self) -> str:
        if (self.value == 0):
            return _("Jack")
        elif (self.value == 1):
            return _("Knight")
        elif (self.value == 2):
            return _("Queen")
        elif (self.value == 3):
            return _("King")
        else:
            return ""

    def __str__(self) -> str:
        return self.name()
