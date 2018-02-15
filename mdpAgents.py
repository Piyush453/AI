# mdpAgents.py
# parsons/20-nov-2017
#
# Version 1
#
# The starting point for CW2.
#
# Intended to work with the PacMan AI projects from:
#
# http://ai.berkeley.edu/
#
# These use a simple API that allow us to control Pacman's interaction with
# the environment adding a layer on top of the AI Berkeley code.
#
# As required by the licensing agreement for the PacMan AI we have:
#
# Licensing Information:  You are free to use or extend these projects for
# educational purposes provided that (1) you do not distribute or publish
# solutions, (2) you retain this notice, and (3) you provide clear
# attribution to UC Berkeley, including a link to http://ai.berkeley.edu.
# 
# Attribution Information: The Pacman AI projects were developed at UC Berkeley.
# The core projects and autograders were primarily created by John DeNero
# (denero@cs.berkeley.edu) and Dan Klein (klein@cs.berkeley.edu).
# Student side autograding was added by Brad Miller, Nick Hay, and
# Pieter Abbeel (pabbeel@cs.berkeley.edu).

# The agent here is was written by Simon Parsons, based on the code in
# pacmanAgents.py

from pacman import Directions
from game import Agent
import api
import random
import game
import util

class MDPAgent(Agent):
       
    # Constructor: this gets run when we first invoke pacman.py
    def __init__(self):                   
        self.GridMap = list()  
        self.curState = list()
        self.newState = list()
        self.reward = 0.04
        self.max_x = self.min_x = self.max_y = self.min_y = 0
        self.ghostState = -2
        self.food = 1
        self.capsule = 2
        self.buffer = 1
    # Gets run after an MDPAgent object is created and once there is
    # game state to access.
    def registerInitialState(self, state):             
        self.assignCorners(state)
        self.GridMap = self.createMap(state)
        
    # This is what gets run in between multiple games
    def final(self, state):        
        self.curState = [list(row) for row in self.GridMap]
    
    def getAction(self, state):
        
        count = 21
        self.updateMap(state)    
        numFood = len(api.food(state))
        while(count > 0):
            change = self.createUtilityMap(state,numFood)                
            if(change):
                break
            count-=1
        legal = api.legalActions(state)        
        if Directions.STOP in legal:
            legal.remove(Directions.STOP)        
        direction = self.findMaxUtility(state, legal)
        return api.makeMove(direction, legal)
    #A function to find and assignt the the corners of the gird
    #@params: self: The object itself
    #@params: state: the current state of the agent
    def assignCorners(self, state):
        for corner in api.corners(state):
            self.min_x = min(self.min_x, corner[0])
            self.max_x = max(self.max_x, corner[0])
            self.min_y = min(self.min_y, corner[1])
            self.max_y = max(self.max_y, corner[1])
    
    #A function to capture the state of the grid and return the updated map
    #@params: self: The object itself
    #@params: state: the current state of the agent
    def createMap(self, state):
        grid=list()                
                           
        for row in range(self.max_x+1):
            rowList = [0]*(self.max_y+1)
            grid.append(rowList)
        
        for food in api.food(state):
            grid[food[0]][food[1]]=self.food        

        for capsule in api.capsules(state):
            grid[capsule[0]][capsule[1]] = self.capsule                                
        
        for ghostState in api.ghostStatesWithTimes(state):
            grid[int(ghostState[0][0])][int(ghostState[0][1])] = self.ghostState if (ghostState[1] < 3) else self.food
            if(util.manhattanDistance(ghostState[0], api.whereAmI(state))<5):
                grid[int(ghostState[0][0])+self.buffer][int(ghostState[0][1])] = -10 if (ghostState[1] < 3) else self.food
                grid[int(ghostState[0][0])][int(ghostState[0][1])+self.buffer] = -10 if (ghostState[1] < 3) else self.food
                grid[int(ghostState[0][0])-self.buffer][int(ghostState[0][1])] = -10 if (ghostState[1] < 3) else self.food
                grid[int(ghostState[0][0])][int(ghostState[0][1])-self.buffer] = -10 if (ghostState[1] < 3) else self.food
            
        for wall in api.walls(state):
            grid[wall[0]][wall[1]] = -10    
            
        return grid
    
    #This function updates the current state of the grid
    #@params: self: The object itself
    #@params: state: the current state of the agent          
    def updateMap(self, state):
        self.curState=self.createMap(state)
        self.newState =[list(row) for row in self.curState]
        
    
    #This function return the utility of an action from one state to the other
    #using the probabilities of the actions that can be performed
    #@params: self: The object itself
    #@params: pLeft: The probability of moving left from the current state
    #@params: pUp: The probability of moving up from the current state
    #@params: pRight: The probability of moving right from the current state
    #@params: pDown: The probability of moving down from the current state
    #@params: pStay: The probability of staying where it is
    #@params: x: Current row of the agent
    #@params: y: Current column of the agent
    def utilitySetter(self, pLeft, pUp, pRight, pDown, pStay, x, y):
        if(self.curState[x-1][y] == -10):
            pStay+=pLeft
            pLeft = 0
        if(self.curState[x][y+1] == -10):
            pStay+=pUp
            pUp = 0
        if(self.curState[x+1][y] == -10):
            pStay+=pRight
            pRight = 0
        if(self.curState[x][y-1] == -10):
            pStay+=pDown
            pDown = 0
        return ((self.curState[x-1][y]*pLeft)+(self.curState[x][y+1]*pUp)+
                (self.curState[x+1][y]*pRight)+(self.curState[x][y-1]*pDown)+
                (self.curState[x][y]*pStay))
    
    #Function that assigns the utilities to the states based on the probability
    #of moving from one state to another. This function also check whether the
    #utilities have changed or not
    #@params: self: The object itself
    #@params: state: Current state of the agent
    #@params: numFood: The number of available food locations
    def createUtilityMap(self, state,numFood):
        change = False
        up = down = right = left = 0
        for i in range(self.min_x+1,len(self.curState)-1):
            for j in range(self.min_y+1,len(self.curState[i])-1):
                #to check whether the agent can move left or not
                if(i-1 == self.min_x):
                    if(j-1 == self.min_y):
                        up = self.utilitySetter(0,0.8,0.1,0,0.1,i,j)
                        down = self.utilitySetter(0,0,0.1,0,0.9,i,j)
                        left = self.utilitySetter(0,0.1,0,0,0.9,i,j)
                        right = self.utilitySetter(0,0.1,0.8,0,0.1,i,j)
                        
                    elif(j+1 == self.max_y):
                        up = self.utilitySetter(0,0,0.1,0,0.9,i,j)
                        down = self.utilitySetter(0,0,0.1,0.8,0.1,i,j)
                        left = self.utilitySetter(0,0,0,0.1,0.9,i,j)
                        right = self.utilitySetter(0,0,0.8,0.1,0.1,i,j)
                    else:
                        up = self.utilitySetter(0.1,0.8,0.1,0,0,i,j)
                        down = self.utilitySetter(0.1,0,0.1,0,0.8,i,j)
                        left = self.utilitySetter(0.8,0.1,0,0,0.1,i,j)
                        right = self.utilitySetter(0,0.1,0.8,0,0.1,i,j)
                elif(i+1 == self.max_x):
                    if(j-1 == self.min_y):
                        up = self.utilitySetter(0.1,0.8,0,0,0.1,i,j)
                        down = self.utilitySetter(0.1,0,0,0,0.9,i,j)
                        left = self.utilitySetter(0.8,0.1,0,0,0.1,i,j)
                        right = self.utilitySetter(0,0.1,0,0,0.9,i,j)
                    elif(j+1 == self.max_y):
                        up = self.utilitySetter(0.1,0,0,0,0.9,i,j)
                        down = self.utilitySetter(0.1,0,0,0.8,0.1,i,j)
                        left = self.utilitySetter(0.8,0,0,0.1,0.1,i,j)
                        right = self.utilitySetter(0,0,0,0.1,0.9,i,j)
                    else:
                        up = self.utilitySetter(0.1,0.8,0,0,0.1,i,j)
                        down = self.utilitySetter(0.1,0,0,0.8,0.1,i,j)
                        left = self.utilitySetter(0.8,0.1,0,0.1,0,i,j)
                        right = self.utilitySetter(0,0.1,0,0.1,0.8,i,j)
                elif(j-1 == self.min_y):
                    up = self.utilitySetter(0.1,0.8,0.1,0,0,i,j)
                    down = self.utilitySetter(0.1,0,0.1,0,0.8,i,j)
                    left = self.utilitySetter(0.8,0.1,0,0,0.1,i,j)
                    right = self.utilitySetter(0,0.1,0.8,0,0.1,i,j)
                elif(j+1 == self.max_y):
                    up = self.utilitySetter(0.1,0,0.1,0,0.8,i,j)
                    down = self.utilitySetter(0.1,0,0.1,0.8,0,i,j)
                    left = self.utilitySetter(0.8,0,0,0.1,0.1,i,j)
                    right = self.utilitySetter(0,0,0.8,0.1,0.1,i,j)
                else:
                    up = self.utilitySetter(0.1,0.8,0.1,0,0,i,j)
                    down = self.utilitySetter(0.1,0,0.1,0.8,0,i,j)
                    left = self.utilitySetter(0.8,0.1,0.1,0,0,i,j)
                    right = self.utilitySetter(0,0.1,0.8,0.1,0,i,j)
            
                if(self.newState[i][j]!=-10 and self.newState[i][j]!=self.ghostState):                                        
                    if(numFood < 5 and self.newState[i][j]!=self.food):
                        self.newState[i][j]=-self.reward + max(up, down, left, right)
                    else:
                        self.newState[i][j]=self.reward + max(up, down, left, right)
                            
        change = self.curState == self.newState
        self.curState = [list(row) for row in self.newState]  
        return change                
    
    #This function returns the utility of the state. If the 
    #@params: self: The object itself
    #@params: x: The row of the agent
    #@params: y: The column of the agent
    def getUtility(self, x, y):
        return self.curState[x][y] if(self.curState[x][y] != -10) else -100
     
    #This function returns the direction in which the utility is the maximum
    #based on the current position of the gaent
    #@params: self: The object itself
    #@params: state: The current state of the agent
    #@params: legal: The leagl directions in which the agent can move
    def findMaxUtility(self, state, legal):
        maxUtility = -10
        direction = Directions.STOP 
        x,y = api.whereAmI(state)                
        if(maxUtility<self.getUtility(x-1,y)):
            maxUtility = self.getUtility(x-1,y)
            direction = Directions.WEST
        if(maxUtility<self.getUtility(x,y+1)):
            maxUtility = self.getUtility(x,y+1)
            direction = Directions.NORTH
        if(maxUtility<self.getUtility(x+1,y)):
            maxUtility = self.getUtility(x+1,y)
            direction = Directions.EAST
        if(maxUtility<self.getUtility(x,y-1)):
            maxUtility = self.getUtility(x,y-1)
            direction = Directions.SOUTH        
        
        return direction
            
            
                    
        