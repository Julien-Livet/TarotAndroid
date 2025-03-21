from enum import Enum
from functools import partial
import gettext
import io
import kivy.app
import kivy.clock
import kivy.core
import kivy.core.image
import kivy.core.window
import kivy.graphics
import kivy.logger
import kivy.resources
import kivy.uix
import kivy.uix.boxlayout
import kivy.uix.button
import kivy.uix.image
import kivy.uix.label
import kivy.uix.popup
import kivy.uix.spinner
import locale
import math
import os
from PIL import Image, ImageDraw, ImageFont
import random
import sys
import time
import threading

overCardRatio = 1 / 3
globalRatio = 1

assert(0 < overCardRatio and overCardRatio <= 1)

cardSize = (0, 0)

class TableLabel(kivy.uix.image.Image):
    def __init__(self, window, image: Image = None):
        super().__init__()
        self._window = window
        self.setImage(image)
        self._mousePressPos = None
        self._pressed = False
        self.img = None
    
    def setImage(self, image: Image):
        self._image = image
        
        if (image):
            self.img_byte_arr = io.BytesIO()
            image.save(self.img_byte_arr, format='PNG')
            self.img_byte_arr.seek(0)
            self.img = kivy.core.image.Image(self.img_byte_arr, ext="png")
            self.texture = self.img.texture
            self.size = self.img.texture.size
            self.size_hint = (None, None)

    def imageWidth(self):
        if (not self.img):
            return 0
            
        return self.img.texture.size[0]

    def imageHeight(self):
        if (not self.img):
            return 0
            
        return self.img.texture.size[1]

    def on_touch_up(self, touch):
        super().on_touch_up(touch)
        if (not self._pressed):
            p = self.to_window(touch.x, touch.y)
            self._mousePressPos = [p[0], self._window.height - p[1]]
        else:
            self._mousePressPos = None

    def on_touch_down(self, touch):
        super().on_touch_down(touch)
        self._mousePressPos = None
        self._pressed = False

class Window(kivy.uix.boxlayout.BoxLayout):
    def __init__(self, app: kivy.app.App):
        super().__init__(orientation = "horizontal", spacing = 0)
        self._playerNumber = 5
        self._window = None
        self._dialog = None
        self._ok = False
        self._app = app

        layout = kivy.uix.boxlayout.BoxLayout(orientation = "vertical")

        threeButton = kivy.uix.button.Button(text = _("Three players"))
        threeButton.bind(on_press = self.threePlayers)
        fourButton = kivy.uix.button.Button(text = _("Four players"))
        fourButton.bind(on_press = self.fourPlayers)
        fiveButton = kivy.uix.button.Button(text = _("Five players"))
        fiveButton.bind(on_press = self.fivePlayers)

        layout.add_widget(threeButton)
        layout.add_widget(fourButton)
        layout.add_widget(fiveButton)

        self.add_widget(layout)

    def setOpacity(self, widget, opacity, *largs):
        widget.opacity = opacity

    def setSpinnerValues(self, spinner, values, *largs):
        spinner.values = values
        spinner.text = values[0]

    def removeSpinnerValues(self, spinner, *largs):
        self._rightLayout.remove_widget(spinner)

    def threePlayers(self, instance):
        self._playerNumber = 3
        self.play()

    def fourPlayers(self, instance):
        self._playerNumber = 4
        self.play()

    def fivePlayers(self, instance):
        self._playerNumber = 5
        self.play()

    def displayTable(self, centerCards: list, displayCenterCards: bool, centerCardsIsDog: bool, *largs):
        self._tableLabel.setImage(self._game.tableImage(self._showPlayers, centerCards, displayCenterCards, centerCardsIsDog))

    def comboBoxActivated(self, spinner, text):
        for i in range(0, 6):
            if (self._dogComboBoxes[i] == spinner):
                self._dogIndex = i
                break

    def play(self):
        global globalRatio

        if (self._playerNumber == 3):
            globalRatio = 1.0
        elif (self._playerNumber == 4):
            globalRatio = 1.2
        elif (self._playerNumber == 5):
            globalRatio = 1.5
        
        globalRatio = 1.5 * kivy.core.window.Window.width / kivy.core.window.Window.height
        
        global cardSize
            
        cardSize = (int(56 * globalRatio), int(109 * globalRatio))

        self._game = Game(self._playerNumber)
        self._game.giveHands()
        self._game._players[0]._isHuman = True
        self._showPlayers = [False for i in range(0, self._playerNumber)]
        self._showPlayers[0] = True #self._showPlayers[random.randrange(self._playerNumber)] = True

        self.clear_widgets()

        self._tableLabel = TableLabel(self)
        self._tableLabel.padding = (0, 0, 0, 0)
        self._pointsLabel = kivy.uix.label.Label(text = _("Attack points: 0 - Defence points: 0"), halign = 'center', valign = 'middle')

        self._contractLabel = kivy.uix.label.Label(text = _("Choose a contract"), halign = 'center', valign = 'middle')
        self._contractLabel.opacity = 0
        self._contractComboBox = kivy.uix.spinner.Spinner()
        self._contractComboBox.opacity = 0

        choices = []

        for i in range(0, 4):
            choices.append(str(Family(i)))

        self._kingLabel = kivy.uix.label.Label(text = _("Call a king"), halign = 'center', valign = 'middle')
        self._kingLabel.opacity = 0
        self._kingComboBox = kivy.uix.spinner.Spinner(text = choices[0], values = choices)
        self._kingComboBox.opacity = 0

        self._dogLabel = kivy.uix.label.Label(text = _("Do a dog"), halign = 'center', valign = 'middle')
        self._dogLabel.opacity = 0
        self._dogComboBoxes = []
        for i in range(0, 6):
            self._dogComboBoxes.append(kivy.uix.spinner.Spinner())
            self._dogComboBoxes[-1].opacity = 0
            self._dogComboBoxes[-1].bind(on_text = self.comboBoxActivated)

        self._cardLabel = kivy.uix.label.Label(text = _("Play a card"), halign = 'center', valign = 'middle')
        self._cardLabel.opacity = 0
        self._cardComboBox = kivy.uix.spinner.Spinner()
        self._cardComboBox.opacity = 0

        okButton = kivy.uix.button.Button(text = _("OK"))
        okButton.bind(on_press = self.ok)

        self._rightLayout = kivy.uix.boxlayout.BoxLayout(orientation = "vertical", size_hint_x = None, width = kivy.core.window.Window.width / 4, spacing = 0)
        self._rightLayout.add_widget(self._contractLabel)
        self._rightLayout.add_widget(self._contractComboBox)
        self._rightLayout.add_widget(self._kingLabel)
        self._rightLayout.add_widget(self._kingComboBox)
        self._rightLayout.add_widget(self._dogLabel)
        self._dogIndex = 0
        for i in range(0, 6):
            self._rightLayout.add_widget(self._dogComboBoxes[i])
        self._rightLayout.add_widget(self._cardLabel)
        self._rightLayout.add_widget(self._cardComboBox)
        self._rightLayout.add_widget(okButton)

        layout = kivy.uix.boxlayout.BoxLayout(orientation = "vertical", spacing = 0)

        layout.add_widget(self._tableLabel)
        layout.add_widget(self._pointsLabel)
        self.add_widget(layout)        
        self.add_widget(self._rightLayout)

        kivy.clock.Clock.schedule_interval(self.monitor, 0)
        
        self._thread = threading.Thread(target = self._game.play, args = (self, ), daemon = True)
        self._thread.start()

    def ok(self, instance):
        self._ok = True
        
    def monitor(self, dt):
        take = ""
        
        if (self._game._calledKing):
            take = _("\nCalled king: ") \
                   + str(self._game._calledKing)

        if (self._game._contract):
            take += _("\nContract: ") \
                    + str(self._game._contract) \
                    + _(" ({0} points)") \
                    .format(self._game.attackTargetPoints())
    
        self._pointsLabel.text = _("Attack points: {0} - Defence points: {1}").format(self._game.attackPoints(), self._game.defencePoints()) + take
                                  
        if (self._tableLabel._mousePressPos):
            if (self._game._currentPlayer != None and self._game._players[self._game._currentPlayer]._isHuman):
                n = len(self._game._players[self._game._currentPlayer]._cards)
                w = (n - 1) * cardSize[0] * overCardRatio + cardSize[0]

                for j in range(0, n):
                    p = (self._tableLabel._mousePressPos[0] - (self._tableLabel.imageWidth() - w) // 2,
                         self._tableLabel._mousePressPos[1] - (self._tableLabel.imageHeight() - cardSize[1]))
                
                    rect = kivy.graphics.Rectangle(pos = (int(j * cardSize[0] * overCardRatio), 0),
                                                   size = (cardSize[0] * (1 if j == n - 1 else overCardRatio), cardSize[1]))

                    if (rect.pos[0] <= p[0] and p[0] <= rect.pos[0] + rect.size[0]
                        and rect.pos[1] <= p[1] and p[1] <= rect.pos[1] + rect.size[1]):
                        pass
                        enabledCards = []
                    
                        enabledCards = self._game._players[self._game._currentPlayer].enabledCards(self._game._centerCards,
                                                                                                   self._game._firstRound,
                                                                                                   self._game._calledKing,
                                                                                                   self._dogLabel.opacity == 1)

                        if (enabledCards[j]):
                            if (self._cardComboBox.opacity == 1):
                                self._cardComboBox.text = self._game._players[self._game._currentPlayer]._cards[j].name()
                            elif (self._dogLabel.opacity == 1):
                                self._tableLabel._mousePressPos = None
                                self._dogComboBoxes[self._dogIndex].text = self._game._players[self._game._currentPlayer]._cards[j].name()
                                self._dogIndex += 1
                                if (not self._dogComboBoxes[self._dogIndex].opacity == 1):
                                    self._dogIndex = 0
                        
                        break
    
        if (not self._thread.is_alive()):
            if (self._game.attackPoints() == 0
                and self._game.defencePoints() == 0):
                self._content = kivy.uix.boxlayout.BoxLayout(orientation = 'vertical')
                self._content.add_widget(kivy.uix.label.Label(text = _("Nobody takes!")))
                self._content.bind(on_touch_down = self.on_popup_ok)
                self._popup = kivy.uix.popup.Popup(title = _("Game over"), content = self._content)
                self._popup.open()
            else:
                if (self._game.attackWins()):
                    self._content = kivy.uix.boxlayout.BoxLayout(orientation = 'vertical')
                    self._content.bind(on_touch_down = self.on_popup_ok)
                    self._content.add_widget(kivy.uix.label.Label(text = _("Attack wins ({0} points for {1} points)!")
                                                                           .format(self._game.attackPoints(),
                                                                                   self._game.attackTargetPoints())))
                    self._popup = kivy.uix.popup.Popup(title = _("Game over"),
                                                       content = self._content)
                    self._popup.open()
                else:
                    self._content = kivy.uix.boxlayout.BoxLayout(orientation = 'vertical')
                    self._content.bind(on_touch_down = self.on_popup_ok)
                    self._content.add_widget(kivy.uix.label.Label(text = _("Attack loses ({0} points for {1} points)!")
                                                                           .format(self._game.attackPoints(),
                                                                                   self._game.attackTargetPoints())))
                    self._popup = kivy.uix.popup.Popup(title = _("Game over"),
                                                       content = self._content)
                    self._popup.open()

    def on_popup_ok(self, instance, touch):
        self._app.stop()

