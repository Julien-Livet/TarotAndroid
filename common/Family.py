from enum import Enum

class Family(Enum):
    Heart = 0
    Diamond = 1
    Club = 2
    Spade = 3

    def __int__(self) -> int:
        return self.value
    
    def imageName(self) -> str:
        if (self.value == 0):
            return "heart"
        elif (self.value == 1):
            return "diamond"
        elif (self.value == 2):
            return "club"
        elif (self.value == 3):
            return "spade"
        else:
            return ""

    def name(self) -> str:
        if (self.value == 0):
            return _("Heart")
        elif (self.value == 1):
            return _("Diamond")
        elif (self.value == 2):
            return _("Club")
        elif (self.value == 3):
            return _("Spade")
        else:
            return ""

    def __str__(self) -> str:
        return self.name()
