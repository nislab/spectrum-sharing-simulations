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
#import matplotlib.pyplot as plt
import csv

'''
Get input from user for system rate, service rate, and second moment of service. Script expects the input in that order
'''

'''
Define simulation Global Parameters
'''

# Customer parameter definitions
LAM = [0.13035,0.13189,0.13342,0.13495,0.13649,0.13802,0.13955,0.14109,0.14262,0.14416,0.14569] # Arrival rates of customers
NUMLAM = len(LAM)
MU = 0.1546 # Service rate of customers; defined as 1 over first moment of service

# Define parameters of server breakdowns
LAMBDA_IN = 0.0003 # (exponential) rate at which server breaks down
MU_IN = 0.037 #rate at which server gets repaired

FM_EFF = (1/MU)*(1+LAMBDA_IN/MU_IN) #Effective First Moment of Service Time (cf Eq. 9 in https://ieeexplore.ieee.org/abstract/document/6776591)
MU_EFF = 1/FM_EFF #Effective mean service rate of customers

# import the csv files of the variables 
IN_ARRIVALS = []
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


K = 1.4897# float(sys.argv[4]) # Service Distribution; defined such that second moment of service is K over MU^2
if K < 1:
    print('K must be at least 1')
    exit()
# define parameters of Gamma distribution for customers; Numpy uses shape/scale definition
if K > 1:
    SHAPE = 1/(K-1) # Shape of Gamma Distribution
    SCALE = (K-1)/MU # Scale of Gamma Distribution

K_IN = 2.1077 # Service Repair Distribution; defined such that second moment of service is K_IN over MU_IN^2
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


    # if server repaired, reset server working status
    #if prio == 0 and server.broken[0] == True:
    #    server.broken[0] = False

    # Record total system time, if beyond the threshold
    if (env.now > t_start):
        tmp = np.int_([1])
        if prio==0:
            tmp[0]=0
        server.wait[tmp[0]] += env.now-arrival
        server.n[tmp[0]] += 1

        #debug code
        #if prio==1:   
        #    if server.status[0] < 10000:
        #        delay = env.now-arrival
        #        server.status[0] += 1
        #        array_index = int(server.status[0])
        #        server.status[array_index] = delay
        


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
    #special case for first pass as trace period starts with satellite pass in progress
    off_time = 0 
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
Server = collections.namedtuple('Server','processor,wait,n,broken,status') # define server tuple to pass into arrivals, provider methods
Mean_Wait = np.zeros((ITERATIONS,NUMLAM,2)) # Mean wait time in the class in each iteration

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
        status=np.zeros(10001) # Used for debugging
        broken = np.array([False],dtype=bool)
        rate_PU = LAMBDA_IN
        rate_SU = LAM[l] # total arrival rate of events (customers or server breakdowns)
        sim_time = 2592000 # sim over a month's worth of arrivals, in minutes
        # sim_time = (10**5)/min(LAM[l],LAMBDA_IN) # Length of time to run simulation over, scales so that 100000 arrvials created
        t_start = FRAC*sim_time # time to start collecting statistics at
        server = Server(processor,wait,n,broken,status)
        #start simulation
        env.process(arrivals_PU(env,server,rate_PU,t_start))
        env.process(arrivals_SU(env,server,rate_SU,t_start))
        env.run(until=sim_time)
        # Record average wait in each class
        Mean_Wait[k,l,0] = wait[0]/n[0]
        Mean_Wait[k,l,1] = wait[1]/n[1]

        # Debug code
        #server_broken_time = 1-status[1]/status[0]
        #mean_wait_time = np.mean(status[1:])
        #print('mean wait time %.3f' %mean_wait_time)
      

'''
Compute Statistics     
'''
Sample_Wait = np.mean(Mean_Wait,axis=0) # Sample Mean of the Wait times
Error = np.std(Mean_Wait, axis=0, ddof=1)*stats.norm.ppf(1-ALPHA/2)/(ITERATIONS**0.5) # confidence interval

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
f.close()
with open('customer_data.csv','a', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(Sample_Wait[:,1])
    writer.writerow(Error[:,1])
f.close()


'''
Plot Satistical Results against Analytical Expected Values
'''

'''
NPAnalytical_Wait_High = np.zeros(NUMLAM) # Expected wait time of Class 0
NPAnalytical_Wait_Low = np.zeros(NUMLAM) # Expected wait time of Class 1
for l in range(NUMLAM):
    NPAnalytical_Wait_High[l] = FM_IN # Mean wait time of class 0 customers is just the mean repair time
    print(K)
    p_0 = (MU_IN/(MU_IN+LAMBDA_IN))
    p_1 = 1- p_0
    b = LAM[l]/MU

    # Eq. (24) in https://pubsonline.informs.org/doi/10.1287/opre.11.3.303
    NPAnalytical_Wait_Low[l] = (b/p_0 + ( LAM[l]*(SM_IN/(FM_IN))*p_0*p_1 + (LAM[l]*b*SM)/(FM*p_0) )/( 2*(p_0-b)))*(1/LAM[l])

    # Debug code to double check the delay formula in our Dyspan '24 paper
    print('Average system time model 1: %.3f' %NPAnalytical_Wait_Low[l])
    MU_PRIME = MU/(1+LAMBDA_IN/MU_IN)
    RHO_PRIME = LAM[l]/MU_PRIME    
    bb  = 1/MU_PRIME + ((K_IN/MU_IN)*(1-MU_PRIME/MU) + LAM[l]*(K)*(1/MU_PRIME**2) )/( 2*(1-RHO_PRIME) )
    print('Average system time model 2: %.3f' %bb)

# Plot using matplotlib
plt.plot(LAM,NPAnalytical_Wait_Low, label='Commerical Users, Analytical') # Plot of Expected Wait Times, class 1
plt.plot(LAM,NPAnalytical_Wait_High, label='EESS Users, Analytical') # Plot of Expected Wait (Repair) Times, class 0
plt.errorbar(LAM, Sample_Wait[:,1], yerr=Error[:,1], fmt='x', label='Commerical Users, Simulated Arrivals') # Plot of Simulated Wait Times, class 1
plt.errorbar(LAM, Sample_Wait[:,0], yerr=Error[:,0], fmt='x', label='EESS Users, Trace Data') # Plot of Simulated Wait (Repair) Times, class 0
plt.xlabel('Lambda')
plt.ylabel('Mean System Delay (seconds)')
plt.legend()
plt.show()
'''



