"""
Simulation of an M|G|1 queue with server breakdowns, modified to accept data from radiometer traces
Classes are denoted as class 0, and class 1. Class 0 arrivals belong to the higher priority class and
represent server breakdowns.
This nomenclature is used to ensure proper sort, as SimPy prioirty resource sorts on priority
in ascending order. This also makes storing system flow time information intuitive, as Python is 
zero indexed.

The simulator uses the Gamma distribution for both service and server repair times, with a hardcoded exception for
the Deterministic distribution for second moment 1/MU^2 and 1/MU_IN^2. This has advantage of seeing how
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
import csv
import os

'''
Get input from user for system rate, service rate, and second moment of service. Script expects the input in that order
'''

'''
Define simulation Global Parameters
'''

# Customer parameter definitions
LAM = 0.13802 # Arrival rate of customers
MU = 0.1546 # Service rate of customers; defined as 1 over first moment of service
if LAM >= MU:
    print('Unstable system specified. Lambda should be less than Mu.')
    exit()
RHO = LAM/MU # Traffic load for each run
K = 1.4897 # Service Distribution; defined such that second moment of service is K over MU^2
if K < 1:
    print('K must be at least 1')
    exit()
# define parameters of Gamma distribution for customers; Numpy uses shape/scale definition
if K > 1:
    SHAPE = 1/(K-1) # Shape of Gamma Distribution
    SCALE = (K-1)/MU # Scale of Gamma Distribution

PHI = 1 # Initial strategy
Cp = 100 # Cost of preemption
F = 650 # Fee to join primary queue
FRAC = 0.1 # fraction of time to wait for before collecting statistics
ROUNDS = 10 # number of rounds to play the game over
ITERATIONS = 30 # number of independent simulations
ALPHA = 0.05 # confidence interval is 100*(1-alpha) percent; also used to deterime how many customers change strategy each round

# import the csv files of the variables 
IN_ARRIVALS = [] # technically the lengths of interarrival periods; used to force server to wait specified interarrival time before next arrival
with open('interArrival.csv',newline='') as f:
    reader = csv.reader(f,quoting=csv.QUOTE_NONNUMERIC)
    for row in reader:
        IN_ARRIVALS.extend(row)
f.close()
IN_SERVICE = []
with open('sweepPeriod.csv',newline='') as f:
    reader = csv.reader(f,quoting=csv.QUOTE_NONNUMERIC)
    for row in reader:
        IN_SERVICE.extend(row)
f.close()

# Define parameters of server breakdowns
LAMBDAs = 1/np.mean(IN_ARRIVALS,axis=0) # (exponential) rate at which server breaks down
MUs = 1/np.mean(IN_SERVICE,axis=0) #rate at which server gets repaired
RHOs = LAMBDAs/MUs
Ks = 1+np.var(IN_SERVICE,axis=0)*(MUs**2) # Service Distribution; defined such that second moment of service is Ks over MUs^2

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
    # continue looping until job complete
    notDone = True
    preemption = 0
    while notDone:
        # yield until the server is available, request with specifed priority
        with server.processor.request(priority=prio) as MyTurn:
            yield MyTurn
            # customer has aquired the server, run job for specified service time
            start = env.now
            try:
                yield env.timeout(serv_time)
                notDone = False # job complete, reverse flag to exit loop
            except simpy.Interrupt:
                # process preempted, adjust remaining service time by how much longer job has remaining
                serv_time -= (env.now-start)
                prio -= 0.0001  #ensure that preempted job has higher priority
                preemption += 1 

    # Record total system time, if beyond the threshold
    if (env.now > t_start):
        tmp = np.int_(np.ceil(prio))
        if prio==0:
            tmp=0
        server.wait[tmp] += env.now-arrival
        server.n[tmp] += 1
        server.preemptions[tmp] += preemption
        


'''
Create stream of customers until SIM_TIME reached

env - the SimPy Enviornment
server - tuple featuring the server resource and the wait time statistic collector
rate - arrival rate passed from loop
t_start - time to begin collection of statistics
'''

def arrivals_SU(env, server, rate, t_start,phi):
    while True:
        yield env.timeout(np.random.exponential(1/rate)) # exponential interarrival rate; 
        arrival = env.now # mark arrival time
        # random draw for higher vs lower class
        decision = 1 - np.random.rand()
        if decision <= phi:
            priority = 1 # User is Priority class customer
        else:
            priority = 2 # User is Ordinary class customer
        if K == 1: 
            serv_time = 1/MU # Special case for Deterministic system
        else:
            serv_time = np.random.gamma(SHAPE,SCALE)
        env.process(provider(env,arrival,priority,serv_time,t_start,server))   


def arrivals_PU(env, server, rate, t_start):
    off_time = 0 # initial arrival in period is not preceeded by PU interruption
    i = 0
    while True:
        #get next arrival
        on_time = IN_ARRIVALS[i]
        # get next on period from 
        yield env.timeout(off_time+on_time) # general off time + exponential on time 
        arrival = env.now # mark arrival time
        priority = 0 # PU arrival
        serv_time = IN_SERVICE[i]
        off_time = serv_time
        env.process(provider(env,arrival,priority,serv_time,t_start,server))
        i = (i+1)%len(IN_SERVICE)   

'''
Define supporting structures
'''
Server = collections.namedtuple('Server','processor,wait,n,preemptions') # define server tuple to pass into arrivals, provider methods
workingdir = os.getcwd() # absolute path to current directory
resultout = os.path.join(workingdir, 'results.csv') # create new csv file
with open(resultout,'a') as file:
    writer = csv.writer(file, lineterminator='\n')
    writer.writerow([PHI,0])
file.close()
'''
Main Simulator Loop
'''
for r in range(ROUNDS):
    print('Round # %d' %(r))
    PHIsim = np.zeros((ITERATIONS))
    for k in range(ITERATIONS):
        # create server elements
        env = simpy.Environment() # establish SimPy enviornment
        processor = simpy.PreemptiveResource(env,capacity=1) # M|G|1 server with priorities, can simulate arbitrary M|G|n by updating capacity
        wait = np.zeros(3)
        n = np.zeros(3)
        preempt = np.zeros(3)
        rate_PU = LAMBDAs
        rate_SU = LAM # total arrival rate of events (customers or server breakdowns)
        sim_time = 2486465 # sim over sample collection period ~1 month in length, in seconds
        t_start = FRAC*sim_time # time to start collecting statistics at
        server = Server(processor,wait,n,preempt)
        #start simulation
        env.process(arrivals_PU(env,server,rate_PU,t_start))
        env.process(arrivals_SU(env,server,rate_SU,t_start,PHI))
        env.run(until=sim_time)
        # Record average wait in each class
        # use expected values if 0 customers in a class; occurs if PHI at or near 0,1
        if n[1] == 0:
            DP = 1/(MU*(1-RHOs)) + (Ks*RHOs/MUs+0.00001*K*RHO/MU)/(2*(1-RHOs)*(1-(RHOs+0.00001*RHO)))
            nPP = LAMBDAs/MU
        else:
            DP = wait[1]/n[1]
            nPP = preempt[1]/n[1]
        if n[2] == 0:
            DS = 1/(MU*(1-(RHOs+0.99999*RHO))) + (Ks*RHOs/MUs+K*RHO/MU)/(2*(1-(RHOs+0.99999*RHO))*(1-(RHOs+RHO)))
            nPS = (LAMBDAs+0.99999*LAM)/MU
        else:
            DS = wait[2]/n[2]
            nPS = preempt[2]/n[2]
        # Update PHI
        if F < (DS + Cp*nPS) - (DP + Cp*nPP):
            # primary better off, increase PHI
            PHIsim[k] = min(PHI+ALPHA*(1-PHI),1)
        elif F > (DS + Cp*nPS) - (DP + Cp*nPP) :
            # secondary better off, decrease PHI
            PHIsim[k] = max(PHI-ALPHA*PHI,0)
    PHI = np.mean(PHIsim,axis=0) 
    PHIerr = np.std(PHIsim,axis=0)*stats.norm.ppf(1-ALPHA/2)/(ITERATIONS**0.5)
    # write to file
    with open(resultout,'a') as file:
        writer = csv.writer(file, lineterminator='\n')
        writer.writerow([PHI,PHIerr])
    file.close() 



