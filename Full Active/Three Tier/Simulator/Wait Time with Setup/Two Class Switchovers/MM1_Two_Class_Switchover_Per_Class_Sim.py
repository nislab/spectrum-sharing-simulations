"""
Module to define simulator for M|M|1 queues with two priority classes, preemtive resume behavior, with 
a swithover period following the busy period of the higher priority customers.
Monitors queuing wait time as statistic of interest
Saves off wait times per class in separate files
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




def Simulator(LAM, MU, PHI, SIGMA, PUfile, GUfile):
    '''
    LAM - Average arrival rate ("Lambda" is reserved for inline functions in python)
    MU - Service rate 
    PHI - Threshold for making AR
    SIGMA - Switchover rate
    PUfile, GUfile - files containing wait time and CI data per class
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
    EPSILON = .00001 # epsilon of interval to determine cost
   
    '''
    Define Priority Queue class
    Taken from SO article: https://stackoverflow.com/questions/19745116/python-implementing-a-priority-queue
    '''
    class PriorityQueue:
        def __init__(self):
            self.items = []
        
        # push new entries onto the heap, sorted by priority and entry time  
        def push(self, priority, entry, service):
            heapq.heappush(self.items, (priority, entry, service))
        
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
            self.q = PriorityQueue() # queues of pending customers, starts empty
            # arrays to store cummulative flow times per class, and total number of customers per class
            self.total_w = np.zeros(2) 
            self.n = np.zeros(2)
            # Flags to indicate triggers for events
            self.idle = True # mark sleeping server
            self.PUperiod = False # mark PU busy period
            self.Switchover = False # mark switchover
            self.PUcount = 0 # count of primary users currently present, used to trigger switchover
            # Process arrivals and server
            self.arrvial_proc = env.process(self.arrivals(env))
            self.server_proc = env.process(self.server(env))
            self.server_wakeup = env.event() # event trigger for server wakeup

        def arrivals(self, env):
            '''
            Packets arrive at randomized intervals, and are passed to the server queue for processing
            Packets will be created until simulation time has expired
            '''
            while True:
                yield env.timeout(np.random.exponential(1/LAM)) # randomized interarrival times; numpy expontial defined in terms of scale, which is inverse of rate
                '''
                Priority determined by rolling random number in the interval (0,1] and comparing to PHI. 
                If less than (or equal to) PHI, priority = 0, is PU 
                If greater than PHI, priority = 1, is GU
                '''
                decision = 1 - np.random.rand() # random.rand is defined in [0,1) so subtraction used to flip the half open interval
                if decision <= PHI:
                    priority = 0 
                else:
                    priority = 1
                # add arrival to queue, as tuple of (priority, arrival time, service length)
                servlen = np.random.exponential(1/MU)
                self.q.push(priority, env.now, servlen)
                # Keep running count of PUs in queue to determine whether to trigger switchover
                if priority == 0:
                    self.PUcount += 1
                # if server idle, wake it up
                if self.idle:
                    self.server_wakeup.succeed() # reactivate server
                    self.server_wakeup = env.event() # reset server wakeup trigger
                # otherwise, if new arrival has prioirty over customer currently in service, trigger preemption
                elif(priority < self.next[0]):
                    self.server_proc.interrupt()
                # otherwise, if in middle of switchover period and PU arrives, trigger interuption    
                elif(self.Switchover and priority == 0):
                    self.server_proc.interrupt()

        def server(self, env):
            '''
            Serve the packets being held in the queue
            Queue is implemented as a heap, with elements as tuples utilizing standard Python tuple sort
            tuple[0] - Priority: 0 for PU, 1 for SU
            tuple[1] - Arrival Time: non negative float, representing initial arrival time to the queue
            tuple[2] - service: remaining service time
            '''
            while True:
                # idle period, sleep until next arrival (otherwise, breaks when attempting to pop from queue)
                if self.q.empty():
                    self.idle = True
                    yield self.server_wakeup # yield until reactivation event succeeds 
                    self.idle = False
                self.next = self.q.pop() # get next customer
                # If PU customer and not currently in a PUperiod, indicate start of new PU busy period by resetting flag
                if (self.next[0] == 0 and not self.PUperiod):
                    self.PUperiod = True
                # Service the current customer
                start = env.now # record start of current customer's service; do so outside try block to avoid computation errors if preempted 
                try:
                    yield env.timeout(self.next[2]) # serve customer for remaining service length
                    # if beyond threshold, record the total flow time (i.e. current time - entry time)
                    if (env.now > T_START):
                        self.total_w[self.next[0]] += (env.now - self.next[1])
                        self.n[self.next[0]] += 1
                        # if PU customer exiting system, indicate as such
                        if self.next[0] == 0:
                            self.PUcount -= 1
                except simpy.Interrupt:
                    # current job interrupted by higher priority arrival, reinsert into queue with time remaining updated
                    self.q.push(self.next[0],self.next[1], self.next[2]-(env.now-start)) # decrement time remaining by amount of time passed
                # if end of a PU bus period, initiate the switchover, which is subject to preemption
                if (self.PUperiod and self.PUcount == 0):
                    try:
                        self.PUperiod = False
                        self.Switchover = True
                        yield env.timeout(np.random.exponential(1/SIGMA))
                        self.Switchover = False                      
                    except simpy.Interrupt:
                        # Switchover preempted; because switchover is Preemptive Repeat, do not need to save off time remaining
                        self.Switchover = False
                        

    '''
    main simulator loop
    '''
    puwait = np.zeros(ITERATIONS)
    guwait = np.zeros(ITERATIONS)
    for k in range(ITERATIONS):
        '''
        start simulation
        '''
        env = simpy.Environment() # establish SimPy enviornment
        sim = SimEnv(env) # pass SimPy enviornment into our defined class
        env.run(until=SIM_TIME)
        '''
        compute average waits per class
        '''
        puwait[k] = sim.total_w[0]/sim.n[0] 
        guwait[k] = sim.total_w[1]/sim.n[1]
        

    '''
    compute statistics, save to file        
    '''
    #PU Statistics
    mean_PUW = np.mean(puwait) # mean 
    error_PUW = np.std(puwait)*stats.norm.ppf(1-ALPHA/2)/(ITERATIONS**0.5) # confidence interval
    PUW = [mean_PUW, error_PUW]
    with open(PUfile, 'a') as waitout:
        writer = csv.writer(waitout, lineterminator='\n')
        writer.writerow(PUW)
    waitout.close()
    #GU Statistics
    mean_GUW = np.mean(guwait) # mean 
    error_GUW = np.std(guwait)*stats.norm.ppf(1-ALPHA/2)/(ITERATIONS**0.5) # confidence interval
    GUW = [mean_GUW, error_GUW]
    with open(GUfile, 'a') as waitout:
        writer = csv.writer(waitout, lineterminator='\n')
        writer.writerow(GUW)
    waitout.close()