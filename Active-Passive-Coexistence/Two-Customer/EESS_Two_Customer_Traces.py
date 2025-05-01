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

'''
Get input from user for system rate, service rate, and second moment of service. Script expects the input in that order
'''

'''
Define simulation Global Parameters
'''

# Customer parameter definitions
# LAM = 0.1256 # Arrival rate of customers
# LAM = 0.13802 # Arrival rate of customers
LAM = 0.14494 # Arrival rate of customers
MU = 0.1546 # Service rate of customers; defined as 1 over first moment of service
K = 1.4897 # Service Distribution; defined such that second moment of service is K over MU^2
PHI = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]
NUMPHI = len(PHI)

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
LAMBDA_IN = 0.0003 # (exponential) rate at which server breaks down
MU_IN = 0.0374 #rate at which server gets repaired

FM_EFF = (1/MU)*(1+LAMBDA_IN/MU_IN) #Effective First Moment of Service Time (cf Eq. 9 in https://ieeexplore.ieee.org/abstract/document/6776591)
MU_EFF = 1/FM_EFF #Effective mean service rate of customers

if LAM >= MU_EFF:
    print('Unstable system specified. Lambda should be less than Mu.')
    exit()

RHO = LAM/MU_EFF # load for each run
FRAC = 0.1 # fraction of time to wait for before collecting statistics
ITERATIONS = 30 # number of independent simulations
ALPHA = 0.05 # confidence interval is 100*(1-alpha) percent
if K < 1:
    print('K must be at least 1')
    exit()
# define parameters of Gamma distribution for customers; Numpy uses shape/scale definition
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
Mean_Wait = np.zeros((ITERATIONS,NUMPHI,3)) # Mean wait time in the class in each iteration
Mean_Preempt = np.zeros((ITERATIONS,NUMPHI,3)) # Mean preemptions for each class

'''
Main Simulator Loop
'''
for l in range(NUMPHI):
    for k in range(ITERATIONS):
        print('Phi %.1f, Iteration # %d' %(PHI[l],k))
        # create server elements
        env = simpy.Environment() # establish SimPy enviornment
        processor = simpy.PreemptiveResource(env,capacity=1) # M|G|1 server with priorities, can simulate arbitrary M|G|n by updating capacity
        wait = np.zeros(3)
        n = np.zeros(3)
        preempt = np.zeros(3)
        rate_PU = LAMBDA_IN
        rate_SU = LAM # total arrival rate of events (customers or server breakdowns)
        phi = PHI[l] # fraction of customers in higher class
        sim_time = 2486465 # sim over sample collection period ~1 month in length, in seconds
        t_start = FRAC*sim_time # time to start collecting statistics at
        server = Server(processor,wait,n,preempt)
        #start simulation
        env.process(arrivals_PU(env,server,rate_PU,t_start))
        env.process(arrivals_SU(env,server,rate_SU,t_start,phi))
        env.run(until=sim_time)
        # Record average wait in each class
        Mean_Wait[k,l,0] = wait[0]/n[0]
        Mean_Preempt[k,l,0] = preempt[0]/n[0]
        Mean_Wait[k,l,1] = wait[1]/n[1]
        Mean_Preempt[k,l,1] = preempt[1]/n[1]
        Mean_Wait[k,l,2] = wait[2]/n[2]
        Mean_Preempt[k,l,2] = preempt[2]/n[2]
      

'''
Compute Statistics     
'''
Sample_Wait = np.mean(Mean_Wait,axis=0) # Sample Mean of the Wait times
Error = np.std(Mean_Wait, axis=0, ddof=1)*stats.norm.ppf(1-ALPHA/2)/(ITERATIONS**0.5) # confidence interval
Sample_Preempt = np.mean(Mean_Preempt,axis=0)
Err_Preempt = np.std(Mean_Preempt,axis=0)*stats.norm.ppf(1-ALPHA/2)/(ITERATIONS**0.5)
# Save results to file
with open('passive_incumbent_data.csv','a', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(Sample_Wait[:,0])
    writer.writerow(Error[:,0])
    writer.writerow(Sample_Preempt[:,0])
    writer.writerow(Err_Preempt[:,0])
f.close()
with open('premium_customer_data.csv','a', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(Sample_Wait[:,1])
    writer.writerow(Error[:,1])
    writer.writerow(Sample_Preempt[:,1])
    writer.writerow(Err_Preempt[:,1])
f.close()
with open('standard_customer_data.csv','a', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(Sample_Wait[:,2])
    writer.writerow(Error[:,2])
    writer.writerow(Sample_Preempt[:,2])
    writer.writerow(Err_Preempt[:,2])
f.close()



