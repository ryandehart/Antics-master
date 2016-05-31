import random
import sys

sys.path.append("..")  # so other modules can be found in parent dir
from Player import *
from Constants import *
from Construction import CONSTR_STATS
from Ant import UNIT_STATS
from Move import Move
from GameState import *
from AIPlayerUtils import *
import Ant
import Construction


##
# FOOD
# Description: This AI is focused purely on beating its opponent to gathering 11 food
# The setup phase, worker movement, and queen use are all made to gather food efficiently
# and make as few purchases as possible
#
# Variables:
#   playerId - The id of the player.
##
class AIPlayer(Player):
    # __init__
    # Description: Creates a new Player
    #
    # Parameters:
    #   inputPlayerId - The id to give the new player (int)
    ##
    def __init__(self, inputPlayerId):
        super(AIPlayer, self).__init__(inputPlayerId, "FOOD")

    ##
    # getPlacement
    #
    # Description: called during setup phase for each Construction that
    #   must be placed by the player.  These items are: 1 Anthill on
    #   the player's side; 1 tunnel on player's side; 9 grass on the
    #   player's side; and 2 food on the enemy's side.
    #
    #   This setup is the random setup
    #
    # Parameters:
    #   construction - the Construction to be placed.
    #   currentState - the state of the game at this point in time.
    #
    # Return: The coordinates of where the construction is to be placed
    ##
    def getPlacement(self, currentState):
        numToPlace = 0
        # implemented by students to return their next move
        if currentState.phase == SETUP_PHASE_1:  # stuff on my side
            numToPlace = 11
            moves = []
            for i in range(0, numToPlace):
                move = None
                while move == None:
                    # Choose any x location
                    x = random.randint(0, 9)
                    # Choose any y location on your side of the board
                    y = random.randint(0, 3)
                    # Set the move if this space is empty
                    if currentState.board[x][y].constr == None and (x, y) not in moves:
                        move = (x, y)
                        # Just need to make the space non-empty. So I threw whatever I felt like in there.
                        currentState.board[x][y].constr == True
                moves.append(move)
            return moves
        elif currentState.phase == SETUP_PHASE_2:  # stuff on foe's side
            numToPlace = 2
            moves = []
            for i in range(0, numToPlace):
                move = None
                while move == None:
                    # Choose any x location
                    x = random.randint(0, 9)
                    # Choose any y location on enemy side of the board
                    y = random.randint(6, 9)
                    # Set the move if this space is empty
                    if currentState.board[x][y].constr == None and (x, y) not in moves:
                        move = (x, y)
                        # Just need to make the space non-empty. So I threw whatever I felt like in there.
                        currentState.board[x][y].constr == True
                moves.append(move)
            return moves
        else:
            return [(0, 0)]

    ##
    # getAttack
    # Description: Gets the attack to be made from the Player
    #
    # Parameters:
    #   currentState - A clone of the current state (GameState)
    #   attackingAnt - The ant currently making the attack (Ant)
    #   enemyLocation - The Locations of the Enemies that can be attacked (Location[])
    ##
    def getAttack(self, currentState, attackingAnt, enemyLocations):
        # Attack a random enemy.
        return enemyLocations[random.randint(0, len(enemyLocations) - 1)]






    ##
    #
    # description: returns the best possible move based on rewards
    #
    # parameters: currentState: the current Gamestate
    ##
    def getMove(self, currentState):


        possibleMoves = listAllMovementMoves(currentState) #list of all possible moves

        #only append build moves if there are 3 or fewer ants
        anthill = currentState.inventories[currentState.whoseTurn].getAnthill()
        nearestFoodDist = 1000  # arbitrarily large
        nearestFoodPoint = (0, 0)
        for constr in currentState.inventories[NEUTRAL].constrs:
            if (constr.type == FOOD and approxDist(constr.coords, anthill.coords) < nearestFoodDist):
                nearestFoodDist = approxDist(constr.coords, anthill.coords)
                nearestFoodPoint = constr.coords
        print nearestFoodDist
        maxAnts = 3 + ((nearestFoodDist + 1) / 3)
        if (maxAnts > 4):
            maxAnts = 4
        print maxAnts
        if (len(currentState.inventories[currentState.whoseTurn].ants) < maxAnts):
            for move in listAllBuildMoves(currentState):
                possibleMoves.append(move)
        possibleMoves.append(Move(END, None, None))  # append end turn move


        maxDepth = 1
        newNode = self.Node(currentState, maxDepth, maxDepth)

        return newNode.evaluateLayer()  # returns best move



    class Node(object):

        def __init__(self, state, depth, maxdepth):
            self.state = state
            self.depth = depth
            self.possibleMoves = listAllLegalMoves(self.state)
            self.maxdepth = maxdepth

        def evaluateLayer(self):
            if (self.depth == 0):
                return self.evaluateState(self.state)
            else:
                newNodes = []
                for move in self.possibleMoves:
                    newNodes.append(Node(self.predictOutcome(self.state, move), self.depth - 1, self.maxdepth))
                bestValue = 0.0
                bestIndex = 0
                index = 0
                for node in newNodes:
                    nodeValue = node.evaluateState(node.state) + node.evaluateLayer()
                    if (nodeValue < bestValue):
                        bestValue = nodeValue
                        bestIndex = index
                    index += 1
                if (self.depth == self.maxdepth):
                    return self.possibleMoves[bestIndex]
                else:
                    return bestValue


        def evaluateChildren(self, nodes):
            best = 0
            for node in nodes:
                if (self.evaluateState(self.state) > best):
                    best = self.evaluateState(self.state)

            return best

        ##
        #   Evaluate State
        #
        ##
        def evaluateState(self, state):

            # useful stuff
            me = state.whoseTurn
            enemy = 0
            if (me == 0):
                enemy = 1

            # go through and find winning moves; return 1.0

            if ((state.inventories[enemy].getQueen() == None) or
                    (state.inventories[enemy].getAnthill().captureHealth <= 0) or
                    (state.inventories[me].foodCount >= FOOD_GOAL)):
                return 1.0

            # score values

            # value given for my food vs enemy food
            foodValue = (1 / 11) * (1 / 10) * (1 / 2) * \
                        (state.inventories[me].foodCount - state.inventories[enemy].foodCount)

            # value given for the queen's position. The queen avoids harvesting lines and fights off enemy attacks
            QueenValue = self.generateQueenValue(state)

            # worker harvesting
            clockwise = [0.0, 0.0, 0.0]  # workers are rewarded for harvesting in a clockwise direction
            # to avoid bumping into each other and maximize efficiency
            harvestingValue = [0.0, 0.0, 0.0]  # workers are rewarded for harvesting food (in any direction)
            workerNumber = 0  # iterator
            distance = 0  # distance remaining in a harvesting cycle for a worker

            # iterates through each worker ant, and setting rewards
            for ant in state.inventories[me].ants:  # for each of my ants
                if (ant.type == WORKER):  # if worker
                    if (ant.carrying == False):

                        # reward for harvesting in general
                        bestDistance = 1000  # arbitrarily large
                        bestFoodPoint = (0, 0)  # nearest food point
                        for constr in state.inventories[NEUTRAL].constrs:  # for each food
                            if (constr.type == FOOD):
                                if (approxDist(ant.coords, constr.coords) <= bestDistance):  # if food is closest
                                    # record closest food point
                                    bestDistance = approxDist(ant.coords, constr.coords)
                                    bestFoodPoint = constr.coords

                        bestDistanceReturn = 1000  # arbitrarily large
                        bestReturnPoint = (0, 0)  # best return point (tunnel or anthill)
                        for constr in state.inventories[me].constrs:  # for each of my tunnels and anthills
                            if (constr.type == TUNNEL, constr.type == ANTHILL):
                                if (approxDist(bestFoodPoint, constr.coords) <= bestDistanceReturn):  # if closest return
                                    # record closest return point to the best food point
                                    bestDistanceReturn = approxDist(bestFoodPoint, constr.coords)
                                    bestReturnPoint = constr.coords

                        distance = bestDistance + bestDistanceReturn  # distance remaining in full harvesting cycle

                        # small bonus reward for harvesting clockwise (toward food)
                        if (ant.coords[0] < bestFoodPoint[0]):  # if west of food
                            if (ant.coords[1] < bestFoodPoint[1]):  # if north of food
                                clockwise[workerNumber] = ant.coords[0]  # reward going east
                            elif (ant.coords[1] > bestFoodPoint[1]):  # if south of food
                                clockwise[workerNumber] = 10 - ant.coords[1]  # reward going north
                        elif (ant.coords[0] > bestFoodPoint[0]):  # if east of food
                            if (ant.coords[1] < bestFoodPoint[1]):  # if north of food
                                clockwise[workerNumber] = ant.coords[1]  # reward goings south
                            elif (ant.coords[1] > bestFoodPoint[1]):  # if south of food
                                clockwise[workerNumber] = 10 - ant.coords[0]  # reward for going west
                    else:

                        # reward harvesting in general
                        bestDistance = 1000  # arbitrarily large
                        bestReturnPoint = (0, 0)  # best return point
                        for constr in state.inventories[me].constrs:  # for each return point
                            if (constr.type == TUNNEL or constr.type == ANTHILL):
                                if (approxDist(ant.coords, constr.coords) <= bestDistance):  # if closest to ant's location
                                    # record closest return point to ant's location
                                    bestDistance = approxDist(ant.coords, constr.coords)
                                    bestReturnPoint = constr.coords

                        distance = approxDist(ant.coords, bestReturnPoint)  # distance remaining in harvesting cycle

                        # small bonus reward for harvesting clockwise (toward return point)
                        if (ant.coords[0] < bestReturnPoint[0]):  # if west of return point
                            if (ant.coords[1] < bestReturnPoint[1]):  # if north of return point
                                clockwise[workerNumber] = ant.coords[0]  # reward going east
                            elif (ant.coords[1] > bestReturnPoint[1]):  # if south of return point
                                clockwise[workerNumber] = 10 - ant.coords[1]  # reward going north
                        elif (ant.coords[0] > bestReturnPoint[0]):  # if east of return point
                            if (ant.coords[1] < bestReturnPoint[1]):  # if north of return point
                                clockwise[workerNumber] = ant.coords[1]  # reward goings south
                            elif (ant.coords[1] > bestReturnPoint[1]):  # if south of return point
                                clockwise[workerNumber] = 10 - ant.coords[0]  # reward for going west

                    # record harvesting values
                    if (distance == 0):
                        harvestingValue[workerNumber] = (1.0 / 2.0)
                    else:
                        harvestingValue[workerNumber] = (1.0 / 4.0) * (1.0 / (0.0 + distance))

                    workerNumber += 1  # iterate

            # record clockwise values
            clockwise[0] /= 1000.0
            clockwise[1] /= 1000.0
            clockwise[2] /= 1000.0

            # return
            return 0.5 + foodValue + harvestingValue[0] + harvestingValue[1] + harvestingValue[2] \
                   + clockwise[0] + clockwise[1] + clockwise[2] + QueenValue

        ##
        #
        # description: moderates movement of the queen to avoid harvesting lines and fight off attacks
        #
        # parameter: state: the Gamestate
        #
        ##
        def generateQueenValue(self, state):

            # useful stuff
            me = state.whoseTurn
            enemy = 0
            if (me == 0):
                enemy = 1

            QueenValue = 0.0  # reward for queen movement. returns between 0.00 and 0.36
            myQueen = getAntList(state, me, (QUEEN,))[0]

            # reward Queen for avoiding harvesting lines
            QueenBlockingRow = False  # queen blocking harvesting row
            QueenBlockingCol = False  # queen blocking harvesting column
            # check anthill and tunnel(s)
            for constr in state.inventories[me].constrs:
                if (constr.type == TUNNEL or constr.type == ANTHILL):
                    if (constr.coords[0] == myQueen.coords[0]):
                        QueenBlockingRow = True
                    if (constr.coords[1] == myQueen.coords[1]):
                        QueenBlockingCol = True
            # check food
            for constr in state.inventories[NEUTRAL].constrs:
                if (constr.type == FOOD and constr.coords[1] < 4):
                    if (constr.coords[0] == myQueen.coords[0]):
                        QueenBlockingRow = True
                    if (constr.coords[1] == myQueen.coords[1]):
                        QueenBlockingCol = True
            # set rewards
            if (QueenBlockingRow == True or QueenBlockingCol == True):
                QueenValue = 0.0
            else:
                QueenValue = 0.05

            # reward queen for staying near the anthill ready to defend
            for constr in state.inventories[me].constrs:
                if (constr.type == ANTHILL):
                    if (approxDist(myQueen.coords, constr.coords) > 0):
                        QueenValue += .01 * (1.0 / approxDist(myQueen.coords, constr.coords))

            # reward queen for maneuvering around attacking amry ants, then striking and killing the ant
            # inflicting the first damage. For drones, the Queen kills the drone without taking any damage.
            nearestThreat = None  # nearest enemy threat, if any
            distNearestThreat = 1000  # arbitrarily large

            for ant in state.inventories[enemy].ants:  # for each enemy ant, find nearest threat, if any
                if (ant.type == DRONE or ant.type == SOLDIER or ant.type == R_SOLDIER):
                    if (nearestThreat == None):
                        nearestThreat = ant
                        distNearestThreat = approxDist(myQueen.coords, ant.coords)
                    elif (approxDist(myQueen.coords, ant.coords) < distNearestThreat):
                        nearestThreat = ant

            # move queen if there is a near threat
            if (nearestThreat != None):  # if a threat exists
                antOccupying = False  # occupying anthill/tunnel (or nearly occupying)
                for constr in state.inventories[me].constrs:  # check if threat is occupying
                    if (approxDist(constr.coords, nearestThreat.coords) <= 2):
                        antOccupying = True
                if (myQueen.hasMoved == True and distNearestThreat == 1):  # if queen will attack threatening ant
                    QueenValue += 0.2
                elif (antOccupying == False):  # if anthill or tunnel is not yet threatened, queen runs away and delays game
                    if (nearestThreat.type == DRONE):
                        if (distNearestThreat > 4):
                            QueenValue += 0.1
                    elif (nearestThreat.type == SOLDIER):
                        if (distNearestThreat > 3):
                            QueenValue += 0.1
                    elif (nearestThreat.type == R_SOLDIER):
                        if (distNearestThreat > 5):
                            QueenValue += 0.1
                elif (antOccupying == True):  # if anthill or tunnel is threatened, queen takes immediate action and strikes
                    QueenValue += .1 * (1.0 / approxDist(myQueen.coords, ant.coords))
                    if (myQueen.hasMoved == True and distNearestThreat == 1):  # if queen will attack threatening ant
                        QueenValue += 0.2

            return QueenValue  # return

        ##
        # predictOutcome
        # Description: returns gameState after a move
        #
        # Parameters:
        #   currentState - the current state
        #   move - the move that will be made
        ##
        def predictOutcome(self, currentState, move):
            nextState = currentState.fastclone()

            # This section of code crashes the program :(

            # if (move.moveType == BUILD):
            #    if (move.buildType >= 0):
            #        newAnt = Ant(move.coordList[0], move.buildType, nextState.whoseTurn)
            #        nextState.inventories[nextState.whoseTurn].ants.append(newAnt)
            #        nextState.inventories[nextState.whoseTurn].foodCount -= UNIT_STATS[move.buildType][COST]
            #    else:
            #        #do the same
            #        nextState.inventories[nextState.whoseTurn].constrs.append()
            #        nextState.inventories[nextState.whoseTurn].foodCount -= UNIT_STATS[move.buildType][COST]

            # if move type is move ant, update location, hasMoved, carrying, etc
            if (move.moveType == MOVE_ANT):
                for ant in nextState.inventories[nextState.whoseTurn].ants:  # for each ant
                    if (ant.coords == move.coordList[0]):  # if ant was ant that was moved
                        ant.coords = move.coordList[len(move.coordList) - 1]  # update location
                        ant.hasMoved = True  # update hasMoved

                        # for workers, update isCarrying if they pick up or drop off food, and update food count if drop off
                        if (ant.type == WORKER):  # if worker
                            if (ant.carrying == False):  # if worker is going out to food

                                # if worker lands on a food, pick it up
                                foodCoords = []
                                for constr in nextState.inventories[NEUTRAL].constrs:
                                    if (constr.type == FOOD):
                                        foodCoords.append(constr.coords)
                                for i in range(0, len(foodCoords)):
                                    if (ant.coords == foodCoords[i]):
                                        ant.carrying = True
                            else:  # if worker is returning food

                                # if worker lands on a return point, drop off food and incrememnt food value
                                foodReturns = []
                                for constr in nextState.inventories[nextState.whoseTurn].constrs:
                                    if (constr.type == TUNNEL or constr.type == ANTHILL):
                                        foodReturns.append(constr.coords)
                                for i in range(0, len(foodReturns)):
                                    if (ant.coords == foodReturns):
                                        ant.carrying = False
                                        nextState.inventories[nextState.whoseTurn].foodCount += 1

                        # record queen's attack only if she has moved
                        if (ant.type == QUEEN or ant.type == DRONE or ant.type == SOLDIER or ant.type == R_SOLDIER):
                            enemy = 0
                            if nextState.whoseTurn == 0:
                                enemy = 1
                            hasAttacked = False
                            for enemyAnt in nextState.inventories[enemy].ants:
                                if (UNIT_STATS[ant.type][RANGE] <= approxDist(ant.coords, enemyAnt.coords) and hasAttacked == False):
                                    hasAttacked = True

            return nextState  # return


# Unit Test
#
#ant = []
#ant.append(Ant((6, 6), QUEEN, 0))
#inventories = []
#inventories.append(Inventory(0, ant, None, 6))
#inventories.append(Inventory(1, None, None, 2))
#inventories.append(Inventory(2, None, None, 0))
#currentState = GameState(None, inventories, 3, 0)
#move = Move(MOVE_ANT, [(6, 6), (6, 5,), (6, 4)], None)
#
#result = predictOutcome(currentState, move)
#
#if (result.inventories[0].getQueen.coords == (6,4)):
#    print "Unit Test #1 passed"