class App(kivy.app.App):
    def build(self):
        kivy.core.window.Window.orientation = 'landscape'
        
        return Window(self)

class Asset:
    def __init__(self, value: int):
        self._value = value
        assert(0 <= self._value and self._value <= 21)
    
    def isFool(self) -> bool:
        return self._value == 0
    
    def isOudler(self) -> bool:
        return self._value == 0 or self._value == 1 or self._value == 21
        
    def value(self) -> int:
        return self._value

    def points(self) -> int:
        if (self.isOudler()):
            return 4.5
        else:
            return 0.5
    
    def __int__(self) -> int:
        return self.value()

    def name(self) -> str:
        if (self.value() == 0):
            return _("Fool")
            
        return _("Asset {0}").format(self.value())

    def imageName(self) -> str:
        return "asset-"+ str(self.value())

    def __str__(self) -> str:
        return self.name()

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

class Family(Enum):
    Heart = 0
    Diamond = 1
    Club = 2
    Spade = 3

    def __int__(self) -> int:
        return self.value
    
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
            if (self._family == Family.Heart):
                s = _("Ace of hearts")
            elif (self._family == Family.Diamond):
                s = _("Ace of diamonds")
            elif (self._family == Family.Club):
                s = _("Ace of clubs")
            elif (self._family == Family.Spade):
                s = _("Ace of spade")
        elif (self.value() <= 10):
            if (self._family == Family.Heart):
                s = _("Heart {0}").format(self.value())
            elif (self._family == Family.Diamond):
                s = _("Diamond {0}").format(self.value())
            elif (self._family == Family.Club):
                s = _("Club {0}").format(self.value())
            elif (self._family == Family.Spade):
                s = _("Spade {0}").format(self.value())
        elif (self.value() == 11):
            if (self._family == Family.Heart):
                s = _("Heart jack")
            elif (self._family == Family.Diamond):
                s = _("Diamond jack")
            elif (self._family == Family.Club):
                s = _("Club jack")
            elif (self._family == Family.Spade):
                s = _("Spade jack")
        elif (self.value() == 12):
            if (self._family == Family.Heart):
                s = _("Heart knight")
            elif (self._family == Family.Diamond):
                s = _("Diamond knight")
            elif (self._family == Family.Club):
                s = _("Club knight")
            elif (self._family == Family.Spade):
                s = _("Spade knight")
        elif (self.value() == 13):
            if (self._family == Family.Heart):
                s = _("Heart queen")
            elif (self._family == Family.Diamond):
                s = _("Diamond queen")
            elif (self._family == Family.Club):
                s = _("Club queen")
            elif (self._family == Family.Spade):
                s = _("Spade queen")
        else: #elif (self.value() == 14):
            if (self._family == Family.Heart):
                s = _("Heart king")
            elif (self._family == Family.Diamond):
                s = _("Diamond king")
            elif (self._family == Family.Club):
                s = _("Club king")
            elif (self._family == Family.Spade):
                s = _("Spade king")

        return s

    def imageName(self) -> str:
        s = ""
        
        if self._family == Family.Heart:
            s = "heart"
        elif self._family == Family.Diamond:
            s = "diamond"
        elif self._family == Family.Club:
            s = "club"
        elif self._family == Family.Spade:
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

