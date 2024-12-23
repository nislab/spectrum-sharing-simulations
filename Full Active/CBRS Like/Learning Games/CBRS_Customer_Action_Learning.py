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

The simulator measures the expected costs of service
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
import heapq

'''
Customer Parameters for Gamma Distribution
'''
LAM = 0.0627845
MU = 0.627845 
RHO = LAM/MU 
K = 3.90054
'''
Incumbent Parameters for Gamma Distribution
'''
LAMi = 0.00163492
MUi = 0.0326984
RHOi = LAMi/MUi
Ki = 1.85499

PHI = 0.9 # Initial value of PHI
Vp = 1.4 # Value of preemption
C = 0.582691 # Cost to join premium queue
ROUNDS = 50 # number of rounds to play the game over
ITERATIONS = 30 # number of independent simulations
ALPHA = 0.05 # Fraction of customers eligible for update


def Simulator(lam, mu, k, phi, lami, mui, ki):
	"""
	Encapsulates the main simulator components, which are then callable by a wrapper to run
	a suite of simulations for varying scenarios.
	lam - Average arrival rate of customers
	mu - Average service rate of cusotmers
	k - Service distribution of customers
	phi - Probability of choosing Priority over General
	lami - Average arrival rate of incumbents
	mui - Average service rate of incumbents
	ki - Service distribution of incumbents
	"""

	"""
	Define Simulation Global Parameters
	"""
	SIM_TIME = (5*10**5)/LAM # length of time to run simulation over; scales so that 1,000,000 users are generated
	FRAC = 0.05 # fraction of time to wait for before collecting statistics
	T_START = FRAC*SIM_TIME # time to start collecting statistics at
	if k > 1:
		shape = 1/(k-1)
		scale = (k-1)/mu
	if ki > 1:
		shapei = 1/(ki-1)
		scalei = (ki-1)/mui

	'''
	Define Priority Queue class
	Taken from SO article: https://stackoverflow.com/questions/19745116/python-implementing-a-priority-queue
	'''
	class PriorityQueue:
		def __init__(self):
			self.items = []
		
		'''    
		push new entries onto the heap
		Users are defined so that queue sorts first by priroity, then by entry time:
		priroity = assigned priority (0 for incumbents, 1 for Priority Customers, 2 for General Customers)
		entry = initial arrival time in system
		service = remaining service length
		'''
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
	Create class with resources to manage the queue
	'''
	class SimEnv:
		def __init__(self,env):
			self.env = env
			self.w = np.zeros(3) # collect wait times for each class
			self.n = np.zeros(3) # collect number of users in each class
			self.q = PriorityQueue() # priority heap queue
			self.idle = True # flag to trigger server activation
			self.server_wakeup = env.event() # event trigger to wake up idle server
			# launch processes
			self.cust_proc = env.process(self.custarrivals(env))
			self.inc_proc = env.process(self.incarrivals(env))
			self.prov_proc = env.process(self.provider(env))
	
		# generate customer arrivals, process in queue
		def custarrivals(self, env):
			# want to continue generating customers until SIM_TIME reached
			while True:
				# randomized interarrival rate
				yield env.timeout(np.random.exponential(1/lam))
				# mark arrival time  
				arrival = env.now 
				'''
				Determine priority class; use random.rand to roll a random number between (0,1] 
				If result is less than or equal to PHI, join Priority class; otherwise, remain in General
				'''
				decision = 1 - np.random.rand()
				if decision <= phi:
					priority = 1 # User is Priority class customer
				else:
					priority = 2 # User is Ordinary class customer
				'''
				serv_time - length of service for customers. Use Gamma Distribution for service times; shape = 1 (Ki = 2) is special case of 
				Exponential distribution. SHAPE and SCALE are defined such that First moment of service is 1/MUi, and second moment is Ki/MUi^2.
				Gamma is not defined for shape, scale <= 0, so instead have hardcoded special case for deterministic 
				'''
				if k == 1: 
					serv_time = 1/mu # Special case for Deterministic system
				else:
					serv_time = np.random.gamma(shape,scale)
				# Have server process customer arrival
				self.q.push(priority, arrival, serv_time)
				# if server idle, wake it up
				if self.idle:
					self.server_wakeup.succeed() # reactivate server
					self.server_wakeup = env.event() # reset server wakeup trigger
				# otherwise, if new arrival has prioirty over customer currently in service, trigger preemption
				elif priority < self.next[0]:
					self.prov_proc.interrupt()

		# generate incumbents, process in queue
		def incarrivals(self,env):
			# want to continue generating customers until SIM_TIME reached
			while True:
				# randomized interarrival rate
				yield env.timeout(np.random.exponential(1/lami))
				# mark arrival time  
				arrival = env.now 
				'''
				serv_time - length of service for incumbents. Use Gamma Distribution for service times; shape = 1 (Ki = 2) is special case of 
				Exponential distribution. SHAPE and SCALE are defined such that First moment of service is 1/MUi, and second moment is Ki/MUi^2.
				Gamma is not defined for shape, scale <= 0, so instead have hardcoded special case for deterministic 
				'''
				if ki == 1: 
					serv_time = 1/mui # Special case for Deterministic system
				else:
					serv_time = np.random.gamma(shapei,scalei)
				# Have server process incumbent arrival - priority is automatically 0
				self.q.push(0, arrival, serv_time)
				# if server idle, wake it up
				if self.idle:
					self.server_wakeup.succeed() # reactivate server
					self.server_wakeup = self.env.event() # reset server wakeup trigger
				# otherwise, if new arrival has prioirty over customer currently in service, trigger preemption
				elif self.next[0] > 0:
					self.prov_proc.interrupt()

		# serve arrivals
		def provider(self,env):
			while True:
				self.idle = True
				# if nothing in queue, sleep until next arrival
				if self.q.empty():
					yield self.server_wakeup # yield until reactivation event succeeds
				self.next = self.q.pop() # get next user
				self.idle = False
				# from now, try serving customer for remaining service time (next[2])
				serv_start = env.now
				try:
					yield env.timeout(self.next[2])
					# Record total time spent waiting in queue, if beyond the threshold
					if (env.now > T_START):
						self.w[self.next[0]] += env.now-self.next[1] # measuring wait time as total flow time
						self.n[self.next[0]] += 1		
				except simpy.Interrupt:
					# process preempted, adjust remaining service time by how much longer job has remaining
					self.q.push(self.next[0], self.next[1], self.next[2]-(env.now-serv_start))
				
	'''
	Main Simulator Routine
	'''
	# create and launch server
	env = simpy.Environment()
	sim = SimEnv(env)
	env.run(until=SIM_TIME)
	# Return per class system delay for Priority (1) and General (2) classes
	# Use placeholder values of phi = 0, 1 since otherwise sim.n[i] = 0 for the other class
	if phi == 0:
		DelayP = 0
	else:
		DelayP = (sim.w[1]/sim.n[1])
	if phi == 1:
		DelayG = 0
	else:
		DelayG = (sim.w[2]/sim.n[2])
	return DelayP, DelayG

'''
Define output file to write progressive results to
'''
workingdir = os.getcwd() # absolute path to current directory
resultout = os.path.join(workingdir, 'results.csv') # create new csv file

# write to file
with open(resultout,'a') as file:
	writer = csv.writer(file, lineterminator='\n')
	writer.writerow([PHI,0])
file.close()
# Run Action Learning Game
for i in range(ROUNDS):
	print('Round # %d' %(i))
	PHIsim = np.zeros((ITERATIONS))
	for k in range(ITERATIONS):
		DP, DG = Simulator(LAM, MU, K, PHI, LAMi, MUi, Ki)
		PP = Vp*RHOi
		PG = Vp*(RHOi+PHI*RHO)
		# use placeholder values if phi = 0 or 1, as otherwise there are 0 customers in other class
		if PHI == 0:
			DP = 1/(MU*(1-RHOi)) + (Ki*RHOi/MUi+0.001*K*RHO/MU)/(2*(1-RHOi)*(1-(RHOi+0.001*RHO)))
		if PHI == 1:
			DG = 1/(MU*(1-(RHOi+0.999*RHO))) + (Ki*RHOi/MUi+K*RHO/MU)/(2*(1-(RHOi+0.999*RHO))*(1-(RHOi+RHO)))
		# Update PHI
		if DP + PP + C < DG + PG:
			# priority better off, increase PHI
			PHIsim[k] = min(PHI+ALPHA*(1-PHI),1)
		elif DG + PG < DP + PP + C :
			# general better off, decrease PHI
			PHIsim[k] = max(PHI-ALPHA*PHI,0)
	PHI = np.mean(PHIsim,axis=0)
	PHIerr = np.std(PHIsim,axis=0)*stats.norm.ppf(1-ALPHA/2)/(ITERATIONS**0.5)
	# write to file
	with open(resultout,'a') as file:
		writer = csv.writer(file, lineterminator='\n')
		writer.writerow([PHI,PHIerr])
	file.close() 