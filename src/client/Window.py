from common import Family
from common import TableLabel
from common import common
from common import TableLabel
from client import Client
import io
import kivy.app
import kivy.graphics.texture
import kivy.uix
import kivy.uix.boxlayout
import kivy.uix.image
import kivy.uix.button
import kivy.uix.checkbox
import kivy.uix.spinner
import kivy.uix.textinput
import math
import os
from PIL import Image
import plyer
import random
from server import Server
import struct
import threading

iniFilename = os.path.dirname(__file__) + "/../../Tarot.ini"

class MyTextInput(kivy.uix.textinput.TextInput):
    max_characters = 8

    def insert_text(self, substring, from_undo = False):
        if (len(self.text) >= self.max_characters and self.max_characters > 0):
            substring = ""

        kivy.uix.textinput.TextInput.insert_text(self, substring, from_undo)

class Window(kivy.uix.boxlayout.BoxLayout):
    def __init__(self, app: kivy.app.App):
        super().__init__(orientation = "horizontal", spacing = 0)
        self._playerNumber = 5
        self._window = None
        self._dialog = None
        self._ok = False
        self._app = app
        self._playerNumber = 5
        self._window = None
        self._dialog = None
        self._ok = False
        self._globalRatio = 0.8
        self._cardSize = (0, 0)
        self._overCardRatio = 1 / 3
        self._client = None
        self._avatarFilename = os.path.dirname(__file__) + "/../../images/avatar.png"
        self._avatar = Image.open(os.path.dirname(__file__) + "/../../images/avatar.png")
        self._localServer = None
        self._localClients = []
        self._timer = None
        self._remainingTime = 15

        assert(0 < self._overCardRatio and self._overCardRatio <= 1)

        layout = kivy.uix.boxlayout.BoxLayout(orientation = "vertical")

        self._lineEdit = MyTextInput()
        self._lineEdit.multiline = False
        self._avatarButton = kivy.uix.button.Button()
        self._avatarButton.size = (128, 128)
        self._avatarButton.size_hint = (None, None)
        self._avatarButton.bind(on_press = self.chooseAvatar)
        self._avatar = None
        
        threeButton = kivy.uix.button.Button(text = _("Three players"))
        threeButton.bind(on_press = self.threePlayers)
        fourButton = kivy.uix.button.Button(text = _("Four players"))
        fourButton.bind(on_press = self.fourPlayers)
        fiveButton = kivy.uix.button.Button(text = _("Five players"))
        fiveButton.bind(on_press = self.fivePlayers)

        self._localRadioButton = kivy.uix.checkbox.CheckBox(active = True)
        self._localRadioButton.group = "group"
        self._onlineRadioButton = kivy.uix.checkbox.CheckBox(active = False)
        self._onlineRadioButton.group = "group"

        if (os.path.exists(iniFilename)):
            lines = []

            with open(iniFilename, 'r') as file:
                lines = file.read().split("\n")
                
            name = lines[0]
            avatarFilename = lines[1]
            local = lines[2]
            self._lineEdit.text = name
            
            if (avatarFilename):
                self._avatarFilename = avatarFilename
                
            self._localRadioButton.active = (local == "True")
            self._onlineRadioButton.active = (local == "False")

        if (self._avatarFilename):
            self._avatar = Image.open(self._avatarFilename)

            self._avatarButton.background_normal = self._avatarFilename
            self._avatarButton.background_down = self._avatarFilename
            
        horizontalLayout = kivy.uix.boxlayout.BoxLayout(orientation = "horizontal")

        horizontalLayout.add_widget(self._lineEdit)
        horizontalLayout.add_widget(self._avatarButton)

        layout.add_widget(horizontalLayout)
        layout.add_widget(threeButton)
        layout.add_widget(fourButton)
        layout.add_widget(fiveButton)

        l = kivy.uix.boxlayout.BoxLayout(orientation = "horizontal")
        l.add_widget(self._localRadioButton)
        l.add_widget(kivy.uix.label.Label(text = _("Local"), halign = 'left', valign = 'middle'))
        l.add_widget(self._onlineRadioButton)
        l.add_widget(kivy.uix.label.Label(text = _("Online"), halign = 'left', valign = 'middle'))
        layout.add_widget(l)

        self.add_widget(layout)

    def __del__(self):
        if (self._client):
            self._client.close()

        for client in self._localClients:
            client.close()

        self._localClients = []

        if (self._localServer):
            self._localServer.close()

    def close(self):
        with open(iniFilename, 'w') as file:
            file.write(self._lineEdit.text + "\n")
            file.write(self._avatarFilename + "\n")
            file.write(str(self._localRadioButton.active) + "\n")

        if (self._client):
            self._client.close()

        for client in self._localClients:
            client.close()

        self._localClients = []

        if (self._localServer):
            self._localServer.close()

    def setOpacity(self, widget, opacity, *largs):
        widget.opacity = opacity
        widget.disabled = (opacity == 0)

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
        if (not self._client or not self._client._id):
            return

        self._tableLabel.setImage(self._game.tableImage(self._showPlayers, centerCards, displayCenterCards, centerCardsIsDog))

    def comboBoxActivated(self, spinner, text):
        for i in range(0, 6):
            if (self._dogComboBoxes[i] == spinner):
                self._dogIndex = i
                break

    def chooseAvatar(self, instance):
        plyer.filechooser.open_file(on_selection = self.on_file_select)

    def on_file_select(self, selection):
        if (selection):
            self._avatarFilename = selection[0]
            self._avatar = Image.open(self._avatarFilename).resize(64, 64)

            self._avatarButton.background_normal = self._avatarFilename
            self._avatarButton.background_down = self._avatarFilename

    def play(self):
        host = "localhost"
        port = 18861

        if (self._localRadioButton.active):
            launched = False
            
            from rpyc.utils.server import ThreadedServer
        
            while (not launched):
                try:
                    self._localServer = ThreadedServer(Server.Service, port = port)
                    launched = True
                except ConnectionRefusedError:
                    port = random.randrange(1024, 49151)
                except OSError:
                    port = random.randrange(1024, 49151)
            
            threading.Thread(target = self._localServer.start).start()
            
            for i in range(1, self._playerNumber):
                self._localClients.append(Client.Client(self, self._playerNumber, False, host, port))
        else:
            #TODO: put a valid server address
            host = "192.168.0.39"

        self._globalRatio = 1.5 * kivy.core.window.Window.width / kivy.core.window.Window.height
            
        self._cardSize = (int(56 * self._globalRatio), int(109 * self._globalRatio))

        self._client = Client.Client(self, self._playerNumber, True, host, port)

        self.clear_widgets()

        self._tableLabel = TableLabel.TableLabel(self)
        self._tableLabel.padding = (0, 0, 0, 0)
        self._pointsLabel = kivy.uix.label.Label(text = _("Attack points: 0 - Defence points: 0"), halign = 'center', valign = 'middle')

        self._contractLabel = kivy.uix.label.Label(text = _("Choose a contract"), halign = 'center', valign = 'middle')
        self._contractLabel.opacity = 0
        self._contractLabel.disabled = True
        self._contractComboBox = kivy.uix.spinner.Spinner()
        self._contractComboBox.opacity = 0
        self._contractComboBox.disabled = True

        choices = []

        for i in range(0, 4):
            choices.append(str(Family.Family(i)))

        self._kingLabel = kivy.uix.label.Label(text = _("Call a king"), halign = 'center', valign = 'middle')
        self._kingLabel.opacity = 0
        self._kingLabel.disabled = True
        self._kingComboBox = kivy.uix.spinner.Spinner(text = choices[0], values = choices)
        self._kingComboBox.opacity = 0
        self._kingComboBox.disabled = True

        self._dogLabel = kivy.uix.label.Label(text = _("Do a dog"), halign = 'center', valign = 'middle')
        self._dogLabel.opacity = 0
        self._dogLabel.disabled = True
        self._dogComboBoxes = []
        for i in range(0, 6):
            self._dogComboBoxes.append(kivy.uix.spinner.Spinner())
            self._dogComboBoxes[-1].opacity = 0
            self._dogComboBoxes[-1].disabled = True
            self._dogComboBoxes[-1].bind(on_text = self.comboBoxActivated)

        self._cardLabel = kivy.uix.label.Label(text = _("Play a card"), halign = 'center', valign = 'middle')
        self._cardLabel.opacity = 0
        self._cardLabel.disabled = True
        self._cardComboBox = kivy.uix.spinner.Spinner()
        self._cardComboBox.opacity = 0
        self._cardComboBox.disabled = True

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

        kivy.clock.Clock.schedule_interval(self.monitor, 100)

    def ok(self, instance):
        self._ok = True
        
    def monitor(self, dt):
        if (self._client == None or self._client._gameData == None):
            return

        from common import Game

        gameData = self._client._gameData
        gameState = gameData._gameState
        
        if (gameState == Game.GameState.Begin
            or gameState == Game.GameState.End):
            self.displayTable(gameData._dog, False, True)
        elif (gameState == Game.GameState.ChooseContract
              or gameState == Game.GameState.CallKing):
            self.displayTable(gameData._dog, False, True)
        elif (gameState == Game.GameState.ShowDog):
            self.displayTable(gameData._dog, True)
        elif (gameState == Game.GameState.Play and len(gameData._centerCards)):
            self.displayTable(gameData._centerCards, True, False)
        elif (gameState == Game.GameState.DoDog):
            self.displayTable([], False, True)
        
        take = ""
        
        if (gameData._calledKing):
            take = _("\nCalled king: ") \
                   + str(gameData._calledKing)

        if (gameData._contract):
            take += _("\nContract: ") \
                    + str(gameData._contract) \
                    + _(" ({0} points)") \
                    .format(gameData.attackTargetPoints())
    
        self._pointsLabel.setText(_("Attack points: {0} - Defence points: {1}")
                                  .format(gameData.attackPoints(),
                                          gameData.defencePoints())
                                  + take)
                   
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
                                if (self._dogIndex >= 6 or not self._dogComboBoxes[self._dogIndex].opacity == 1):
                                    self._dogIndex = 0
                        
                        break

        if (gameData._gameState == Game.GameState.End):
            if (gameData.attackPoints() == 0
                and gameData.defencePoints() == 0):
                self._content = kivy.uix.boxlayout.BoxLayout(orientation = 'vertical')
                self._content.add_widget(kivy.uix.label.Label(text = _("Nobody takes!")))
                self._content.bind(on_touch_down = self.on_popup_ok)
                self._popup = kivy.uix.popup.Popup(title = _("Game over"), content = self._content)
                self._popup.open()
            else:
                if (gameData.attackWins()):
                    self._content = kivy.uix.boxlayout.BoxLayout(orientation = 'vertical')
                    self._content.bind(on_touch_down = self.on_popup_ok)
                    self._content.add_widget(kivy.uix.label.Label(text = (_("Well done!") if self._game._players[0].attackTeam() else _("Shame!"))
                                                                         + _(" Attack wins ({0} points for {1} points)!")
                                                                           .format(self._game.attackPoints(),
                                                                                   self._game.attackTargetPoints())))
                    self._popup = kivy.uix.popup.Popup(title = _("Game over"),
                                                       content = self._content)
                    self._popup.open()
                else:
                    self._content = kivy.uix.boxlayout.BoxLayout(orientation = 'vertical')
                    self._content.bind(on_touch_down = self.on_popup_ok)
                    self._content.add_widget(kivy.uix.label.Label(text = (_("Well done!") if self._game._players[0].defenceTeam() else _("Shame!"))
                                                                         + _(" Attack loses ({0} points for {1} points)!")
                                                                           .format(self._game.attackPoints(),
                                                                                   self._game.attackTargetPoints())))
                    self._popup = kivy.uix.popup.Popup(title = _("Game over"),
                                                       content = self._content)
                    self._popup.open()

    def on_popup_ok(self, instance, touch):
        self._app.stop()