class Card:
    def __init__(self, asset: Asset = None, familyCard: FamilyCard = None):
        self._asset = asset
        self._familyCard = familyCard
        assert((self._asset and self._familyCard == None)
               or (self._asset == None and self._familyCard))
        
    def isAsset(self) -> bool:
        return self._asset
        
    def isFamilyCard(self) -> bool:
        return self._familyCard
    
    def asset(self) -> Asset:
        return self._asset
    
    def familyCard(self) -> FamilyCard:
        return self._familyCard
    
    def value(self) -> int:
        if self.isAsset():
            return self._asset.value()
        else: #elif self.isFamilyCard():
            return self._familyCard.value()

    def points(self) -> int:
        if self.isAsset():
            return self._asset.points()
        else: #elif self.isFamilyCard():
            return self._familyCard.points()

    def __int__(self) -> int:
        if self.isAsset():
            return int(self._asset)
        else: #elif self.isFamilyCard():
            return int(self._familyCard)

    def __str__(self) -> str:
        if self.isAsset():
            return str(self._asset)
        else: #elif self.isFamilyCard():
            return str(self._familyCard)

    def name(self) -> str:
        if self.isAsset():
            return self._asset.name()
        else: #elif self.isFamilyCard():
            return self._familyCard.name()

    def imageName(self) -> str:
        if self.isAsset():
            return self._asset.imageName()
        else: #elif self.isFamilyCard():
            return self._familyCard.imageName()

    def image(self):
        image = Image.open(kivy.resources.resource_find("images/" + self.imageName() + ".png"))

        image = image.resize(cardSize)
        
        return image

    def isOudler(self) -> bool:
        if self.isAsset():
            return self._asset.isOudler()
        else: #elif self.isFamilyCard():
            return False

def countOudlersForCards(cards: list) -> int:
    count = 0

    for card in cards:
        if (card.isOudler()):
            count += 1

    return count

def imageForCards(cards: list, enabledCards: list, shown: bool = True):
    assert(len(cards) == len(enabledCards))

    if (len(cards) == 0):
        return None
    
    firstImage = None
    
    if (shown):
        firstImage = cards[0].image()
    else:
        firstImage = Image.open(kivy.resources.resource_find("images/back.png"))
        
        firstImage = firstImage.resize(cardSize)
    
    image = Image.new('RGBA', (firstImage.width + int((len(cards) - 1) * firstImage.width * overCardRatio), firstImage.height))
    
    for i in range(0, len(cards)):
        im = None
        
        if (shown):
            im = cards[i].image()
        else:
            im = firstImage
            
        image.paste(im, (int(i * firstImage.width * overCardRatio), 0))
        
        if (shown):
            if (not enabledCards[i]):
                im = Image.new('RGBA', (im.width, im.height))
                im.paste((0, 0, 0, 128), [0, 0, im.width, im.height])
                img = Image.new('RGBA', (image.width, image.height))
                img.paste(im, (int(i * firstImage.width * overCardRatio), 0))
                image = Image.alpha_composite(image, img)
    
    return image

def pointsForCards(cards: list) -> int:
    points = 0
    
    for card in cards:
        points += card.points()

    return points

def sortCards(cards: list) -> list:
    assets = []
    families = {Family.Heart: [],
                Family.Club: [],
                Family.Diamond: [],
                Family.Spade: []}
    for card in cards:
        if card.isAsset():
            assets.append(card)
        else: #elif card.isFamilyCard():
            families[card.familyCard().family()].append(card)
    assets = sorted(assets, key = lambda x: x.value(), reverse = True)
    for k, v in families.items():
        families[k] = sorted(families[k], key = lambda x: x.value(), reverse = True)
    cards = assets
    if (len(families[Family.Club]) == 0):
        families[Family.Club], families[Family.Spade] = families[Family.Spade], families[Family.Club]
    if (len(families[Family.Diamond]) == 0):
        families[Family.Diamond], families[Family.Heart] = families[Family.Heart], families[Family.Diamond]
    families = [x[1] for x in families.items()]
    for f in families:
        cards += f
        
    return cards

