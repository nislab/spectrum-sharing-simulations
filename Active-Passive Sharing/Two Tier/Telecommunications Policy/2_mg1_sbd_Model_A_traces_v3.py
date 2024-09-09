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
LAM = [0.0423,0.0465,0.0507,0.0550,0.0592,0.0634,0.0676] # Arrival rates of customers
NUMLAM = len(LAM)
MU = 0.101464 # Service rate of customers; defined as 1 over first moment of service

# Define parameters of server breakdowns
LAMBDA_IN = 0.00027 # (exponential) rate at which server breaks down
MU_IN = 0.04 #rate at which server gets repaired

FM_EFF = (1/MU)*(1+LAMBDA_IN/MU_IN) #Effective First Moment of Service Time (cf Eq. 9 in https://ieeexplore.ieee.org/abstract/document/6776591)
MU_EFF = 1/FM_EFF #Effective mean service rate of customers

# import the csv files of the variables 
IN_ARRIVALS = [] # technically the lengths of interarrival periods; used to force server to wait specified interarrival time before next arrival
with open('interarrivalTimes.csv',newline='') as f:
    reader = csv.reader(f,quoting=csv.QUOTE_NONNUMERIC)
    for row in reader:
        IN_ARRIVALS.extend(row)
f.close()
IN_SERVICE = []
with open('overpassTimes.csv',newline='') as f:
    reader = csv.reader(f,quoting=csv.QUOTE_NONNUMERIC)
    for row in reader:
        IN_SERVICE.extend(row)
f.close()

for l in range(NUMLAM):
    if LAM[l] >= MU_EFF:
        print('Unstable system specified. Lambda should be less than Mu.')
        exit()

RHO = np.zeros(NUMLAM) # load for each run
for l in range(NUMLAM):
    RHO[l] = LAM[l]/MU_EFF 
FRAC = 0.1 # fraction of time to wait for before collecting statistics
ITERATIONS = 30 # number of independent simulations
ALPHA = 0.05 # confidence interval is 100*(1-alpha) percent


K = 1.67 # Service Distribution; defined such that second moment of service is K over MU^2
if K < 1:
    print('K must be at least 1')
    exit()
# define parameters of Gamma distribution for customers; Numpy uses shape/scale definition
if K > 1:
    SHAPE = 1/(K-1) # Shape of Gamma Distribution
    SCALE = (K-1)/MU # Scale of Gamma Distribution

K_IN = 1.17 # Service Repair Distribution; defined such that second moment of service is K_IN over MU_IN^2
if K_IN < 1:
    print('K_IN must be at least 1')
    exit()

# define parameters of Gamma distribution for server repair; Numpy uses shape/scale definition
if K_IN > 1:
    SHAPE_IN = 1/(K_IN-1) # Shape of Gamma Distribution
    SCALE_IN = (K_IN-1)/MU_IN # Scale of Gamma Distribution

FM = 1/MU #first moment of service time of customers (without interruptions)
SM = K/(MU**2)   #second moment of service time of customers (without interruptions)
FM_IN = 1/MU_IN #first moment of server repair time
SM_IN = K_IN/(MU_IN**2) #Second moment of server repair time    



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
        tmp = np.int_([1])
        if prio==0:
            tmp[0]=0
        server.wait[tmp[0]] += env.now-arrival
        server.n[tmp[0]] += 1
        server.preemptions[tmp[0]] += preemption
        


'''
Create stream of customers until SIM_TIME reached

env - the SimPy Enviornment
server - tuple featuring the server resource and the wait time statistic collector
rate - arrival rate passed from loop
t_start - time to begin collection of statistics
'''

def arrivals_SU(env, server, rate, t_start):
    while True:
        yield env.timeout(np.random.exponential(1/rate)) # exponential interarrival rate; 
        arrival = env.now # mark arrival time
        priority = 1 # regular customer arrival
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
Mean_Wait = np.zeros((ITERATIONS,NUMLAM,2)) # Mean wait time in the class in each iteration
Mean_Preempt = np.zeros((ITERATIONS,NUMLAM,2)) # Mean preemptions for each class

'''
Main Simulator Loop
'''
for l in range(NUMLAM):
    for k in range(ITERATIONS):
        print('Lambda %.3f, Iteration # %d' %(LAM[l],k))
        # create server elements
        env = simpy.Environment() # establish SimPy enviornment
        processor = simpy.PreemptiveResource(env,capacity=1) # M|G|1 server with priorities, can simulate arbitrary M|G|n by updating capacity
        wait = np.zeros(2)
        n = np.zeros(2)
        preempt = np.zeros(2)
        rate_PU = LAMBDA_IN
        rate_SU = LAM[l] # total arrival rate of events (customers or server breakdowns)
        sim_time = 5266763 # sim over sample collection period ~2 months in length, in seconds
        t_start = FRAC*sim_time # time to start collecting statistics at
        server = Server(processor,wait,n,preempt)
        #start simulation
        env.process(arrivals_PU(env,server,rate_PU,t_start))
        env.process(arrivals_SU(env,server,rate_SU,t_start))
        env.run(until=sim_time)
        # Record average wait in each class
        Mean_Wait[k,l,0] = wait[0]/n[0]
        Mean_Preempt[k,l,0] = preempt[0]/n[0]
        Mean_Wait[k,l,1] = wait[1]/n[1]
        Mean_Preempt[k,l,1] = preempt[1]/n[1]
      

'''
Compute Statistics     
'''
Sample_Wait = np.mean(Mean_Wait,axis=0) # Sample Mean of the Wait times
Error = np.std(Mean_Wait, axis=0, ddof=1)*stats.norm.ppf(1-ALPHA/2)/(ITERATIONS**0.5) # confidence interval
Sample_Preempt = np.mean(Mean_Preempt,axis=0)
Err_Preempt = np.std(Mean_Preempt,axis=0)*stats.norm.ppf(1-ALPHA/2)/(ITERATIONS**0.5)
# Save results to file
print('Statistical Results')
for l in range(NUMLAM):
    print('At arrival rate %f:' %(LAM[l]))
    print('Sample Wait time of Class 0 is %.3f with error %.3f.' %(Sample_Wait[l,0],Error[l,0]))
    print('Sample Wait time of Class 1 is %.3f with error %.3f.' %(Sample_Wait[l,1],Error[l,1]))

with open('eess_data.csv','a', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(Sample_Wait[:,0])
    writer.writerow(Error[:,0])
    writer.writerow(Sample_Preempt[:,0])
    writer.writerow(Err_Preempt[:,0])
f.close()
with open('customer_data.csv','a', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(Sample_Wait[:,1])
    writer.writerow(Error[:,1])
    writer.writerow(Sample_Preempt[:,1])
    writer.writerow(Err_Preempt[:,1])
f.close()



