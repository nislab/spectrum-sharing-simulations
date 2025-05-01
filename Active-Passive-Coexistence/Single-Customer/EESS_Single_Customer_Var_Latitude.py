"""
Simulation of an M|G|1 queue with server breakdowns
Classes are denoted as class 0, and class 1. Class 0 arrivals belong to the higher priority class and
represent server breakdowns.
This nomenclature is used to ensure proper sort, as SimPy prioirty resource sorts on priority
in ascending order. This also makes storing system flow time information intuitive, as Python is 
zero indexed.

The simulator uses a latitude in decimal format to extrapolate a first and second moment of interarrival times
to define a distribution. For testing purposes we utilize exponential, gamma, and log-normal distributions for comparison

Service times use logistic distributions in all cases
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
LAM = [0.13035,0.13342,0.13649,0.13955,0.14262,0.14569] # Arrival rates of customers
NUMLAM = len(LAM)
MU = 0.1546 # Service rate of customers; defined as 1 over first moment of service
K = 1.4897 # Service Distribution; defined such that second moment of service is K over MU^2

if K < 1:
    print('K must be at least 1')
    exit()
# define parameters of Gamma distribution for customers; Numpy uses shape/scale definition
if K > 1:
    SHAPE = 1/(K-1) # Shape of Gamma Distribution
    SCALE = (K-1)/MU # Scale of Gamma Distribution


# Define parameters of server breakdowns
LAT = 42.36 # latitude of center of area to consider (BOS)
#LAT = 19.42 # latitude of center of area to consider (CDX)
#LAT = 64.83 # latitude of center of area to consider (FAK)

DIST = 0 # distribution in use, 0 for exp, 1 for Gamma, 2 for log-log
M1 = 3600*(1.56 - 0.00266*abs(LAT) - (1.73*10**(-4))*LAT**2) # estimated interarrival mean from latitude, in seconds
M2 = 3600*(1.80 + 0.00338*abs(LAT) - (2.86*10**(-4))*LAT**2) # estimated interarrival std deviation from latitude, in seconds
if DIST == 1:
    # Gamma Parameters
    SHAPE_ARRIN = (M1/M2)**2
    SCALE_ARRIN = (M2**2)/M1
elif DIST == 2:
    # Log-normal parameters
    LN_MEAN = math.log(M1**2/math.sqrt(M1**2+M2**2))
    LN_STD = math.log(1+M2**2/M1**2)


LAMBDA_IN = 1/M1 # interarrival rate, equal to 1/mean
MU_IN = 0.036 # service rate, latitude indipendent, equal to 1/mean service time (based on MST of 27.8026)
K_IN = 1.4464 # Service Repair Distribution; defined such that second moment of service is K_IN over MU_IN^2; based on std dev of 18.5769

# define shape and scale parameters as appropriate for arrivals



if K_IN < 1:
    print('K_IN must be at least 1')
    exit()
else:
    # define parameters of Logistic distribution for server repair; Numpy uses shape/scale definition
    SHAPE_SERVIN = 1/MU_IN # Shape of Logistic Distribution; corresponds to location/mean
    SCALE_SERVIN = math.sqrt((3*(K_IN-1))/((np.pi*MU_IN)**2)) # Scale of Logistic Distribution; defined directly in terms of Variance

# define parameters for service distribution times

FM_EFF = (1/MU)*(1+LAMBDA_IN/MU_IN) #Effective First Moment of Service Time (cf Eq. 9 in https://ieeexplore.ieee.org/abstract/document/6776591)
MU_EFF = 1/FM_EFF #Effective mean service rate of customers


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
    preemptions = 0
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
                preemptions += 1 


    # Record total system time, if beyond the threshold
    if (env.now > t_start):
        tmp = np.int_([1])
        if prio==0:
            tmp[0]=0
        server.wait[tmp[0]] += env.now-arrival
        server.n[tmp[0]] += 1
        server.preempt[tmp[0]] += preemptions
        
        


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
    off_time =0
    while True:
        match DIST:
            case 1:
                # Gamma
                on_time = np.random.gamma(SHAPE_ARRIN,SCALE_ARRIN)
            case 2:
                # Log-Normal
                on_time = np.random.lognormal(LN_MEAN,LN_STD)
            case _:
                # Default 0, Exponential
                on_time = np.random.exponential(M1)
        yield env.timeout(off_time+on_time) # general off time + exponential on time 
        arrival = env.now # mark arrival time
        priority = 0 # PU arrival
        serv_time = abs(np.random.logistic(SHAPE_SERVIN,SCALE_SERVIN)) # logistic distribution includes negative support; handle this by accepting absolute value of drawn value
        off_time = serv_time
        env.process(provider(env,arrival,priority,serv_time,t_start,server))   



'''
Define supporting structures
'''
Server = collections.namedtuple('Server','processor,wait,n,preempt') # define server tuple to pass into arrivals, provider methods
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
        preemptions = np.zeros(2)
        rate_PU = LAMBDA_IN
        rate_SU = LAM[l] # total arrival rate of events (customers or server breakdowns)
        sim_time = 5266711 # sim over ~2 months worth of arrivals (BOS)
        # sim_time = 5251917 # sim over ~2 months worth of arrivals (CMX)
        # sim_time = 5270046 # sim over ~2 months worth of arrivals (FAK)
        t_start = FRAC*sim_time # time to start collecting statistics at
        server = Server(processor,wait,n,preemptions)
        #start simulation
        env.process(arrivals_PU(env,server,rate_PU,t_start))
        env.process(arrivals_SU(env,server,rate_SU,t_start))
        env.run(until=sim_time)
        # Record average wait in each class
        Mean_Wait[k,l,0] = wait[0]/n[0]
        Mean_Preempt[k,l,0] = preemptions[0]/n[0]
        Mean_Wait[k,l,1] = wait[1]/n[1]
        Mean_Preempt[k,l,1] = preemptions[1]/n[1]

      

'''
Compute Statistics     
'''
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