class Player:
    def __init__(self, game, id: int):
        self._game = game
        self._id = id
        self._folds = []
        self._cards = []
        self._attackTeam = False
        self._teamKnown = False
        self._isHuman = False
        self._cuts = {Family.Heart: False,
                      Family.Diamond: False,
                      Family.Club: False,
                      Family.Spade: False}
        
    def isHuman(self):
        return self._isHuman
    
    def points(self) -> int:
        points = 0
        
        points += pointsForCards(self._folds)

        return points
                
    def folds(self) -> list:
        return self._folds
        
    def cards(self) -> list:
        return self._cards
        
    def attackTeam(self) -> bool:
        return self._attackTeam
        
    def defenceTeam(self) -> bool:
        return not self._attackTeam
        
    def teamKnown(self) -> bool:
        return self._teamKnown

    def chooseContract(self, window: Window, contract: Contract) -> Contract:
        possibleContracts = []
        
        if (contract):
            possibleContracts = [-1]
            possibleContracts += [i for i in range(int(contract) + 1, 4)]
        else:
            possibleContracts = [i for i in range(-1, 4)]
            
        if (len(possibleContracts) == 0):
            return None
        
        strContracts = {}
        strContracts[-1] = _("Pass")
        
        for i in range(0, 4):
            strContracts[i] = str(Contract(i))
        
        choices = [strContracts[i] for i in possibleContracts]

        if (self._isHuman):
            kivy.clock.Clock.schedule_once(partial(window.setOpacity, window._contractLabel, 1))
            kivy.clock.Clock.schedule_once(partial(window.setSpinnerValues, window._contractComboBox, choices))
            kivy.clock.Clock.schedule_once(partial(window.setOpacity, window._contractComboBox, 1))
            window._ok = False
            
            while (not window._ok):
                time.sleep(0.01)
            
            contract = {v: k for k, v in strContracts.items()}.get(window._contractComboBox.text)
            
            kivy.clock.Clock.schedule_once(partial(window.setOpacity, window._contractLabel, 0))
            kivy.clock.Clock.schedule_once(partial(window.setOpacity, window._contractComboBox, 0))

            if (contract == -1):
                return None
            else:
                return Contract(contract)
        else:
            guessContract = None
        
            oudlerCount = countOudlersForCards(self._cards)
            
            assets = []
            families = {Family.Heart: [],
                        Family.Club: [],
                        Family.Diamond: [],
                        Family.Spade: []}
            for card in self._cards:
                if card.isAsset():
                    assets.append(card)
                else: #elif card.isFamilyCard():
                    families[card.familyCard().family()].append(card)
            assets = sorted(assets, key = lambda x: x.value())
            for k, v in families.items():
                families[k] = sorted(families[k], key = lambda x: x.value())
            
            points = 0
            
            for card in self._cards:
                points += card.points()
            
            if (oudlerCount == 0):
                guessContract = None
            elif (oudlerCount == 1):
                if (len(assets) >= 22 // 3):
                    guessContract = Contract.Guard
                else:
                    guessContract = Contract.Little
            else:
                cutCount = 0
                
                for k, v in families.items():
                    if (len(families[k]) == 0):
                        cutCount += 1

                if (cutCount == 0):
                    guessContract = Contract.Guard
                else:
                    if (points >= self._game.maximumPoints() // self._game._playerNumber):
                        guessContract = Contract.GuardAgainst
                    else:
                        guessContract = Contract.GuardWithout
            
            if (not guessContract
                or (contract and guessContract.value <= contract.value)):
                return None
            
            return guessContract
    
    def callKing(self, window: Window) -> Family:
        strFamilies = {}
        choices = []
        
        for i in range(0, 4):
            strFamilies[i] = str(Family(i))
            choices.append(str(Family(i)))
        
        calledKing = None
        
        if (self._isHuman):
            kivy.clock.Clock.schedule_once(partial(window.setOpacity, window._kingLabel, 1))
            kivy.clock.Clock.schedule_once(partial(window.setOpacity, window._kingComboBox, 1))
            window._ok = False
            
            while (not window._ok):
                time.sleep(0.01)
            
            calledKing = Family({v: k for k, v in strFamilies.items()}.get(window._kingComboBox.text))
            
            kivy.clock.Clock.schedule_once(partial(window.setOpacity, window._kingLabel, 0))
            kivy.clock.Clock.schedule_once(partial(window.setOpacity, window._kingComboBox, 0))
        else:
            families = {Family.Heart: [],
                        Family.Club: [],
                        Family.Diamond: [],
                        Family.Spade: []}
            familyPoints = {Family.Heart: 0,
                            Family.Club: 0,
                            Family.Diamond: 0,
                            Family.Spade: 0}
            kings = {Family.Heart: False,
                     Family.Club: False,
                     Family.Diamond: False,
                     Family.Spade: False}
            for card in self._cards:
                if card.isFamilyCard():
                    families[card.familyCard().family()].append(card)
                    familyPoints[card.familyCard().family()] += card.points()
                    
                    if (card.value() == 14):
                        kings[card.familyCard().family()] = True
            for k, v in families.items():
                families[k] = sorted(families[k], key = lambda x: x.value())
            
            familyPoints = dict(sorted(familyPoints.items(), key = lambda item: item[1], reverse = True))
            kings = dict(sorted(kings.items(), key = lambda item: item[1]))
                
            for k, v in familyPoints.items():
                if (len(families[k]) and families[k][-1].value() != 14):
                    calledKing = k
                    break
            
            if (not calledKing):
                calledKing = list(kings.items())[0][0]

        return calledKing
    
    def doDog(self, dog: list, window: Window) -> list:
        newDog = []
        
        self._cards += dog
        self._cards = sortCards(self._cards)
        
        kivy.clock.Clock.schedule_once(partial(window.displayTable, [], False, True))

        for i in range(len(dog), 6):
            kivy.clock.Clock.schedule_once(partial(window.removeSpinnerValues, window._dogComboBoxes[i]))
                
        if (self._isHuman):
            comboBoxes = []
            
            strCards = {}
            choices = []
            
            for i in range(0, len(self._cards)):
                if (not (self._cards[i].isAsset()
                         or (self._cards[i].isFamilyCard()
                             and self._cards[i].familyCard().value() == 14))):
                    strCards[i] = str(self._cards[i])
                    choices.append(str(self._cards[i]))
            
            kivy.clock.Clock.schedule_once(partial(window.setOpacity, window._dogLabel, 1))
            
            for i in range(0, len(dog)):
                kivy.clock.Clock.schedule_once(partial(window.setSpinnerValues, window._dogComboBoxes[i], choices))
                kivy.clock.Clock.schedule_once(partial(window.setOpacity, window._dogComboBoxes[i], 1))

            loop = True
            
            while (loop):
                window._ok = False
                
                while (not window._ok):
                    time.sleep(0.01)
  
                selectedCards = []
                
                for i in range(0, len(dog)):
                    selectedCards.append(window._dogComboBoxes[i].text)
                
                loop = len(set(selectedCards)) != len(dog)
            
            kivy.clock.Clock.schedule_once(partial(window.setOpacity, window._dogLabel, 0))
            
            for i in range(0, len(dog)):
                kivy.clock.Clock.schedule_once(partial(window.setOpacity, window._dogComboBoxes[i], 0))
                          
            d = {v: k for k, v in strCards.items()}
            
            for i in range(0, len(dog)):
                selectedCards[i] = d.get(selectedCards[i])
            
            selectedCards = sorted(selectedCards)
            
            for i in reversed(range(0, len(dog))):
                j = selectedCards[i]
                newDog.append(self._cards[j])
                del self._cards[j]
        else:
            #TODO: ...
            
            self._cards = self._cards[0:len(self._cards) - len(dog)]
            newDog = dog
        
        assert(len(newDog) == len(dog))
        
        return sortCards(newDog)

    def enabledCards(self, cards: list, firstRound: bool, calledKing: Family, doDog = False):
        enabledCards = []
        
        if (doDog):
            for i in range(0, len(self._cards)):
                if (not (self._cards[i].isAsset()
                         or (self._cards[i].isFamilyCard()
                         and self._cards[i].familyCard().value() == 14))):
                        enabledCards.append(True)
                else:
                    enabledCards.append(False)
            
            return enabledCards
    
        cardAssets = []

        for card in cards:
            if (card.isAsset()):
                cardAssets.append(card)
  
        cardAssets = sorted(cardAssets, key = lambda x: x.value())
        
        handAssets = []
        handFamilies = {Family.Heart: [],
                        Family.Diamond: [],
                        Family.Club: [],
                        Family.Spade: []}
        
        for i in range(0, len(self._cards)):
            if (self._cards[i].isAsset()):
                handAssets.append(self._cards[i])
            else:
                handFamilies[self._cards[i].familyCard().family()].append(self._cards[i])
 
        handAssets = sorted(handAssets, key = lambda x: x.value())
        
        for i in range(0, len(self._cards)):
            add = True
            
            ok = True
            
            if (firstRound):
                if (len(cards) == 0):
                    if (self._cards[i].isFamilyCard()
                        and self._cards[i].familyCard().family() == calledKing
                        and self._cards[i].familyCard().value() != 14):
                        add = False
                        ok = False
                else:
                    ok = True
            
            if (ok):
                firstCard = None
            
                if (len(cards)):
                    firstCard = cards[0]
                    
                    if (firstCard.isAsset() and firstCard.asset().isFool()):
                        if (len(cards) > 1):
                            firstCard = cards[1]
                        else:
                            firstCard = None

                if (firstCard):
                    if (firstCard.isAsset()):
                        if (len(handAssets)):
                            if (self._cards[i].isAsset()):
                                if (not self._cards[i].asset().isFool()
                                    and handAssets[-1].value() > cardAssets[-1].value()
                                    and self._cards[i].asset().value() < cardAssets[-1].value()):
                                    add = False
                            else:
                                add = False
                    else:
                        if (self._cards[i].isAsset()):
                            if (len(handFamilies[firstCard.familyCard().family()])):
                                if (not self._cards[i].asset().isFool()):
                                    add = False
                            else:
                                if (len(cardAssets)):
                                    if (handAssets[-1].value() > cardAssets[-1].value()
                                        and self._cards[i].asset().value() < cardAssets[-1].value()):
                                        add = False

                            if (add):
                                self._cuts[firstCard.familyCard().family()] = True
                        else:
                            if (self._cards[i].familyCard().family() != firstCard.familyCard().family()
                                and len(handAssets)):
                                add = False
                                self._cuts[self._cards[i].familyCard().family()] = True
            
            enabledCards.append(add)

        return enabledCards

    def playCard(self, window: Window, players: list, cards: dict, firstRound: bool, calledKing: Family) -> Card:
        time.sleep(1)

        card = None

        cardList = [x[1] for x in cards.items()]
        
        enabledCards = self.enabledCards(cardList, firstRound, calledKing)
        
        strCards = {}
        choices = []

        for i in range(0, len(enabledCards)):
            if (enabledCards[i]):
                strCards[i] = self._cards[i].name()
                choices.append(self._cards[i].name())

        kivy.clock.Clock.schedule_once(partial(window.displayTable, cardList, True, False))

        if (self._isHuman):
            kivy.clock.Clock.schedule_once(partial(window.setOpacity, window._cardLabel, 1))
            kivy.clock.Clock.schedule_once(partial(window.setSpinnerValues, window._cardComboBox, choices))
            kivy.clock.Clock.schedule_once(partial(window.setOpacity, window._cardComboBox, 1))
            window._ok = False
            
            while (not window._ok):
                time.sleep(0.01)
            
            kivy.clock.Clock.schedule_once(partial(window.setOpacity, window._cardLabel, 0))
            kivy.clock.Clock.schedule_once(partial(window.setOpacity, window._cardComboBox, 0))
            
            selectedCard = {v: k for k, v in strCards.items()}.get(window._cardComboBox.text)

            card = self._cards[selectedCard]
            del self._cards[selectedCard]
        else:
            assets = []
            families = {Family.Heart: [],
                        Family.Club: [],
                        Family.Diamond: [],
                        Family.Spade: []}
            for card in cardList:
                if card.isAsset():
                    assets.append(card)
                else: #elif card.isFamilyCard():
                    families[card.familyCard().family()].append(card)
            assets = sorted(assets, key = lambda x: x.value())
            for k, v in families.items():
                families[k] = sorted(families[k], key = lambda x: x.value())

            p, c = self._game.setWinner(cards)
        
            playedAssets, playedFamilies = self._game.playedCards()

            order = players.index(self._id)

            selectedCard = len(choices) - 1#selectedCard = random.randrange(len(choices))

            if (p == None):
                if (self._attackTeam):
                    if (self._game._taker == self._id):
                        if (len(assets)):
                            assetIndex = -1
                            
                            if (assets[assetIndex].value() == 0):
                                assetIndex -= 1
                            if (assets[assetIndex].value() == 1):
                                assetIndex -= 1
                            
                            if (abs(assetIndex + 1) > len(assets)):
                                assetIndex += 1
                                
                                if (assets[assetIndex].value() == 1
                                    and assetIndex == -2):
                                    assetIndex = -1
                            
                            selectedCard = choices.index(assets[assetIndex].name())
                        else:
                            for k, v in families.items():
                                bestCard = 15
                                
                                if (len(playedFamilies[k])):
                                    bestCard = playedFamilies[k][-1].value()
                                    
                                if (len(families[k]) and families[k][-1] >= bestCard - 1):
                                    cut = False
                                    
                                    for i in range(0, self._game._playerNumber):
                                        if (self._game._players[i]._cuts[families[k]]):
                                            cut = True
                                            break
                                    
                                    if (not cut):
                                        selectedCard = choices.index(families[k][-1].name())
                    else:
                        takerOrder = players.index(self._game._taker)
                        
                        if (order < takerOrder):
                            if (len(assets)):
                                index = 0
                                
                                if (assets[index].name() == "asset-1"):
                                    index -= 1
                                
                                selectedCard = choices.index(assets[index])
                            else:
                                familyIsPlayed = {Family.Heart: False,
                                                  Family.Club: False,
                                                  Family.Diamond: False,
                                                  Family.Spade: False}
                                playedFamily = False
                                    
                                for k, v in playedFamilies.items():
                                    if (len(v)):
                                        familyIsPlayed[k] = True
                                        playedFamily = True
                                
                                familyIsPlayed = dict(sorted(familyIsPlayed.items(), key = lambda item: item[1], reverse = True))
                            
                                if (playedFamily):
                                    i = 0
                                    
                                    while (i < 4):
                                        try:
                                            selectedCard = choices.index(families[familyIsPlayed[i]][0].name())
                                            i = 4
                                        except:
                                            pass
                                            
                                        i += 1
                                else:
                                    ok = False
                                    
                                    while (not ok):
                                        try:
                                            selectedCard = choices.index(families[Family(random.randrange(4))][0].name())
                                            ok = True
                                        except:
                                            pass
                        else:
                            familyIsPlayed = {Family.Heart: False,
                                              Family.Club: False,
                                              Family.Diamond: False,
                                              Family.Spade: False}
                                
                            for k, v in playedFamilies.items():
                                if (len(v)):
                                    familyIsPlayed[k] = True
                            
                            familyIsPlayed = dict(sorted(familyIsPlayed.items(), key = lambda item: item[1], reverse = True))
                            
                            try:
                                selectedCard = choices.index(families[playedFamilies[0]][0].name())
                            except:
                                pass
                else:
                    takerOrder = players.index(self._game._taker)
                        
                    if (order < takerOrder):
                        familyIsPlayed = {Family.Heart: False,
                                          Family.Club: False,
                                          Family.Diamond: False,
                                          Family.Spade: False}
                            
                        for k, v in playedFamilies.items():
                            if (len(v)):
                                familyIsPlayed[k] = True
                        
                        playedFamilies = dict(sorted(familyIsPlayed.items(), key = lambda item: item[1]))
                        
                        if (list(playedFamilies.values()).count(True) == 4):
                            index = 0
                                
                            if (assets[index].name() == "asset-1"):
                                index -= 1
                            
                            selectedCard = choices.index(assets[index])
                        else:
                            i = 0
                                        
                            while (i < 4):
                                try:
                                    selectedCard = choices.index(families[familyIsPlayed[i]][0].name())
                                    i = 4
                                except:
                                    pass
                                    
                                i += 1
                    else:
                        if (len(assets)):
                            selectedCard = choices.index(assets[0].name())
                        else:
                            playedFamily = None
                            
                            for k, v in playedFamilies.items():
                                if (len(v)):
                                    playedFamily = k
                                    break
                            
                            if (playedFamily):
                                selectedCard = choices.index(families[playedFamily][0].name())
                            else:
                                selectedCard = choices.index(families[Family(random.randrange(4))][0].name())
            else:
                if (self._game._players[p].teamKnown()):
                    if (c.isFamilyCard()):
                        bestCard = 15
                
                        if (len(playedFamilies[c.familyCard().family()])):
                            bestCard = playedFamilies[c.familyCard().family()][-1].value()
                    
                        if (self._game._players[p].attackTeam()):
                            if (self._attackTeam):
                                if (choices[0].startswith("asset-")):
                                    selectedCard = -1
                                else:    
                                    selectedCard = 0
                            else:
                                if (families[c.familyCard().family()][-1].value() >= bestCard - 1):
                                    selectedCard = 0
                                else:
                                    selectedCard = -1
                        else:
                            if (not self._attackTeam):
                                if (choices[0].startswith("asset-")):
                                    selectedCard = -1
                                else:    
                                    selectedCard = 0
                            else:
                                selectedCard = -1
                    else: #elif (c.isAsset()):
                        bestAsset = 22
                        
                        if (len(playedAssets)):
                            bestAsset = playedAssets[-1].value()
                    
                        assetOneIndex = -1
                        
                        for i in range(0, len(self._cards)):
                            if (self._cards[i].isAsset() and self._cards[i].value() == 1):
                                assetOneInCards = i
                                break
                    
                        if (self._game._players[p].attackTeam()):
                            if (self._attackTeam):
                                if (assets[-1].value() >= bestAsset - 1
                                    and assetOneIndex != -1):
                                    selectedCard = choices.index(self._cards[assetOneIndex].name())
                            else:
                                if (choices[selectedCard] == "asset-1" and selectedCard - 1 >= 0):
                                    selectedCard -= 1
                        else:
                            if (not self._attackTeam):
                                if (assets[-1].value() >= bestAsset - 1
                                    and assetOneIndex != -1):
                                    selectedCard = choices.index(self._cards[assetOneIndex].name())
                            else:
                                if (choices[selectedCard] == "asset-1" and selectedCard - 1 >= 0):
                                    selectedCard -= 1
                else:
                    if (c.isFamilyCard()):
                        selectedCard = 0
                    else: #elif (c.isAsset()):
                        index = -1
                        
                        if (choices[index] == "asset-1"):
                            index -= 1
                        
                        try:
                            selectedCard = choices[index]
                            selectedCard = index
                        except:
                            pass

            selectedCard = {v: k for k, v in strCards.items()}.get(choices[selectedCard])
            
            card = self._cards[selectedCard]
            del self._cards[selectedCard]
        
        return card
    
class Game:
    def __init__(self, playerNumber: int = 5):
        self._cards = []
        self._hands = []
        self._dog = []
        self._players = []
        self._contract = None
        self._calledKing = None
        self._playerNumber = playerNumber
        self._firstPlayer = None
        self._taker = None
        self._foolPlayed = None
        self._foolCardGiven = False
        self._currentPlayer = None
        self._firstRound = True
        self._centerCards = []
        assert(3 <= self._playerNumber and self._playerNumber <= 5)
    
    def play(self, window: Window):
        self._firstPlayer = random.randrange(self._playerNumber)
        
        for i in range(0, self._playerNumber):
            p = (self._firstPlayer + i) % self._playerNumber
            self._currentPlayer = p
            kivy.clock.Clock.schedule_once(partial(window.displayTable, self._dog, False, True))
            contract = self._players[p].chooseContract(window, self._contract)
            if (contract):
                self._taker = p
                self._contract = contract
        
        if (not self._contract):
            return

        self._players[self._taker]._attackTeam = True
        self._players[self._taker]._teamKnown = True

        self._currentPlayer = self._taker
        kivy.clock.Clock.schedule_once(partial(window.displayTable, self._dog, False, True))

        if (self._playerNumber == 5):
            self._calledKing = self._players[self._taker].callKing(window)
        else:
            for i in range(0, len(self._players)):
                if (i != self._taker):
                    self._players[i]._attackTeam = False
                    self._players[i]._teamKnown = True

        if (self._contract == Contract.Little
            or self._contract == Contract.Guard):
            kivy.clock.Clock.schedule_once(partial(window.displayTable, self._dog, True, True))
            time.sleep(2)

            kingInDog = False

            for card in self._dog:
                if (card.isFamilyCard()
                    and card.familyCard().family() == self._calledKing
                    and card.familyCard().value() == 14):
                    kingInDog = True
                    break

            if (not kingInDog):
                found = False

                for i in range(0, len(self._players)):
                    for card in self._players[i].cards():
                        if (card.isFamilyCard()
                            and card.familyCard().family() == self._calledKing
                            and card.familyCard().value() == 14):
                            self._players[i]._attackTeam = True
                            found = True
                            break
                    
                    if (found):
                        break
            else:
                for i in range(0, len(self._players)):
                    if (i != self._taker):
                        self._players[i]._attackTeam = False
                        self._players[i]._teamKnown = True

            self._dog = self._players[self._taker].doDog(self._dog, window)

        n = (78 - len(self._dog)) // self._playerNumber

        for i in range(0, n):
            cards = {}

            players = [(self._firstPlayer + j) % self._playerNumber for j in range(0, self._playerNumber)]

            for j in range(0, self._playerNumber):
                self._centerCards = []
                p = (self._firstPlayer + j) % self._playerNumber
                self._currentPlayer = p
                self._firstRound = (i == 0)
                cards[p] = self._players[p].playCard(window, players, cards, self._firstRound, self._calledKing)
                self._centerCards = [x[1] for x in cards.items()]
                
                if (cards[p].isFamilyCard()
                    and cards[p].familyCard().family() == self._calledKing
                    and cards[p].familyCard().value() == 14):
                    for player in self._players:
                        player._teamKnown = True
                    
                if (not self._players[p]._teamKnown):
                    firstCard = None
                        
                    if (len(cards)):
                        firstCard = list(cards.items())[0][1]
                        
                        if (firstCard.isAsset()
                            and firstCard.asset().isFool()):
                            if (len(list(cards.items())) > 1):
                                firstCard = None
                            else:
                                firstCard = list(cards.items())[1][1]
                                    
                    if (cards[p].isAsset()):      
                        if (firstCard and firstCard.isFamilyCard()
                            and firstCard.familyCard().family() == self._calledKing):
                            self._players[p]._attackTeam = False
                            self._players[p]._teamKnown = True
                    elif (cards[p].isFamilyCard()
                          and firstCard == self._calledKing
                          and cards[p].isFamilyCard() != self._calledKing):
                        self._players[p]._attackTeam = False
                        self._players[p]._teamKnown = True

                kivy.clock.Clock.schedule_once(partial(window.displayTable, [v for k, v in cards.items()], True, False))
                time.sleep(1)
            
            self._firstPlayer = self.playSet(cards, i == n - 1)

        kivy.clock.Clock.schedule_once(partial(window.displayTable, self._dog, True, False))
        time.sleep(1)

        if (self._contract == Contract.GuardWithout):
            for p in self._players:
                if (p.defenceTeam()):
                    p._folds += self._dog
                    break
        else:
            self._players[self._taker]._folds += self._dog

        self._dog = []
        
        kivy.clock.Clock.schedule_once(partial(window.displayTable, [], False, False))
        
        self._currentPlayer = None

    def attackPoints(self):
        points = 0

        for p in self._players:
            if p.teamKnown() and p.attackTeam():
                points += p.points()

        return points

    def attackFolds(self):
        folds = []

        for p in self._players:
            if p.teamKnown() and p.attackTeam():
                folds += p.folds()
        
        return folds

    def defencePoints(self):
        points = 0

        for p in self._players:
            if p.teamKnown() and p.defenceTeam():
                points += p.points()
        
        return points

    def defenceFolds(self):
        folds = []

        for p in self._players:
            if p.teamKnown() and p.defenceTeam():
                folds += p.folds()
        
        return folds

    def giveFoolCard(self):
        if (not self._foolPlayed):
            return
        elif (self._foolCardGiven):
            return
            
        defencePlayer = -1
        attackPlayer = -1
        
        for i in range(0, self.playerNumber):
            if (self._players[i].defenceTeam()):
                defencePlayer = i
            else:
                attackPlayer = i
            if (defencePlayer != -1 and attackPlayer != -1):
                break
                
        folds = []
                
        if (self._foolPlayed[0]):
            folds = self.attackFolds()
        else:
            folds = self.defenceFolds()
        
        folds = sorted(folds, key = lambda x: x.points())
            
        givenCard = None
            
        if (len(folds) > 1):
            givenCard = folds[0]
            self._foolCardGiven = True
            
        if (givenCard):
            for player in self._players:
                if (givenCard in self._players._cards):
                    del self._players._cards[self._players._cards.index(givenCard)]
                    break

            if (self._foolPlayed[0]):
                self._players[defencePlayer]._folds.append(givenCard)
            else:
                self._players[attackPlayer]._folds.append(givenCard)

    def maximumPoints(self):
        cards = []
    
        for i in range(0, 4):
            for j in range(1, 11):
                cards.append(Card(familyCard = FamilyCard(family = Family(i), value = j)))
            for j in range(0, 4):
                cards.append(Card(familyCard = FamilyCard(family = Family(i), head = Head(j))))
        for i in range(0, 22):
            cards.append(Card(asset = Asset(i)))
            
        points = 0
        
        for card in cards:
            points += card.points()
            
        return points

    def giveHands(self):
        self._foolPlayed = None
        self._foolCardGiven = False
        self._cards = []
        self._firstRound = True
        self._centerCards = []
        for i in range(0, 4):
            for j in range(1, 11):
                self._cards.append(Card(familyCard = FamilyCard(family = Family(i), value = j)))
            for j in range(0, 4):
                self._cards.append(Card(familyCard = FamilyCard(family = Family(i), head = Head(j))))
        for i in range(0, 22):
            self._cards.append(Card(asset = Asset(i)))
        random.shuffle(self._cards)
        assert(len(self._cards) == 78)
        
        self._players = [Player(self, i) for i in range(0, self._playerNumber)]
        
        n = 78 // 3 // self._playerNumber
        
        for i in range(0, n):
            for j in range(0, len(self._players)):
                self._players[j]._cards += self._cards[0:3]
                self._cards = self._cards[3:]
        
        for player in self._players:
            player._cards = sortCards(player._cards)
        
        self._dog = sortCards(self._cards)
        self._cards = []

    def setWinner(self, cards: dict):
        if (len(cards) == 0):
            return (None, None)
            
        assets = {}
        families = {Family.Heart: {},
                    Family.Diamond: {},
                    Family.Club: {},
                    Family.Spade: {}}
        for k, v in cards.items():
            if v.isAsset():
                assets[k] = v
            else: #elif v.isFamilyCard():
                families[v.familyCard().family()][k] = v
        
        if (len(assets)):
            assets = dict(sorted(assets.items(), key = lambda item: item[1].value()))
            
            p, a = list(assets.items())[-1]
            
            if (a.value() > 0):
                return (p, a)
                
        p, firstCard = list(cards.items())[0]
        
        if (firstCard.isAsset() and firstCard.asset().isFool()):
            if (len(cards) > 1):
                p, firstCard = list(cards.items())[1]
            else:
                return (p, firstCard)
                
        f = dict(sorted(families[firstCard.familyCard().family()].items(), key = lambda item: item[1].value()))
        
        p, c = list(f.items())[-1]
        
        return (p, c)
    
    def playSet(self, cards: dict, lastSet: bool):
        assets = {}
        families = {Family.Heart: {},
                    Family.Diamond: {},
                    Family.Club: {},
                    Family.Spade: {}}
        for k, v in cards.items():
            if v.isAsset():
                assets[k] = v
            else: #elif v.isFamilyCard():
                families[v.familyCard().family()][k] = v.familyCard()

        assets = dict(sorted(assets.items(), key = lambda x: x[1].value()))
        for i in range(0, 4):
            families[Family(i)] = dict(sorted(families[Family(i)].items(), key = lambda x: x[1].value()))

        foolIndex = -1
        
        for i in range(0, len(assets.items())):
            if (list(assets.items())[i][1].asset().isFool()):
                foolIndex = i
                break

        if (len(assets)):
            a = [x[1] for x in assets.items()]
            
            if (foolIndex != -1):
                p = list(assets.items())[foolIndex][0]
                
                if (lastSet):
                    attackTeam = self._players[p].attackTeam()
                    
                    if (attackTeam):
                        for i in range(0, self.playerNumber):
                            if (self._players[i].defenceTeam()):
                                self._players[i]._folds.append(list(assets.items())[foolIndex][1])
                                del assets[i]
                                break
                    else:
                        for i in range(0, self.playerNumber):
                            if (self._players[i].attackTeam()):
                                self._players[i]._folds.append(list(assets.items())[foolIndex][1])
                                del assets[i]
                                break
                else:
                    self._players[p]._folds.append(list(assets.items())[foolIndex][1])
                    del assets[p]
                    
            if (len(assets)):
                p = list(assets.items())[-1][0]
                self._players[p]._folds += [x[1] for x in cards.items()]
                return p
        
        firstCard = list(cards.items())[0][1]
        
        if (firstCard.isAsset() and firstCard.asset().isFool()):
            firstCard = list(cards.items())[1][1]
        
        f = firstCard.familyCard().family()
        p = list(families[f].items())[-1][0]
        self._players[p]._folds += [x[1] for x in cards.items()]
        
        self.giveFoolCard()
        
        return p

    def attackTargetPoints(self):
        points = 56
        oudlerCount = countOudlersForCards(self.attackFolds())

        if (oudlerCount == 3):
            points = 36
        elif (oudlerCount == 2):
            points = 41
        elif (oudlerCount == 1):
            points = 51
            
        return points

    def defenceTargetPoints(self):
        points = 56
        oudlerCount = countOudlersForCards(self.defencefolds())

        if (oudlerCount == 3):
            points = 36
        elif (oudlerCount == 2):
            points = 41
        elif (oudlerCount == 1):
            points = 51
            
        return points

    def attackWins(self):
        return self.attackPoints() >= self.attackTargetPoints()

    def defenceWins(self):
        return not self.attackWins()

    def tableImage(self, showPlayers: list, centerCards: list, showCenterCards: bool, centerCardsIsDog: bool = False):
        assert(len(showPlayers) == self._playerNumber)
        
        tableImage = Image.new('RGBA',
                               (int(kivy.core.window.Window.width * 3 / 4),
                                int(kivy.core.window.Window.height * 8 / 10)),
                               color=(139, 69, 19))
        
        centerCardsImage = imageForCards(centerCards, [True for c in centerCards], shown = showCenterCards)
        #(381, 87)
        if (centerCardsImage):
            tableImage.paste(centerCardsImage, ((tableImage.width - centerCardsImage.width) // 2,
                                                0))
                                                
        text = "?"
        
        if (self._players[self._currentPlayer].teamKnown()):
            text = _("Attack") if self._players[self._currentPlayer].attackTeam() else _("Defence")
    
        draw = ImageDraw.Draw(tableImage)
    
        font = ImageFont.truetype("fonts/DejaVuSans.ttf", 20)
        bbox = draw.textbbox((0, 0), text, font = font, spacing = 0, align = "center")
        w = bbox[2] - bbox[0]
        h = int(1.5 * (bbox[3] - bbox[1]))
        textImage = Image.new('RGBA', (w, h))
        draw = ImageDraw.Draw(textImage)
        draw.text((0, 0), text, font = font, fill = "black")
        textImage = textImage.resize((int(textImage.width * globalRatio),
                                      int(textImage.height * globalRatio)))
        
        image = Image.new('RGBA', (tableImage.width, tableImage.height))
        image.paste(textImage, ((tableImage.width - textImage.width) // 2,
                                (tableImage.height - textImage.height) // 2))
        tableImage = Image.alpha_composite(tableImage, image)
        
        enabledCards = self._players[self._currentPlayer].enabledCards(centerCards, self._firstRound, self._calledKing, centerCardsIsDog)

        playerCardsImage = imageForCards(self._players[self._currentPlayer]._cards,
                                         enabledCards,
                                         shown = showPlayers[self._currentPlayer])
        
        if (playerCardsImage):
            img = playerCardsImage

            bgImg = img.resize((int(img.width + 10 * globalRatio),
                                int(img.height + 10 * globalRatio)))
            bgImg.paste((255, 255, 0, 128), [0, 0, bgImg.width, bgImg.height])
            
            image = Image.new('RGBA', (tableImage.width, tableImage.height))
            image.paste(bgImg, ((tableImage.width - bgImg.width) // 2,
                                tableImage.height - img.height - (bgImg.height - img.height) // 2 ))
            tableImage = Image.alpha_composite(tableImage, image)    

            image = Image.new('RGBA', (tableImage.width, tableImage.height))
            image.paste(img, ((tableImage.width - img.width) // 2, tableImage.height - img.height))
            tableImage = Image.alpha_composite(tableImage, image)
        
        center = (tableImage.width - 100 * globalRatio, 50 * globalRatio)
        radius = 50 * globalRatio
        
        positions = [(center[0], center[1] + radius)]
        angles = [0]
        
        for i in range(1, self._playerNumber):
            angles.append(angles[-1] - 360 / self._playerNumber)
            x = center[0] + radius * math.sin(math.radians(angles[-1]))
            y = center[1] + radius * math.cos(math.radians(angles[-1]))
            positions.append((x, y))
        
        draw = ImageDraw.Draw(tableImage)
        
        font = ImageFont.truetype("fonts/DejaVuSans.ttf", 20)
            
        for i in range(0, self._playerNumber):
            text = "?"
            
            if (self._players[i].teamKnown()):
                text = "A" if self._players[i].attackTeam() else "D"
        
            text += " - " + str(i)
            
            bbox = draw.textbbox((0, 0), text, font = font, spacing = 0, align = "center")
            w = bbox[2] - bbox[0]
            h = int(1.5 * (bbox[3] - bbox[1]))
            textImage = Image.new('RGBA', (w, h))
            draw = ImageDraw.Draw(textImage)
            draw.text((0, 0), text, font = font, fill = "black")
            
            if (i == self._currentPlayer):
                draw.line((0, 0.95 * h, w, 0.95 * h), fill = "black", width = 2)

            textImage = textImage.resize((int(textImage.width * globalRatio),
                                          int(textImage.height * globalRatio)))
            
            img = Image.new('RGBA', (tableImage.width, tableImage.height))
            img.paste(textImage, (int(positions[i][0]), int(positions[i][1])))
            tableImage = Image.alpha_composite(tableImage, img)
        
        return tableImage

    def playedCards(self):
        assets = []
        families = {Family.Heart: [],
                    Family.Diamond: [],
                    Family.Club: [],
                    Family.Spade: []}

        folds = self.attackFolds() + self.defenceFolds()
                    
        for c in folds:
            if c.isAsset():
                assets.append(c)
            else: #elif c.isFamilyCard():
                families[c.familyCard().family()].append(c)
        
        assets = sorted(assets, key = lambda x: x.value())
        
        for k, v in families.items():
            families[k] = sorted(families[k], key = lambda x: x.value())
        
        return (assets, families)

def main():
    locale_dir = os.path.join(os.path.dirname(__file__), 'locales')
    lang = locale.getlocale()[0]
    
    from jnius import autoclass
    Locale = autoclass('java.util.Locale')
    loc = Locale.getDefault()
    lang = loc.getLanguage() + "_" + loc.getCountry()

    lang = gettext.translation('messages', localedir = locale_dir, languages = [lang], fallback = True)
    lang.install()

    app = App()
    app.run()

if (__name__ == "__main__"):
    try:
        main()
    except Exception as e:
        kivy.logger.Logger.error(f"An error occurred: {str(e)}")
        raise
