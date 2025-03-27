from common import Family
from common import Head

class FamilyCard:
    def __init__(self, family: Family, head: Head = None, value: int = None):
        self._family = family
        self._value = value
        self._head = head
        assert((self._value and self._head == None)
               or (self._value == None and self._head))
        if (self._value):
            assert(1 <= self._value and self._value <= 10)
    
    def isFamily(self, family: Family) -> bool:
        return self._family == family

    def family(self) -> Family:
        return self._family
        
    def name(self) -> str:
        s = ""

        if (self.value() == 1):
            if (self._family == Family.Family.Heart):
                s = _("Ace of hearts")
            elif (self._family == Family.Family.Diamond):
                s = _("Ace of diamonds")
            elif (self._family == Family.Family.Club):
                s = _("Ace of clubs")
            elif (self._family == Family.Family.Spade):
                s = _("Ace of spade")
        elif (self.value() <= 10):
            if (self._family == Family.Family.Heart):
                s = _("Heart {0}").format(self.value())
            elif (self._family == Family.Family.Diamond):
                s = _("Diamond {0}").format(self.value())
            elif (self._family == Family.Family.Club):
                s = _("Club {0}").format(self.value())
            elif (self._family == Family.Family.Spade):
                s = _("Spade {0}").format(self.value())
        elif (self.value() == 11):
            if (self._family == Family.Family.Heart):
                s = _("Heart jack")
            elif (self._family == Family.Family.Diamond):
                s = _("Diamond jack")
            elif (self._family == Family.Family.Club):
                s = _("Club jack")
            elif (self._family == Family.Family.Spade):
                s = _("Spade jack")
        elif (self.value() == 12):
            if (self._family == Family.Family.Heart):
                s = _("Heart knight")
            elif (self._family == Family.Family.Diamond):
                s = _("Diamond knight")
            elif (self._family == Family.Family.Club):
                s = _("Club knight")
            elif (self._family == Family.Family.Spade):
                s = _("Spade knight")
        elif (self.value() == 13):
            if (self._family == Family.Family.Heart):
                s = _("Heart queen")
            elif (self._family == Family.Family.Diamond):
                s = _("Diamond queen")
            elif (self._family == Family.Family.Club):
                s = _("Club queen")
            elif (self._family == Family.Family.Spade):
                s = _("Spade queen")
        else: #elif (self.value() == 14):
            if (self._family == Family.Family.Heart):
                s = _("Heart king")
            elif (self._family == Family.Family.Diamond):
                s = _("Diamond king")
            elif (self._family == Family.Family.Club):
                s = _("Club king")
            elif (self._family == Family.Family.Spade):
                s = _("Spade king")

        return s

    def imageName(self) -> str:
        s = ""
        
        if (self._family == Family.Family.Heart):
            s = "heart"
        elif (self._family == Family.Family.Diamond):
            s = "diamond"
        elif (self._family == Family.Family.Club):
            s = "club"
        elif (self._family == Family.Family.Spade):
            s = "spade"
            
        return s + "-" + str(self.value())

    def value(self) -> int:
        if (self._head):
            return 11 + int(self._head)
        else:
            return self._value
            
    def points(self) -> int:
        if (self._value):
            return 0.5
        else:
            return int(self._head) + 1 + 0.5

    def __int__(self) -> int:
        return self.value()

    def __str__(self) -> str:
        return self.name()
