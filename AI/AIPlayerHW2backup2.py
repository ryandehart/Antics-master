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
        super(AIPlayer, self).__init__(inputPlayerId, "backup")

    ##
    # getPlacement
    #
    # Description: called during setup phase for each Construction that
    #   must be placed by the player.  These items are: 1 Anthill on
    #   the player's side; 1 tunnel on player's side; 9 grass on the
    #   player's side; and 2 food on the enemy's side.
    #
    #   This setup is written to fool an algorithm that places food as
    #   far away from the tunnel and anthill as possible into placing
    #   the food in the far back where it is easily defended, and it
    #   still only takes 4 turns for a worker to make a full harvest cycle.
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
            return [(3, 1), (6, 2), (0, 3), (1, 3), (2, 3), (3, 3), (0, 2), (9, 0), (9, 1), (8, 3), (9, 3)]
        if currentState.phase == SETUP_PHASE_2:  # stuff on enemy side
            foodPoints = [(4, 6), (5, 6)]  # the places where we will place food
            enemyPlayer = 0
            if currentState.whoseTurn == 0:
                enemyPlayer = 1
            tunnel = getConstrList(currentState, enemyPlayer, (TUNNEL,))[0].coords
            anthill = getConstrList(currentState, enemyPlayer, (ANTHILL,))[0].coords

            # place 2 foods at empty cells
            for i in range(0, 2):
                for x in range(0, 10):
                    for y in range(6, 10):
                        # if the cell is empty, the distance is the greatest so far,
                        # and is not the same cell used for the first food
                        if (currentState.board[x][y].constr == None) and \
                                ((x, y) != foodPoints[0]) and \
                                (min(approxDist(tunnel, (x, y)), approxDist(anthill, (x, y))) >=
                                     approxDist(tunnel, foodPoints[i])):
                            # set point
                            foodPoints[i] = (x, y)
            return foodPoints  # returns the points where food will be placed
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
    # predictOutcome
    # Description: returns gameState after a move
    #
    # Parameters:
    #   currentState - the current state
    #   move - the move that will be made
    ##
    def predictOutcome(self, currentState, move):
        nextState = currentState.fastclone()

        #This section of code crashes the program :(

        #if (move.moveType == BUILD):
        #    if (move.buildType >= 0):
        #        newAnt = Ant(move.coordList[0], move.buildType, nextState.whoseTurn)
        #        nextState.inventories[nextState.whoseTurn].ants.append(newAnt)
        #        nextState.inventories[nextState.whoseTurn].foodCount -= UNIT_STATS[move.buildType][COST]
        #    else:
        #        #do the same
        #        nextState.inventories[nextState.whoseTurn].constrs.append()
        #        nextState.inventories[nextState.whoseTurn].foodCount -= UNIT_STATS[move.buildType][COST]

        if (move.moveType == MOVE_ANT):
            for ant in nextState.inventories[nextState.whoseTurn].ants:
                if (ant.coords == move.coordList[0]):
                    ant.coords = move.coordList[len(move.coordList) - 1]
                    ant.hasMoved = True
                    if (ant.type == WORKER):
                        if (ant.carrying == False):
                            foodCoords = []
                            for constr in nextState.inventories[NEUTRAL].constrs:
                                if (constr.type == FOOD):
                                    foodCoords.append(constr.coords)
                            for i in range(0, len(foodCoords)):
                                if (ant.coords == foodCoords[i]):
                                    ant.carrying = True
                        else:
                            foodReturns = []
                            for constr in nextState.inventories[nextState.whoseTurn].constrs:
                                if (constr.type == TUNNEL or constr.type == ANTHILL):
                                    foodReturns.append(constr.coords)
                            for i in range(0, len(foodReturns)):
                                if (ant.coords == foodReturns):
                                    ant.carrying = False
                                    nextState.inventories[nextState.whoseTurn].foodCount += 1
                    if (ant.type == QUEEN or ant.type == DRONE or ant.type == SOLDIER or ant.type == R_SOLDIER):
                        enemy = 0
                        if nextState.whoseTurn == 0:
                            enemy == 1
                        hasAttacked = False
                        for enemyAnt in nextState.inventories[enemy].ants:
                            if (UNIT_STATS[ant.type][RANGE] <= approxDist(ant.coords,
                                                                          enemyAnt.coords) and hasAttacked == False):
                                self.getAttack(nextState, ant, enemyAnt.coords)
                                hasAttacked = True

        return nextState

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

        foodValue = (1 / 11) * (1 / 10) * (1 / 2) * (
        state.inventories[me].foodCount - state.inventories[enemy].foodCount)

        QueenValue = 0.0
        myQueen = getAntList(state, me, (QUEEN,))[0]
        QueenBlockingRow = False
        QueenBlockingCol = False
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
        if (QueenBlockingRow == True or QueenBlockingCol == True):
            QueenValue = 0.0
        else:
            QueenValue = 0.05

        for constr in state.inventories[me].constrs:
            if (constr.type == ANTHILL):
                if (approxDist(myQueen.coords, constr.coords) > 0):
                    QueenValue += .01 * (1.0 / approxDist(myQueen.coords, constr.coords))

        nearestDrone = None
        distNearestDrone = 1000
        for ant in state.inventories[enemy].ants:
            if (ant.type == DRONE or ant.type == SOLDIER or ant.type == R_SOLDIER):
                if (nearestDrone == None):
                    nearestDrone = ant
                    distNearestDrone = approxDist(myQueen.coords, ant.coords)
                elif (approxDist(myQueen.coords, ant.coords) < distNearestDrone):
                    nearestDrone = ant
        if (nearestDrone != None):
            antOccupying = False
            for constr in state.inventories[me].constrs:
                if (approxDist(constr.coords, nearestDrone.coords) <= 2):
                    antOccupying = True
            if (myQueen.hasMoved == True and distNearestDrone == 1):  # if queen will attack drone
                QueenValue += 0.2
            elif (antOccupying == False):  # if anthill or tunnel is threatened
                if (nearestDrone.type == DRONE):
                    if (distNearestDrone > 4):
                        QueenValue += 0.1
                elif (nearestDrone.type == SOLDIER):
                    if (distNearestDrone > 3):
                        QueenValue += 0.1
                elif (nearestDrone.type == R_SOLDIER):
                    if (distNearestDrone > 5):
                        QueenValue += 0.1
            elif (antOccupying == True):
                QueenValue += .1 * (1.0 / approxDist(myQueen.coords, ant.coords))
                if (myQueen.hasMoved == True and distNearestDrone == 1):  # if queen will attack drone
                    QueenValue += 0.2

        clockwise = [0.0, 0.0, 0.0]
        workerNumber = 0
        for ant in state.inventories[me].ants:
            if (ant.type == WORKER):
                if (ant.carrying == False):
                    bestDistance = 1000
                    bestFoodPoint = (0, 0)
                    for constr in state.inventories[NEUTRAL].constrs:
                        if (constr.type == FOOD):
                            if (approxDist(ant.coords, constr.coords) <= bestDistance):
                                bestDistance = approxDist(ant.coords, constr.coords)
                                bestFoodPoint = constr.coords


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
                    bestDistance = 1000
                    bestReturnPoint = (0, 0)
                    for constr in state.inventories[me].constrs:
                        if (constr.type == TUNNEL or constr.type == ANTHILL):
                            if (approxDist(ant.coords, constr.coords) <= bestDistance):
                                bestDistance = approxDist(ant.coords, constr.coords)
                                bestReturnPoint = constr.coords

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
                workerNumber += 1

        clockwise[0] /= 1000.0
        clockwise[1] /= 1000.0
        clockwise[2] /= 1000.0

        distance = 0
        harvestingValue = [0.0, 0.0, 0.0]
        workerNumber = 0
        for i in range(0, len(state.inventories[me].ants)):
            if (state.inventories[me].ants[i].type == WORKER):
                if (state.inventories[me].ants[i].carrying == False):
                    newAnt = state.inventories[me].ants[i]

                    bestDistance = 1000
                    bestFoodPoint = (0, 0)
                    for constr in state.inventories[NEUTRAL].constrs:
                        if (constr.type == FOOD):
                            if (approxDist(newAnt.coords, constr.coords) <= bestDistance):
                                bestDistance = approxDist(newAnt.coords, constr.coords)
                                bestFoodPoint = constr.coords

                    bestDistanceReturn = 1000
                    bestReturnPoint = (0, 0)
                    for constr in state.inventories[me].constrs:
                        if (constr.type == TUNNEL, constr.type == ANTHILL):
                            if (approxDist(bestFoodPoint, constr.coords) <= bestDistanceReturn):
                                bestDistanceReturn = approxDist(bestFoodPoint, constr.coords)
                                bestReturnPoint = constr.coords
                    distance = bestDistance + bestDistanceReturn
                else:
                    newAnt = state.inventories[me].ants[i]

                    bestDistance = 1000
                    bestReturnPoint = (0, 0)
                    for constr in state.inventories[me].constrs:
                        if (constr.type == TUNNEL or constr.type == ANTHILL):
                            if (approxDist(newAnt.coords, constr.coords) <= bestDistance):
                                bestDistance = approxDist(newAnt.coords, constr.coords)
                                bestReturnPoint = constr.coords
                    distance = approxDist(newAnt.coords, bestReturnPoint)

                if (distance == 0):
                    harvestingValue[workerNumber] = (1.0 / 1.0)
                else:
                    harvestingValue[workerNumber] = (1.0 / 2.0) * (1.0 / (0.0 + distance))
                workerNumber += 1

        return 0.5 + foodValue + harvestingValue[0] + harvestingValue[1] + harvestingValue[2] + clockwise[0] + clockwise[1] + \
               clockwise[2] + QueenValue


    def getMove(self, currentState):
        possibleMoves = listAllMovementMoves(currentState)
        if (len(currentState.inventories[currentState.whoseTurn].ants) <= 3):
            for move in listAllBuildMoves(currentState):
                possibleMoves.append(move)
        possibleMoves.append(Move(END, None, None))
        possibleStates = []
        for move in possibleMoves:
            possibleStates.append(self.predictOutcome(currentState, move))

        bestMoveValue = 0.0
        bestMoveIndex = 0
        index = 0
        for state in possibleStates:
            evaluatedState = self.evaluateState(state)
            if (evaluatedState > bestMoveValue):
                bestMoveValue = evaluatedState
                bestMoveIndex = index
            index += 1

        return possibleMoves[bestMoveIndex]


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