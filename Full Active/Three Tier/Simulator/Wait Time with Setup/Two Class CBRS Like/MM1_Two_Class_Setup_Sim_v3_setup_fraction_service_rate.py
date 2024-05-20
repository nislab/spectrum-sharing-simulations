"""
Module to define simulator for M|M|1 queues with two priority classes, preemtive resume behavior, with setup times
Uses simpy to dynamically generate events to facilitate extension of implementation
to Preemptive Resume
v3: changes setup rate to be defined in terms of service time based on updated derived model
also, setup times now impact every customer as they enter service.
Monitors queuing wait time as statistic of interest
Author: Jonathan Chamberlain, 2021 jdchambo@bu.edu
"""

# import required packages - numpy, scipy, and simpy required to be installed if not present
import math
import numpy as np
import scipy as sp
import scipy.stats as stats
import simpy
import heapq
import sys
import csv

def Simulator(LAM, MU, PHI, SIGMA, costfile):
    '''
    LAM - Average arrival rate ("Lambda" is reserved for inline functions in python)
    MU - Service rate 
    PHI - Threshold for making AR
    SIGMA - Setup factor (setup rate = SIGMA*MU)
    costfle - file containing cost and CI data
    '''


    '''
    Simulation Global Parameters
    '''
    RHO = LAM/MU # System Load
    SIM_TIME = 5*(10**5)/LAM # Length of time to run simulation over - scale to avg ~500,000 customers during timeframe
    FRAC = 0.1 # fraction of time to wait for before collecting statistics
    T_START = FRAC*SIM_TIME # time to start collecting statistics at
    ITERATIONS = 30 # number of independent simulations
    ALPHA = 0.05 # confidence interval is 100*(1-alpha) percent
   
    '''
    Define Priority Queue class
    Taken from SO article: https://stackoverflow.com/questions/19745116/python-implementing-a-priority-queue
    '''
    class PriorityQueue:
        def __init__(self):
            self.items = []
        
        # push new entries onto the heap, sorted by priority and entry time - also contains flag for Ghost customers as well as remaining time in service and initial length of service   
        def push(self, priority, entry, service, init):
            heapq.heappush(self.items, (priority, entry, service, init))
        
        # pop items from the queue, to get next item for processing
        def pop(self):
            customer = heapq.heappop(self.items)
            return customer
    
        # define empty check
        def empty(self):
            return not self.items


    '''
    Define simulator enviornment class
    '''

    class SimEnv:
        def __init__(self, env):
            self.env = env # SimPy Enviornment
            self.total_w = np.zeros(2) # total of observed queue wait during monitoring period, per bucket
            self.n = np.zeros(2) # total number of observed packets during monitoring period, per bucket
            self.idle = True # flag to trigger activation event
            self.q = PriorityQueue() # queues of pending customers, starts empty
            self.arrvial_proc = env.process(self.arrivals(env))
            self.server_proc = env.process(self.server(env))
            self.server_wakeup = env.event() # event trigger to wake up idle server

        def arrivals(self, env):
            '''
            Packets arrive at randomized intervals, and are passed to the server queue for processing
            Packets will be created until simulation time has expired
            '''
            while True:
                yield env.timeout(np.random.exponential(1/LAM)) # randomized interarrival rate; numpy expontial defined w/r/t 1/lambda and not lambda
                '''
                Priority determined by rolling random number in the interval (0,1] and comparing to PHI. 
                If less than PHI, priority = 0, is PU 
                If greater than PHI, priority = 1, is SU
                '''
                decision = 1 - np.random.rand()
            
                if decision <= PHI:
                    priority = 0 
                else:
                    priority = 1
                # add arrival to queue, as tuple of (priority, arrival time, service); priority is negated due to tuple sorting rules
                servlen = np.random.exponential(1/MU)
                self.q.push(priority, env.now, servlen, servlen) 
                # if server idle, wake it up
                if self.idle:
                    self.server_wakeup.succeed() # reactivate server
                    self.server_wakeup = env.event() # reset server wakeup trigger
                # otherwise, if new arrival has prioirty over customer currently in service, trigger preemption
                elif(priority < self.next[0]):
                    self.server_proc.interrupt()

        def server(self, env):
            '''
            Serve the packets being held in the queue
            Queue is implemented as a heap, with elements as tuples utilizing standard Python tuple sort
            tuple[0] - Priority: 0 for PU, 1 for SU
            tuple[1] - Arrival Time: non negative float, representing initial arrival time to the queue
            tuple[2] - service: remaining service time
            tuple[3] - init: the initial length of service
            '''
            while True:
                if self.q.empty():
                    # idle period, sleep until next arrival, perform initial setup
                    self.idle = True
                    yield self.server_wakeup # yield until reactivation event succeeds
                    self.idle = False
                self.next = self.q.pop() # get next customer - tuple of (priority, entry time)
                '''
                Run job for length of service units; if beyond threshold, record wait time in queue on complietion
                '''
                try:
                    # setup time
                    inSetup = True
                    yield env.timeout(np.random.exponential(1/(SIGMA*MU))) 
                    # service period
                    inSetup = False
                    start = env.now
                    yield env.timeout(self.next[2])
                    if (env.now > T_START):
                        self.total_w[self.next[0]] += (env.now - (self.next[1] + self.next[3])) # total wait time is exit time - initial queue entry - service time
                        self.n[self.next[0]] += 1
                except simpy.Interrupt:
                    # current job interrupted by higher priority arrival, reinsert into queue with time remaining updated
                    if inSetup:
                        self.q.push(self.next[0],self.next[1], self.next[2], self.next[3]) # decrement time remaining by amount of time passed
                    else:
                        self.q.push(self.next[0],self.next[1], self.next[2]-(env.now-start), self.next[3]) # decrement time remaining by amount of time passed
                        

    '''
    main simulator loop
    '''
    costs = np.zeros(ITERATIONS)
    for k in range(ITERATIONS):
        '''
        start simulation
        '''
        env = simpy.Environment() # establish SimPy enviornment
        sim = SimEnv(env)
        env.run(until=SIM_TIME)
        '''
        compute corresponding cost
        '''
        costs[k] = (sim.total_w[1]/sim.n[1]) - (sim.total_w[0]/sim.n[0]) # cost is dfference in wait times as SU - wait times as PU
        

    '''
    compute statistics, save to file        
    '''
    mean_C = np.mean(costs) # mean costs
    error_C = np.std(costs)*stats.norm.ppf(1-ALPHA/2)/(ITERATIONS**0.5) # confidence interval
    C = [mean_C, error_C]
    with open(costfile, 'a') as costout:
        writer = csv.writer(costout, lineterminator='\n')
        writer.writerow(C)
