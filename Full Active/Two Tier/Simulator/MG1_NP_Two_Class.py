"""
Simulation of an M|G|1 queue with two priority classes and no preemption
Uses simpy to dynamically generate events 
Classes are denoted as class 0, and class 1. Class 0 is the higher priority class.
This nomenclature is used to ensure proper sort, as SimPy prioirty resource sorts on priority
in ascending order. This also makes storing system flow time information intuitive, as Python is 
zero indexed.

The simulator uses the Gamma distribution for service times, with a hardcoded exception for
the Deterministic distribution for second moment 1/MU^2. This has advantage of seeing how
changing the service distribution changes the results. In addition, Gamma distribution with
SHAPE = 1 corresponds to the Exponential distribution
"""

# import required packages - numpy, scipy, and simpy required to be installed if not present

import math
import numpy as np
import scipy as sp
import scipy.stats as stats
import simpy
import collections
import matplotlib.pyplot as plt


'''
Get input from user for system rate, service rate, fraction of customers in higher class,
and second moment of service. Script expects the input in that order
'''

'''
Define simulation Global Parameters
'''

LAM = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9] # Arrival rates of customers
NUMLAM = len(LAM)
MU = 1 # Service rate of customers; defined as 1 over first moment of service
for l in range(NUMLAM):
    if LAM[l] >= MU:
        print('Unstable system specified. Lambda should be less than Mu.')
        exit()
PHI = 0.5 # float(sys.argv[3]) # Fraction of customers in higher class
if PHI < 0 or PHI > 1:
    print('PHI must be in [0,1]')
    exit()
K = 2# float(sys.argv[4]) # Service Distribution; defined such that second moment of service is K over MU^2
if K < 1:
    print('K must be at least 1')
    exit()
RHO = np.zeros(NUMLAM) # load for each run
for l in range(NUMLAM):
    RHO[l] = LAM[l]/MU 
FRAC = 0.05 # fraction of time to wait for before collecting statistics
ITERATIONS = 10 # number of independent simulations
ALPHA = 0.05 # confidence interval is 100*(1-alpha) percent
# define parameters of Gamma distribution; Numpy uses shape/scale definition
if K > 1:
    SHAPE = 1/(K-1) # Shape of Gamma Distribution
    SCALE = (K-1)/MU # Scale of Gamma Distribution


'''
Create the provider to serve the customers

env - SimPy Enviornment
arrival - the customer's arrival time to the queue
prio - the customer's priority
serv_time - the length of service of the job; randomly generated on arrival
server - tuple featuring the server resource and the wait time statistic collector
t_start - time to begin collection of statistics
'''

def provider(env,arrival,prio,serv_time,t_start,server):
    # yield until the server is available, request with specifed priority
    with server.processor.request(priority=prio) as MyTurn:
        yield MyTurn

        # customer has aquired the server, run job for specified service time
        yield env.timeout(serv_time)

        # Record total system time, if beyond the threshold
        if (env.now > t_start):
            server.wait[prio] += env.now-arrival
            server.n[prio] += 1


'''
Create stream of customers until SIM_TIME reached

env - the SimPy Enviornment
server - tuple featuring the server resource and the wait time statistic collector
rate - arrival rate passed from loop
t_start - time to begin collection of statistics
'''

def arrivals(env, server, rate, t_start):
    while True:
        yield env.timeout(np.random.exponential(1/rate)) # randomized interarrival rate; 
        arrival = env.now # mark arrival time
        decision = np.random.rand() # roll random number between [0,1), determine  whether to purchase premium access
        '''
        priority - customer has option to purchase priority, we assume they do so with probability phi, with the cost to do so
        set at the level that leads to the equilibrium state phi. Class 0 is highest prioirty here, to ensure proper sorting of customers.
        This is not necessarily typical priority convention.
        '''
        if decision <= PHI:
            priority = 0 # customer part of fraction who joined premium class
        else:
            priority = 1 # customer part of fraction who remained in ordinary class
        '''
        serv_time - length of service for customers. Use Gamma Distribution for service times; shape = 1 (K = 2) is special case of 
        Exponential distribution. SHAPE and SCALE are defined such that First moment of service is 1/MU, and second moment is K/MU^2.
        Gamma is not defined for shape, scale <= 0, so instead have hardcoded special case for deterministic 
        '''
        if K == 1: 
            serv_time = 1/MU # Special case for Deterministic system
        else:
            serv_time = np.random.gamma(SHAPE,SCALE)
        # Have server process customer arrival
        env.process(provider(env,arrival,priority,serv_time,t_start,server))

