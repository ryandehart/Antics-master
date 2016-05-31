  # -*- coding: latin-1 -*-
import random
import sys
sys.path.append("..")  #so other modules can be found in parent dir
from Player import *
from Constants import *
from Construction import CONSTR_STATS
from Ant import UNIT_STATS
from Move import Move
from GameState import addCoords
from AIPlayerUtils import *


##
#AIPlayer
#Description: The responsbility of this class is to interact with the game by
#deciding a valid move based on a given game state. This class has methods that
#will be implemented by students in Dr. Nuxoll's AI course.
#
#Variables:
#   playerId - The id of the player.
##
class AIPlayer(Player):

    #__init__
    #Description: Creates a new Player
    #
    #Parameters:
    #   inputPlayerId - The id to give the new player (int)
    ##
    def __init__(self, inputPlayerId):
        super(AIPlayer,self).__init__(inputPlayerId, "Simple Drone->Queen Attack And Food Gatherer")
        self.myFood = None
        self.myTunnel = None

    ##
    #getPlacement
    #
    #Description: The getPlacement method corresponds to the
    #action taken on setup phase 1 and setup phase 2 of the game.
    #In setup phase 1, the AI player will be passed a copy of the
    #state as currentState which contains the board, accessed via
    #currentState.board. The player will then return a list of 11 tuple
    #coordinates (from their side of the board) that represent Locations
    #to place the anthill and 9 grass pieces. In setup phase 2, the player
    #will again be passed the state and needs to return a list of 2 tuple
    #coordinates (on their opponent's side of the board) which represent
    #Locations to place the food sources. This is all that is necessary to
    #complete the setup phases.
    #
    #Setup Phase 1 is hard coded, Phase 2 places food far from enemy tunnel
    #
    #Parameters:
    #   currentState - The current state of the game at the time the Game is
    #       requesting a placement from the player.(GameState)
    #
    #Return: If setup phase 1: list of eleven 2-tuples of ints -> [(x1,y1), (x2,y2),…,(x10,y10)]
    #       If setup phase 2: list of two 2-tuples of ints -> [(x1,y1), (x2,y2)]
    ##
    def getPlacement(self, currentState):
        #places grass and anthill and tunnel
        if currentState.phase == SETUP_PHASE_1:
            return [(0,0), (4,1), (1,3), (2,3), (3,3), (4,3), (5,3), (6,3), (7,3), (8,3), (9,3)]

        #places enemy food
        elif currentState.phase == SETUP_PHASE_2:
            foodPoints = [(0,0), (0,0)] #the places where we will place food
            enemyPlayer = 0
            if currentState.whoseTurn == 0:
                enemyPlayer = 1
            tunnel = getConstrList(currentState, enemyPlayer, (TUNNEL,))[0].coords

            #place 2 foods at empty cells
            for i in range(0, 2):
                for x in range(0, 10):
                    for y in range(6, 10):
                        #if the cell is empty, the distance is the greatest so far,
                        #and is not the same cell used for the first food
                        if (currentState.board[x][y].constr == None) and \
                                ((x, y) != foodPoints[0]) and \
                                ((self.getDistance(tunnel, (x, y)) >=
                                self.getDistance(tunnel, foodPoints[i]))
                                or foodPoints[i] == (0,0)):
                            #set point
                            foodPoints[i] = (x, y)
            return foodPoints #returns the points where food will be placed

        return [(0,0)] #for compiling; never reaches here

    ##
    #getDistance
    #Description:finds the raw distance between two cells
    def getDistance(self, src, dst):
        differenceX = abs(src[0] - dst[0])
        differenceY = abs(src[1] - dst[1])
        return differenceX + differenceY


    ##
    #getMove
    #Description: The getMove method corresponds to the play phase of the game
    #and requests from the player a Move object. All types are symbolic
    #constants which can be referred to in Constants.py. The move object has a
    #field for type (moveType) as well as field for relevant coordinate
    #information (coordList). If for instance the player wishes to move an ant,
    #they simply return a Move object where the type field is the MOVE_ANT constant
    #and the coordList contains a listing of valid locations starting with an Ant
    #and containing only unoccupied spaces thereafter. A build is similar to a move
    #except the type is set as BUILD, a buildType is given, and a single coordinate
    #is in the list representing the build location. For an end turn, no coordinates
    #are necessary, just set the type as END and return.
    #
    #Based in the Simple Food Gatherer's getMove. Harvests food with its worker and builds
    #one drone as soon as possible. Then it sends the drone to attack the enemy's tunnel.
    #The queen stays back for defense.
    #
    #Parameters:
    #   currentState - The current state of the game at the time the Game is
    #       requesting a move from the player.(GameState)
    #
    #Return: Move(moveType [int], coordList [list of 2-tuples of ints], buildType [int]
    ##
    def getMove(self, currentState):
        #Useful pointers
        myInv = getCurrPlayerInventory(currentState)
        me = currentState.whoseTurn

        #the first time this method is called, the food and tunnel locations
        #need to be recorded in their respective instance variables
        if (self.myTunnel == None):
            self.myTunnel = getConstrList(currentState, me, (TUNNEL,))[0]
        if (self.myFood == None):
            foods = getConstrList(currentState, None, (FOOD,))
            self.myFood = foods[0]
            #find the food closest to the tunnel
            bestDistSoFar = 1000 #i.e., infinity
            for food in foods:
                dist = stepsToReach(currentState, self.myTunnel.coords, food.coords)
                if (dist < bestDistSoFar):
                    self.myFood = food
                    bestDistSoFar = dist

        #if there are no ants besides queen, make no move
        numAnts = len(myInv.ants)
        if (numAnts == 1):
            return Move(END, None, None)

        #if queen is on anthill, move it
        self.myAntHill = getConstrList(currentState, me, (ANTHILL,))[0]
        self.myQueen = getAntList(currentState, me, (QUEEN,))[0]
        if self.myAntHill.coords == self.myQueen.coords:
            path = createPathToward(currentState, self.myQueen.coords, (self.myQueen.coords[0] + 2, self.myQueen.coords[1]), UNIT_STATS[QUEEN][MOVEMENT])
            return Move(MOVE_ANT, path, None)

        #if we can build a drone, do so
        droneExists = False
        for i in range(0, len(myInv.ants)):
            if (myInv.ants[i].type == DRONE):
                droneExists = True
        if (droneExists == False):
            legalBuilds = listAllBuildMoves(currentState)
            for i in range (0, len(legalBuilds)):
                if (legalBuilds[i].buildType == DRONE):
                    return Move(legalBuilds[i].moveType, legalBuilds[i].coordList, legalBuilds[i].buildType)

        #if we have a drone, attack the enemy's queen
        enemyPlayer = 0
        if me == 0:
            enemyPlayer = 1
        foods = getConstrList(currentState, None, (FOOD,))
        self.enemyQueen = getAntList(currentState, enemyPlayer, (QUEEN,))[0]
        self.enemyFood = foods[0]
        self.myDrone = None
        if droneExists == True:
            self.myDrone = getAntList(currentState, me, (DRONE,))[0]
            #if the drone has already moved
            if not(self.myDrone.hasMoved):
                path = createPathToward(currentState, self.myDrone.coords,
                                       self.enemyQueen.coords, UNIT_STATS[DRONE][MOVEMENT])
                return Move(MOVE_ANT, path, None)

        #move worker
        workerExists = False
        for i in range(0, len(myInv.ants)):
            if (myInv.ants[i].type == WORKER):
                workerExists = True
        if workerExists:
            #this section is modeled after the Simple Food Gatherer
            #by Andrew Nuxoll

            #dont try to move the worker twice in one turn
            myWorker = getAntList(currentState, me, (WORKER,))[0]
            if (myWorker.hasMoved):
                return Move(END, None, None)

            #if the worker has food, move toward tunnel
            if (myWorker.carrying):
                path = createPathToward(currentState, myWorker.coords,
                                        self.myTunnel.coords, UNIT_STATS[WORKER][MOVEMENT])
                return Move(MOVE_ANT, path, None)

            #if the worker has no food, move toward food
            else:
                path = createPathToward(currentState, myWorker.coords,
                                        self.myFood.coords, UNIT_STATS[WORKER][MOVEMENT])
                return Move(MOVE_ANT, path, None)
    
    ##
    #getAttack
    #Description: The getAttack method is called on the player whenever an ant completes 
    #a move and has a valid attack. It is assumed that an attack will always be made 
    #because there is no strategic advantage from withholding an attack. The AIPlayer 
    #is passed a copy of the state which again contains the board and also a clone of 
    #the attacking ant. The player is also passed a list of coordinate tuples which 
    #represent valid locations for attack. Hint: a random AI can simply return one of 
    #these coordinates for a valid attack. 
    #
    #Parameters:
    #   currentState - The current state of the game at the time the Game is requesting 
    #       a move from the player. (GameState)
    #   attackingAnt - A clone of the ant currently making the attack. (Ant)
    #   enemyLocation - A list of coordinate locations for valid attacks (i.e. 
    #       enemies within range) ([list of 2-tuples of ints])
    #
    #Return: A coordinate that matches one of the entries of enemyLocations. ((int,int))
    ##
    def getAttack(self, currentState, attackingAnt, enemyLocations):
        #Attack a random enemy, as in AIPlayer
        return enemyLocations[random.randint(0, len(enemyLocations) - 1)]
        
    ##
    #registerWin
    #Description: The last method, registerWin, is called when the game ends and simply 
    #indicates to the AI whether it has won or lost the game. This is to help with 
    #learning algorithms to develop more successful strategies.
    #
    #Parameters:
    #   hasWon - True if the player has won the game, False if the player lost. (Boolean)
    #
    def registerWin(self, hasWon):
        #method templaste, not implemented
        pass
