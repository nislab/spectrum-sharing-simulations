"""
Simulation of an M|G|1 queue modeling CBRS, with three priority classes 
and preemtive resume service.
Uses simpy to dynamically generate events 

The classes are:
Incumbent class - class 0, government users bypassing the commerical setup
Priority class - class 1, customers opting to pay fee to join higher class
General class - class 2, customers opting to remain in default lowest priority

Customers choose between class 1 and 2 at rate phi
It is assumed that PHI is a static equilibrium for validation purposes

The simulator uses the Gamma distribution for service times, with a hardcoded exception for
the Deterministic distribution for second moment 1/MU^2. This has advantage of seeing how
changing the service distribution changes the results. In addition, Gamma distribution with
SHAPE = 1 corresponds to the Exponential distribution

The simulator measures the wait times for each class as well as the number of preemptions.
"""

# import required packages - numpy, scipy, and simpy required to be installed if not present

import math
import numpy as np
import simpy
import os
import scipy as sp
import scipy.stats as stats
import sys
import csv


def Simulator(LAM, MU, PHI, K, LAMi, MUi, Ki, CAPACITY, incumbentfile, priorityfile, generalfile):
	"""
	Encapsulates the main simulator components, which are then callable by a wrapper to run
	a suite of simulations for varying scenarios.
	LAM - Average arrival rate of customers
	MU - Average service rate of customers
	PHI - Probability of choosing Priority over General
	K - Service distribution of customers (K = 1 corresponds to Deterministic, K = 2 corresponds to Exponential)
	LAMi - Average arrival rate of incumbents
	MUi - Average service rate of incumbents
	Ki - Service distribution of incumbents
	CAPACITY - capacity of the server
	incumbentfile - file to save off incumbent statistics
	priorityfile - file to save off priority class statistics
	generalfile - file to save off general class statistics
	"""


	"""
	Define Simulation Global Parameters
	"""
	SIM_TIME = 1000 #(10**6)/LAM # length of time to run simulation over; scales so that 1000000 users are generated
	FRAC = 0.05 # fraction of time to wait for before collecting statistics
	ITERATIONS = 30 # number of independent simulations
	ALPHA = 0.05 # confidence interval is 100*(1-alpha) percent
	# define parameters of Gamma distribution; Numpy uses shape/scale definition
	if K > 1:
		SHAPE = 1/(K-1) 
		SCALE = (K-1)/MU 
	if Ki > 1:
		SHAPEi = 1/(Ki-1)
		SCALEi = (Ki-1)/MUi

	'''
	Create class with resources to manage the queue
	'''
	class PriorityQueue:
		def __init__(self):
			self.env = simpy.Environment() # establish SimPy enviornment
			self.server = simpy.PreemptiveResource(self.env,capacity=CAPACITY) # M|G|1 server with priorities, can simulate arbitrary M|G|n by updating capacity
			self.w = np.zeros(3) # collect wait times for each class
			self.n = np.zeros(3) # collect number of users in each class
			self.p = np.zeros(3) # collect number of preemptions in each class
			self.t_start = FRAC*SIM_TIME # time to begin collecting statistics to allow system to reach steady state

		# establish simulation and run, return relevant statistics
		def launchSimulation(self):
			self.env.process(self.custarrivals())
			self.env.process(self.incarrivals())
			self.env.run(until=SIM_TIME)
			return self.w, self.n, self.p

	
		# generate customer arrivals, process in queue
		def custarrivals(self):
			# want to continue generating customers until SIM_TIME reached
			while True:
				# randomized interarrival rate
				yield self.env.timeout(np.random.exponential(1/LAM))
				# mark arrival time  
				arrival = self.env.now 
				'''
				Determine priority class; use random.rand to roll a random number between (0,1] 
				If result is less than or equal to PHI, join Priority class; otherwise, remain in General
				'''
				decision = 1 - np.random.rand()
				if decision <= PHI:
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

		# generate incumbents, process in queue
		def incarrivals(self):
			# want to continue generating customers until SIM_TIME reached
			while True:
				# randomized interarrival rate
				yield self.env.timeout(np.random.exponential(1/LAMi))
				# mark arrival time  
				arrival = self.env.now 
				'''
				serv_time - length of service for incumbents. Use Gamma Distribution for service times; shape = 1 (Ki = 2) is special case of 
				Exponential distribution. SHAPE and SCALE are defined such that First moment of service is 1/MUi, and second moment is Ki/MUi^2.
				Gamma is not defined for shape, scale <= 0, so instead have hardcoded special case for deterministic 
				'''
				if Ki == 1: 
					serv_time = 1/MUi # Special case for Deterministic system
				else:
					serv_time = np.random.gamma(SHAPEi,SCALEi)
				# Have server process customer arrival - priority is automatically 0
				self.env.process(self.provider(arrival,0,serv_time))

		# serve arrivals
		def provider(self,arr,prio,serv):
			# continue looping until job complete
			notDone = True
			preemptions = 0 #count number of preemptions in service
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
						preemptions += 1
						print(preemptions)

			# Record total time spent waiting in queue, if beyond the threshold
			if (self.env.now > self.t_start):
				self.w[prio] += self.env.now-arr # measuring wait time as total flow time
				self.n[prio] += 1
				self.p[prio] += preemptions


	'''
	Main Simulator Loop
	'''
	Waits = np.zeros((ITERATIONS,3)) # Per Class mean wait times
	Nums = np.zeros((ITERATIONS,3)) # Per Class number of users
	Preemptions = np.zeros((ITERATIONS,3)) # Per Class number of preemptions
		
	for k in range(ITERATIONS):
		# create and launch server
		Q = PriorityQueue()
		w, n, p = Q.launchSimulation()
		# Record statistics, including mean wait time per class
		Waits[k] = w/n # want the average flow times, not the totals
		Nums[k] = n
		Preemptions[k] = p/n # want the average preemption per user
	# compute statistics
	MeanWaits = np.mean(Waits,axis=0) # mean of (average) Wait/Flow times
	ErrorWaits = np.std(Waits,axis=0)*stats.norm.ppf(1-ALPHA/2)/(ITERATIONS**0.5) # CI of (average) Wait/Flow Times
	MeanNums = np.mean(Nums,axis=0) # mean number of users
	ErrorNums = np.std(Nums,axis=0)*stats.norm.ppf(1-ALPHA/2)/(ITERATIONS**0.5) # CI of number of users
	MeanPreemptions = np.mean(Preemptions,axis=0) # mean number of preemptions
	ErrorPreemptions = np.std(Preemptions,axis=0)*stats.norm.ppf(1-ALPHA/2)/(ITERATIONS**0.5) # CI of number of users
	# Save off values for later analysis
	Inc = [MeanWaits[0], ErrorWaits[0], MeanNums[0], ErrorNums[0], MeanPreemptions[0], ErrorPreemptions[0]]
	PU = [MeanWaits[1], ErrorWaits[1], MeanNums[1], ErrorNums[1], MeanPreemptions[1], ErrorPreemptions[1]]
	GU = [MeanWaits[2], ErrorWaits[2], MeanNums[2], ErrorNums[2], MeanPreemptions[2], ErrorPreemptions[2]]
	with open(incumbentfile, 'a') as incout:
		writer = csv.writer(incout, lineterminator='\n')
		writer.writerow(Inc)
	incout.close()
	with open(priorityfile, 'a') as puout:
		writer = csv.writer(puout, lineterminator='\n')
		writer.writerow(PU)
	puout.close()
	with open(generalfile, 'a') as guout:
		writer = csv.writer(guout, lineterminator='\n')
		writer.writerow(GU)
	guout.close()

