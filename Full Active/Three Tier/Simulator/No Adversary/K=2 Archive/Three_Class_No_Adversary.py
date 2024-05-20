"""
Simulation of an M|G|1 queue with three priority classes and preemtive resume behavior
Uses simpy to dynamically generate events 

The classes are:
Incumbent class - class 0, government users arriving at rate theta*lambda
Priority class - class 1, customers opting to pay fee to join higher class
Ordinary class - class 2, customers opting to remain in default lowest priority

Customers choose between class 1 and 2 at rate phi

The simulator uses the Gamma distribution for service times, with a hardcoded exception for
the Deterministic distribution for second moment 1/MU^2. This has advantage of seeing how
changing the service distribution changes the results. In addition, Gamma distribution with
SHAPE = 1 corresponds to the Exponential distribution
"""

# import required packages - numpy, scipy, and simpy required to be installed if not present

import math
import numpy as np
import simpy
import os
import csv


'''
Get input from user for system rate, service rate, fraction of customers in higher class,
and second moment of service. Script expects the input in that order
'''

'''
Define simulation Global Parameters
'''

LAM = 0.9 # Arrival rate of customers
MU = 1 # Service rate of customers; defined as 1 over first moment of service
THETA = 0.2 # Fraction of arrivals who are in the incumbent class
PHI = 0.9 # Fraction of customers in higher class
K = 2 # Service Distribution; defined such that second moment of service is K over MU^2
RHO = LAM/MU # traffic load 
CAPACITY = 1 # server capacity
SIM_TIME = (10**6)/LAM # length of time to run simulation over; scales so that 1000000 users are generated
FRAC = 0.05 # fraction of time to wait for before collecting statistics
ITERATIONS = 30 # number of independent simulations
ALPHA = 0.05 # confidence interval is 100*(1-alpha) percent
# define parameters of Gamma distribution; Numpy uses shape/scale definition
if K > 1:
	SHAPE = 1/(K-1) # Shape of Gamma Distribution
	SCALE = (K-1)/MU # Scale of Gamma Distribution

'''
Create class with resources to manage the queue
'''
class PriorityQueue:
	def __init__(self):
		self.env = simpy.Environment() # establish SimPy enviornment
		self.server = simpy.PreemptiveResource(self.env,capacity=CAPACITY) # M|G|1 server with priorities, can simulate arbitrary M|G|n by updating capacity
		self.w = np.zeros(3) # collect wait times for each class
		self.n = np.zeros(3) # collect number of users in each class
		self.t_start = FRAC*SIM_TIME # time to begin collecting statistics to allow system to reach steady state

	# establish simulation and run, return relevant statistics
	def launchSimulation(self):
		self.env.process(self.arrivals())
		self.env.run(until=SIM_TIME)
		return self.w, self.n

	
	# generate arrivals, process in queue
	def arrivals(self):
		# want to continue generating customers until SIM_TIME reached
		while True:
			# randomized interarrival rate
			yield self.env.timeout(np.random.exponential(1/LAM))
			# mark arrival time  
			arrival = self.env.now 
			'''
			Determine priority class
			First, determine whether customer is incumbent or not; incumbents arrive at fraction theta
			Second, if not incumbent, determine if customer purchased priroity; does so at fraction phi
			Use random.rand to roll a random number between [0,1) in both cases
			'''

			decision = np.random.rand() # roll random number between [0,1), determine  whether to purchase premium access
			'''
			priority - customer has option to purchase priority, we assume they do so with probability phi, with the cost to do so
			set at the level that leads to the equilibrium state phi. Class 0 is highest prioirty here, to ensure proper sorting of customers.
			This is not necessarily typical priority convention.
			'''
			if np.random.rand() <= THETA:
				priority = 0 # User is incumbant class
			elif np.random.rand() <= PHI:
				priority = 1 # User is Priority class customer
			else:
				priority = 2 # User is Ordinary class customer
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
			self.env.process(self.provider(arrival,priority,serv_time))

	# serve arrivals
	def provider(self,arr,prio,serv):
		# continue looping until job complete
		notDone = True
		while notDone:
			# yield until the server is available, request with specifed priority
			with self.server.request(priority=prio) as MyTurn:
				yield MyTurn
				# customer has aquired the server, run job for specified service time
				start = self.env.now
				try:
					yield self.env.timeout(serv)
					notDone = False # job complete, reverse flag to exit loop
				except simpy.Interrupt:
					# process preempted, adjust remaining service time by how much longer job has remaining
					serv -= (self.env.now-start)

		# Record total system time, if beyond the threshold
		if (self.env.now > self.t_start):
			self.w[prio] += self.env.now-arr
			self.n[prio] += 1             


def main():
	Wait = np.zeros((ITERATIONS,3))
	Num = np.zeros((ITERATIONS,3))
	Mean_Wait = np.zeros((ITERATIONS,3))
	'''
	Main Simulator Loop
	'''
	for k in range(ITERATIONS):
		print('Iteration # %d' %(k))
		# create and launch server
		Q = PriorityQueue()
		w, n = Q.launchSimulation()
		# Record statistics, including mean wait time per class
		for i in range(3):
			Wait[k,i] = w[i]
			Num[k,i] = n[i]
			Mean_Wait[k,i] = w[i]/n[i]
	# Save off files for later analysis
	workingdir = os.getcwd() # absolute path to current directory
	waitfile = os.path.join(workingdir, 'wait.csv')
	os.makedirs(os.path.dirname(waitfile), exist_ok = True)
	with open(waitfile, 'a') as waitout:
		writer = csv.writer(waitout, lineterminator='\n')
		writer.writerow(Wait)
	numfile = os.path.join(workingdir, 'num.csv')
	os.makedirs(os.path.dirname(numfile), exist_ok = True)
	with open(numfile, 'a') as numout:
		writer = csv.writer(numout, lineterminator='\n')
		writer.writerow(Num)
	meanfile = os.path.join(workingdir, 'mean.csv')
	os.makedirs(os.path.dirname(meanfile), exist_ok = True)
	with open(meanfile, 'a') as meanout:
		writer = csv.writer(meanout, lineterminator='\n')
		writer.writerow(Mean_Wait)
	
if __name__ == "__main__":
	main()

