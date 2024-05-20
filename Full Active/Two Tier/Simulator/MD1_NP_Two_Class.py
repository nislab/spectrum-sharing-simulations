"""
Simulation of M|D|1 queues with two classes, no preemption, no AR
Classes are denoted as class 0 and class 1 - class 0 is the "priority" class
Uses simpy to dynamically generate events to facilitate extension of implementation
to, Advance Reservation, and Preemptive Resume
Monitors system wait time as statistic of interest

v1: modified to use single value of lambda - plot against classes and not lambda,
for use to extend into further development.
Author: Jonathan Chamberlain, 2018 jdchambo@bu.edu
"""

# import required packages - numpy, scipy, and simpy required to be installed if not present
import math
import numpy as np
import scipy as sp
import scipy.stats as stats
import matplotlib.pyplot as plt
import simpy
import heapq


'''
Simulation Global Parameters
'''
MU = 20 # service rate, inverse of service time.
SERV_TIME = 1/MU # service time - deterministic since this is an M|D|1 queue
SERV_MOMTWO = SERV_TIME**2 # second moment of service
AR_LAMBDA = 18 # mean arrival rate - lambda parameter in queuing formulae
RHO = AR_LAMBDA/MU # load for each run
SIM_TIME = 2*(10**4) # Length of time to run simulation over
FRAC = 0.05 # fraction of time to wait for before collecting statistics
T_START = FRAC*SIM_TIME # time to start collecting statistics at
ITERATIONS = 30 # number of independent simulations
ALPHA = 0.05 # confidence interval is 100*(1-alpha) percent
RSEED = 1869 # base seed for random number generation
CLASSES = 2 # number of classes
THRESHOLD = 0.4 # Probability of being in class 0, all others in class 1

'''
Define Priority Queue class
Taken from SO article: https://stackoverflow.com/questions/19745116/python-implementing-a-priority-queue
'''
class PriorityQueue:
    def __init__(self):
        self.items = []
        
    # push new entries onto the heap, sorted by priority and entry time    
    def push(self, priority, entry):
        heapq.heappush(self.items, (priority, entry))
        
    # pop items from the queue, to get next item for processing
    def pop(self):
        customer = heapq.heappop(self.items)
        return customer
    
    # define empty check
    def empty(self):
        return not self.items


'''
Define simulator class
'''

class Simulate:
    def __init__(self, env, meanAR):
        self.env = env # SimPy Enviornment
        self.meanAR = meanAR # Mean Arrival Rate
        self.total_w = np.zeros(CLASSES) # total of observed wait during monitoring period, per class
        self.n = np.zeros(CLASSES) # total number of observed packets during monitoring period, per class
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
            yield env.timeout(np.random.exponential(1/self.meanAR)) # randomized interarrival rate; numpy expontial defined w/r/t 1/lambda and not lambda
            # add job to queue based on class, identify by current time index
            if np.random.rand() < THRESHOLD:    
                self.q.push(0,env.now)
            else:
                self.q.push(1,env.now)    
            # if server idle, wake it up
            if self.idle:
                self.server_wakeup.succeed() # reactivate server
                self.server_wakeup = env.event() # reset server wakeup trigger
        
    def server(self, env):
        '''
        Packets held in queue pending processing
        '''
        while True:
            self.idle = True
            # if nothing in either queue, put server to sleep - else next part breaks
            if self.q.empty():
                yield self.server_wakeup # yield until reactivation event succeeds
            # serve job at head of queue - Priority queue automatically sorts by priority, then entry into system
            self.next = self.q.pop() # get next customer - tuple of (priority, entry time)
            self.idle = False
            # run job for SERV_TIME units
            yield env.timeout(SERV_TIME)
            # if beyond threshold, record total wait time in queue, add to total_w
            if (env.now > T_START):
                self.total_w[self.next[0]] += (env.now - self.next[1])
                self.n[self.next[0]] += 1

                
'''
main simulator loop
'''
mean_w = np.zeros((ITERATIONS,CLASSES)) # simulated mean wait time, per class
for k in range(ITERATIONS):
    '''
    start simulation
    '''
    np.random.seed(RSEED+k*11) # reseed pRNG
    env = simpy.Environment() # establish SimPy enviornment
    sim = Simulate(env, AR_LAMBDA)
    env.run(until=SIM_TIME)
    '''
    compute average queue length for each class
    '''
    for j in range(CLASSES):
        mean_w[k,j] = sim.total_w[j]/sim.n[j]
        

'''
compute statistics        
'''
sample_mean = np.mean(mean_w, axis=0) # mean result of average queue length for each class
error = np.std(mean_w, axis = 0)*stats.norm.ppf(1-ALPHA/2)/(ITERATIONS**0.5) # confidence intervals

'''
Analytical formulae, used to validate simulation
'''

w = np.zeros(CLASSES) # array of wait times
R = AR_LAMBDA*SERV_MOMTWO/2 # mean residual time
w[0] = R/(1-(THRESHOLD*RHO)) + SERV_TIME # Mean system wait time Class 0 - rho_0 = THRESHOLD*rho is the load for class 0 customers in this system
w[1] = R/((1-(THRESHOLD*RHO))*(1-RHO)) + SERV_TIME # Mean system wait time Class 1 - formula simplified since rho_0 + rho_1 = rho in this system

    
'''    
normalized error of simulation
'''

norm_err = np.zeros(CLASSES)
for i in range(CLASSES):
    norm_err[i] = error[i]/sample_mean[i]
    
print("Normalized Error for each class:\n")
print(norm_err)

'''
plot results
'''

plt.plot(range(CLASSES), w, label='analytical') # analytical results
plt.errorbar(range(CLASSES), sample_mean, yerr = error, fmt = 'x', label = 'simulation') # simulation results with errorbars
plt.title('Comparison of Analytical results to simulation outputs')
plt.xlabel('Class')
plt.ylabel('Mean System Wait Time')
plt.legend()
plt.show()

