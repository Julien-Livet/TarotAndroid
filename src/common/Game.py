from common import Asset
from common import Card
from common import Contract
from common import Family
from common import FamilyCard
from common import Head
from common import Player
from common import common
from enum import Enum
import math
import os
from PIL import Image, ImageDraw, ImageFont
import random
from server import Server

class GameState(Enum):
    Begin = 0
    ChooseContract = 1
    CallKing = 2
    ShowDog = 3
    DoDog = 4
    Play = 5
    End = 6

class GameData:
    def __init__(self, playerNumber: int):
        assert(3 <= playerNumber and playerNumber <= 5)

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
        self._gameState = GameState.Begin
        self._remainingTime = 0

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
        
        for i in range(0, self._playerNumber):
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

    def giveHands(self):
        self._gameState = GameState.Begin
        self._foolPlayed = None
        self._foolCardGiven = False
        self._cards = []
        self._firstRound = True
        self._centerCards = []
        self._firstPlayer = random.randrange(self._playerNumber)
        for i in range(0, 4):
            for j in range(1, 11):
                self._cards.append(Card.Card(familyCard = FamilyCard.FamilyCard(family = Family.Family(i), value = j)))
            for j in range(0, 4):
                self._cards.append(Card.Card(familyCard = FamilyCard.FamilyCard(family = Family.Family(i), head = Head.Head(j))))
        for i in range(0, 22):
            self._cards.append(Card.Card(asset = Asset.Asset(i)))
        random.shuffle(self._cards)
        assert(len(self._cards) == 78)
        
        self._players = [Player.Player() for i in range(0, self._playerNumber)]
        
        n = 78 // 3 // self._playerNumber
        
        for i in range(0, n):
            for j in range(0, len(self._players)):
                self._players[j]._cards += self._cards[0:3]
                self._cards = self._cards[3:]
        
        for player in self._players:
            player._cards = common.sortCards(player._cards)
        
        self._dog = common.sortCards(self._cards)
        self._cards = []
        
        for player in self._players:
            assets = []
            
            for card in player._cards:
                if (card.isAsset()):
                    assets.append(card)
                    
            if (len(assets) == 1 and assets[0].value() == 1):
                self.giveHands()

    def setWinner(self, cards: dict):
        if (len(cards) == 0):
            return (None, None)
            
        assets = {}
        families = {Family.Family.Heart: {},
                    Family.Family.Diamond: {},
                    Family.Family.Club: {},
                    Family.Family.Spade: {}}
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
        families = {Family.Family.Heart: {},
                    Family.Family.Diamond: {},
                    Family.Family.Club: {},
                    Family.Family.Spade: {}}
        for k, v in cards.items():
            if v.isAsset():
                assets[k] = v
            else: #elif v.isFamilyCard():
                families[v.familyCard().family()][k] = v.familyCard()

        assets = dict(sorted(assets.items(), key = lambda x: x[1].value()))
        for i in range(0, 4):
            families[Family.Family(i)] = dict(sorted(families[Family.Family(i)].items(), key = lambda x: x[1].value()))

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
                                del assets[list(assets.keys())[foolIndex]]
                                break
                    else:
                        for i in range(0, self._playerNumber):
                            if (self._players[i].attackTeam()):
                                self._players[i]._folds.append(list(assets.items())[foolIndex][1])
                                del assets[list(assets.keys())[foolIndex]]
                                break
                else:
                    self._players[p]._folds.append(list(assets.items())[foolIndex][1])
                    del assets[list(assets.keys())[foolIndex]]
                    
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
        oudlerCount = common.countOudlersForCards(self.attackFolds())

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

    def tableImage(self, gui, showPlayers: list, centerCards: list, showCenterCards: bool, centerCardsIsDog: bool = False, bottomPlayer: int = 0):
        assert(len(showPlayers) == self._playerNumber)

        tableImage = Image.new('RGBA',
                               (int(kivy.core.window.Window.width * 3 / 4),
                                int(kivy.core.window.Window.height * 8 / 10)),
                               color=(139, 69, 19))
        
        centerCardsImage = imageForCards(centerCards, [True for c in centerCards], shown = showCenterCards)

        if (centerCardsImage):
            tableImage.paste(centerCardsImage, ((tableImage.width - centerCardsImage.width) // 2,
                                                0))
        
        if (self._currentPlayer == None):
            return tableImage
                              
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
        families = {Family.Family.Heart: [],
                    Family.Family.Diamond: [],
                    Family.Family.Club: [],
                    Family.Family.Spade: []}

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

class Game(GameData):
    def __init__(self, server: Server.Server, playerNumber: int = 5):
        super().__init__(playerNumber)
        self._server = server

    def play(self):
        self._firstPlayer = random.randrange(self._playerNumber)
        
        self._gameState = GameState.Begin
        
        for i in range(0, self._playerNumber):
            p = (self._firstPlayer + i) % self._playerNumber
            self._currentPlayer = p

            self._state = GameState.ChooseContract
            contract = self._server.chooseContract(self)
            if (contract):
                self._taker = p
                self._contract = contract
        
        if (not self._contract):
            self._gameState = GameState.ShowDog
            QtTest.QTest.qWait(1000)

            self._gameState = GameState.End

            return

        self._players[self._taker]._attackTeam = True
        self._players[self._taker]._teamKnown = True

        self._currentPlayer = self._taker
        self._gameState = GameState.CallKing

        if (self._playerNumber == 5):
            self._calledKing = self._server.callKing(self)
        else:
            for i in range(0, len(self._players)):
                if (i != self._taker):
                    self._players[i]._attackTeam = False
                    self._players[i]._teamKnown = True

        kingInDog = False

        if (self._contract == Contract.Contract.Little
            or self._contract == Contract.Contract.Guard):
            self._gameState = GameState.ShowDog
            QtTest.QTest.qWait(2000)

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

        if (self._contract == Contract.Contract.Little
            or self._contract == Contract.Contract.Guard):
            self._gameState = GameState.DoDog
        
            self._dog = self._server.doDog(self)

        self._gameState = GameState.Play
        
        n = (78 - len(self._dog)) // self._playerNumber

        for i in range(0, n):
            cards = {}

            players = [(self._firstPlayer + j) % self._playerNumber for j in range(0, self._playerNumber)]

            for j in range(0, self._playerNumber):
                self._centerCards = []
                p = (self._firstPlayer + j) % self._playerNumber
                self._currentPlayer = p
                self._firstRound = (i == 0)
                cards[p] = self._server.playCard(self)
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

                QtTest.QTest.qWait(1000)
            
            self._firstPlayer = self.playSet(cards, i == n - 1)

        self._gameState = GameState.ShowDog
        QtTest.QTest.qWait(1000)

        if (self._contract == Contract.Contract.GuardWithout):
            for p in self._players:
                if (p.defenceTeam()):
                    p._folds += self._dog
                    break
        else:
            self._players[self._taker]._folds += self._dog

        self._dog = []
        
        self._currentPlayer = None
        self._gameState = GameState.End
