"""
Simulation of an M|G|1 queue with three priority classes and preemtive resume behavior
Uses simpy to dynamically generate events 

The classes are:
Incumbent class - class 0, government users arriving at rate theta*lambda
Priority class - class 1, customers opting to pay fee to join higher class
Ordinary class - class 2, customers opting to remain in default lowest priority

Customers choose between class 1 and 2 at rate phi

Each round however, a certain percentage of customers will be given the option to deviate based on the 
results from the previous round; any deviations will result in a new base value of phi being chosen for the next round. 

The simulator uses the Gamma distribution for service times, with a hardcoded exception for
the Deterministic distribution for second moment 1/MU^2. This has advantage of seeing how
changing the service distribution changes the results. In addition, Gamma distribution with
SHAPE = 1 corresponds to the Exponential distribution

v0.1 - uses expected vs recorded wait times to determine updates (Strategic Learning)
"""

# import required packages - numpy, scipy, and simpy required to be installed if not present

import math
import numpy as np
import simpy
import os
import scipy as sp
import scipy.stats as stats
import csv


'''
Define simulation Global Parameters
'''

# customer statistics
LAMc = 0.1 # Arrival rate 
MUc = 1 # Service rate = 1/(first moment of service)
RHOc = LAMc/MUc # traffic load, used for validation
Kc = 3  # Service Distribution; defined such that second moment of service = K/MU^2

# incumbent statistics
LAMi = 0.5 # Arrival rate 
MUi = 10 # Service rate = 1/(first moment of service)
RHOi = LAMi/MUi # traffic load, used for validation
Ki = 2 # Service Distribution; defined such that second moment of service = K/MU^2

CAPACITY = 1 # server capacity
SIM_TIME = 5*(10**5)/LAMc # length of time to run simulation over; scales so that ~5,000,000 customers are generated in each round
C = 0.167527  # Cost to join Premium class
FRAC = 0.05 # fraction of time to wait for before collecting statistics
ALPHA = 0.10 # Best Response Update Fraction
ITERATIONS = 20 # number of rounds to run the game over
# define parameters of Gamma distribution; Numpy uses shape/scale definition
if Kc > 1:
	SHAPEc = 1/(Kc-1) # Shape of Gamma Distribution
	SCALEc = (Kc-1)/MUc # Scale of Gamma Distribution
if Ki > 1:
	SHAPEi = 1/(Ki-1) # Shape of Gamma Distribution
	SCALEi = (Ki-1)/MUi # Scale of Gamma Distribution

'''
Define output file to write progressive results to
'''
workingdir = os.getcwd() # absolute path to current directory
resultout = os.path.join(workingdir, 'results.csv') # create new csv file