'''
Define supporting structures
'''
Server = collections.namedtuple('Server','processor,wait,n') # define server tuple to pass into arrivals, provider methods
Mean_Wait = np.zeros((ITERATIONS,NUMLAM,2)) # Mean wait time in the class in each iteration

'''
Main Simulator Loop
'''
for l in range(NUMLAM):
    for k in range(ITERATIONS):
        print('Lambda %.3f, Iteration # %d' %(LAM[l],k))
        # create server elements
        env = simpy.Environment() # establish SimPy enviornment
        processor = simpy.PriorityResource(env,capacity=1) # M|G|1 server with priorities, can simulate arbitrary M|G|n by updating capacity
        wait = np.zeros(2)
        n = np.zeros(2)
        rate = LAM[l]
        sim_time = 5*(10**5)/rate # Length of time to run simulation over, scales so that 500000 arrvials created
        t_start = FRAC*sim_time # time to start collecting statistics at
        server = Server(processor,wait,n)
        #start simulation
        env.process(arrivals(env,server,rate,t_start)) 
        env.run(until=sim_time)
        # Record average wait in each class
        Mean_Wait[k,l,0] = wait[0]/n[0]
        Mean_Wait[k,l,1] = wait[1]/n[1]
    
        

'''
Compute Statistics     
'''
Sample_Wait = np.mean(Mean_Wait,axis=0) # Sample Mean of the Wait times
Error = np.std(Mean_Wait, axis=0)*stats.norm.ppf(1-ALPHA/2)/(ITERATIONS**0.5) # confidence interval
print('Statistical Results')
for l in range(NUMLAM):
    print('At arrival rate %f:' %(LAM[l]))
    print('Sample Wait time of Class 0 is %.3f with error %.3f.' %(Sample_Wait[l,0],Error[l,0]))
    print('Sample Wait time of Class 1 is %.3f with error %.3f.' %(Sample_Wait[l,1],Error[l,1]))

'''
Plot Satistical Results against Analytical Expected Values
'''

NPAnalytical_Wait_High = np.zeros(NUMLAM) # Expected wait time of Class 0
NPAnalytical_Wait_Low = np.zeros(NUMLAM) # Expected wait time of Class 1
for l in range(NUMLAM):
    NPAnalytical_Wait_High[l] = (K*RHO[l])/(2*MU*(1-PHI*RHO[l])) + 1/MU 
    NPAnalytical_Wait_Low[l] = (K*RHO[l])/(2*MU*(1-RHO[l])*(1-PHI*RHO[l])) + 1/MU 
plt.plot(LAM,NPAnalytical_Wait_Low, label='Low Class, Analytical') # Plot of Expected Wait Times, class 1
plt.plot(LAM,NPAnalytical_Wait_High, label='High Class, Analytical') # Plot of Expected Wait Times, class 0
plt.errorbar(LAM, Sample_Wait[:,1], yerr=Error[:,1], fmt='x', label='Low Class, Simulated') # Plot of Simulated Wait Times, class 1
plt.errorbar(LAM, Sample_Wait[:,0], yerr=Error[:,0], fmt='x', label='High Class, Simulated') # Plot of Simulated Wait Times, class 0
plt.title('Comparison of Analytical results to simulation outputs (K=%d, MU=%.3f' %(K, MU))
plt.xlabel('Lambda')
plt.ylabel('Mean System Wait Time')
plt.legend()
plt.show()