'''
Create class with resources to manage the queue
'''
class PriorityQueue:
	def __init__(self,PHI):
		self.env = simpy.Environment() # establish SimPy enviornment
		self.server = simpy.PreemptiveResource(self.env,capacity=CAPACITY) # M|G|1 server with priorities, can simulate arbitrary M|G|n by updating capacity
		self.phi = PHI # starting beleif of the customers in the current round
		# Flag whether customers should favor prioirty class or general class if deviating
		self.w = np.zeros(3) # collect wait times for each class
		self.n = np.zeros(3) # collect number of users in each class
		self.generator = np.random.default_rng() # define Generator instance introduced in numpy updates
		self.t_start = FRAC*SIM_TIME # time to begin collecting statistics to allow system to reach steady state

	# establish simulation and run, return relevant statistics
	def launchSimulation(self):
		self.env.process(self.arrivals())
		#self.env.process(self.incumbents())
		self.env.run(until=SIM_TIME)
		return self.w, self.n

	# generate incumbents, process in queue
	def incumbents(self):
		# want to continue generating incumbents until SIM_TIME reached
		while True:
			# randomized interarrival rate
			yield self.env.timeout(self.generator.exponential(1/LAMi))
			# mark arrival time  
			arrival = self.env.now 
			priority = 0 # User is incumbant class
		
			'''
			serv_time - length of service. Use Gamma Distribution for service times; shape = 1 (K = 2) is special case of 
			Exponential distribution. SHAPE and SCALE are defined such that First moment of service is 1/MU, and second moment is K/MU^2.
			Gamma is not defined for shape, scale <= 0, so instead have hardcoded special case for deterministic 
			'''
			if Ki == 1: 
				serv_time = 1/MUi # Special case for Deterministic system
			else:
				serv_time = self.generator.gamma(SHAPEi,SCALEi)
			# Have server process customer arrival
			self.env.process(self.provider(arrival,priority,serv_time))

	
	# generate customers, process in queue
	def arrivals(self):
		# want to continue generating customers until SIM_TIME reached
		while True:
			# randomized interarrival rate
			yield self.env.timeout(self.generator.exponential(1/LAMc))
			# mark arrival time  
			arrival = self.env.now 
			'''
			priority - customer has option to purchase priority, we assume they do so with probability phi 
			Class 0 is highest prioirty here, to ensure proper sorting of users in SimPy.
			This is not necessarily typical priority convention.
			'''
			if np.random.rand() <= self.phi:
				priority = 1 # User is Priority class customer
			else:
				priority = 2 # User is General class customer

			'''
			serv_time - length of service for customers. Use Gamma Distribution for service times; shape = 1 (K = 2) is special case of 
			Exponential distribution. SHAPE and SCALE are defined such that First moment of service is 1/MU, and second moment is K/MU^2.
			Gamma is not defined for shape, scale <= 0, so instead have hardcoded special case for deterministic 
			'''
			if Kc == 1: 
				serv_time = 1/MUc # Special case for Deterministic system
			else:
				serv_time = self.generator.gamma(SHAPEc,SCALEc)
			# Have server process customer arrival
			self.env.process(self.provider(arrival,priority,serv_time))

	# serve arrivals
	def provider(self,arr,prio,serv):
		# continue looping until job complete 
		notDone = True
		service = serv # need original serv time in order to compute wait in queue
		while notDone:
			# yield until the server is available, request with specifed priority
			with self.server.request(priority=prio) as MyTurn:
				yield MyTurn
				# customer has aquired the server, run job for specified service time
				start = self.env.now
				try:
					yield self.env.timeout(service)
					notDone = False # job complete, reverse flag to exit loop 
				except simpy.Interrupt:
					# process preempted, adjust remaining service time by how much longer job has remaining
					service -= (self.env.now-start)
		# Record total time spent waiting in queue, if beyond the threshold (customers only)
		if (self.env.now > self.t_start):
			self.w[prio] += self.env.now-arr # want to measure just the wait time for our purposes, not the total flow time
			self.n[prio] += 1           


def main():
	PHI = 0.5 # Round 1, customers proceed with initial belief PHI without option to deviate
	# create and launch server
	'''
	Main Simulator Loop
	'''
	for i in range(ITERATIONS):
		print('Iteration # %d' %(i)) # print to screen for visual indicator that loop is working
		# create and launch server
		Q = PriorityQueue(PHI)
		w, n = Q.launchSimulation()
		# Record statistics, including mean wait time per class
		mean_wait_p = w[1]/n[1] # mean_wait of priority customers
		expected_p = (Kc*RHOc)/(2*MUc*(1-PHI*RHOc))+1/MUc
		mean_wait_g = w[2]/n[2] # mean_wait of general custoemrs
		expected_g = (Kc*RHOc)/(2*MUc*(1-PHI*RHOc)*(1-RHOc))+1/(MUc*(1-PHI*RHOc))
		# determine update for PHI
		PHI_last = PHI
		if expected_p + C < expected_g:
			PHI = min(PHI+ALPHA*(1-PHI),1) # premium users better off, so general users incentivised to switch
		elif expected_g < expected_p + C:
			PHI = max(PHI-ALPHA*PHI,0) # general users better off, so premium users incentivised to switch
		# write current PHI to file to record output for later
		with open(resultout,'a') as file:
			writer = csv.writer(file, lineterminator='\n')
			writer.writerow([PHI_last,expected_p+C,expected_g,mean_wait_g,expected_p,mean_wait_p])
			#writer.writerow([PHI_last,mean_wait_i,mean_wait_p,expected_p,mean_wait_g,expected_g])
		file.close()

		
	
if __name__ == "__main__":
	main()

