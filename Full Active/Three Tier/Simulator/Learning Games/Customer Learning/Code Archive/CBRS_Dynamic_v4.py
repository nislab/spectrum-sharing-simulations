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

v2: Emulate alteration of incumbent parameters; after a particular iteration, the incumbent statistics update
Some time later, the provider updates the value of C to compensate for the change.

v2.1: Updates use actual expected service time rather than collected estimates

v3: Simulate change in customer attributes

v4: Simulate change in incumbent attributes given nighttime traffic
"""

# import required packages - numpy, scipy, and simpy required to be installed if not present

import math
import numpy as np
import simpy
import os
import scipy as sp
import scipy.stats as stats
import csv
import heapq


'''
Define simulation Global Parameters
'''
ALPHA = 0.05 # Best Response Update Fraction
ITERATIONS = 50 # number of rounds to run the game over
# define parameters of Gamma distribution; Numpy uses shape/scale definition


'''
Define output file to write progressive results to
'''
workingdir = os.getcwd() # absolute path to current directory
resultout = os.path.join(workingdir, 'results.csv') # create new csv file

'''
Define Priority Queue class
Taken from SO article: https://stackoverflow.com/questions/19745116/python-implementing-a-priority-queue
'''
class PriorityQueue:
	def __init__(self):
		self.items = []
		
	# push new entries onto the heap, sorted by priority and entry time - also contains flag for Ghost customers as well as remaining time in service and initial length of service   
	def push(self, priority, arrival, serv_time):
		heapq.heappush(self.items, (priority, arrival, serv_time))
		
	# pop items from the queue, to get next item for processing
	def pop(self):
		customer = heapq.heappop(self.items)
		return customer
	
	# define empty check
	def empty(self):
		return not self.items



'''
	Define simulator enviornment class
	'''

class Channel:
	def __init__(self, env, phi,LAMc,MUc,Kc,SHAPEc,SCALEc,LAMi,MUi,Ki,SHAPEi,SCALEi,T_START):
		# establish enviornment, collection vectors
		self.env = env # SimPy Enviornment
		self.phi = phi # probability to pick higher priority
		# customer parameters for current simulation run
		self.lamc = LAMc
		self.muc = MUc
		self.kc = Kc
		self.shapec = SHAPEc
		self.scalec = SCALEc
		# incumbent parameters for current simulation run
		self.lami = LAMi
		self.mui = MUi
		self.ki = Ki
		self.shapei = SHAPEi
		self.scalei = SCALEi
		self.tstart = T_START # time at which to start collecting statistics
		self.generator = np.random.default_rng() # define Generator instance introduced in numpy updates
		self.w = np.zeros(3) # total wait time for incumbents, customers
		self.n = np.zeros(3) # total number of incumbents, customers
		# set up queue, launch processes
		self.idle = True # flag to trigger activation event
		self.q = PriorityQueue() # queues of pending customers, starts empty
		self.customer_proc = self.env.process(self.customers(env))
		self.incumbent_proc = self.env.process(self.incumbents(env))
		self.server_proc = self.env.process(self.server(env))
		# define trigger to wake up idle server
		self.server_wakeup = env.event() # event trigger to wake up idle server

	def customers(self, env):
		'''
		Process for customer job arrivals to queue. Customers choose between priority and general access with probability PHI
		'''
		while True:
			# randomized, Poission interarrival rate
			yield env.timeout(self.generator.exponential(1/self.lamc))
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
			if self.kc == 1: 
				serv_time = 1/self.muc # Special case for Deterministic system
			else:
				serv_time = self.generator.gamma(self.shapec,self.scalec)
			# push onto the queue
			self.q.push(priority, env.now, serv_time) 
			# if server idle, wake it up
			if self.idle:
				self.server_wakeup.succeed() # reactivate server
				self.server_wakeup = env.event() # reset server wakeup trigger
			# otherwise, if new arrival has prioirty over customer currently in service, trigger preemption
			elif priority < self.next[0]:
				self.server_proc.interrupt()

	def incumbents(self, env):
		'''
		Incumbents are non-customers with reserved priority usage over the channel
		'''
		while True:
			# randomized Poission interarrival rate
			yield env.timeout(self.generator.exponential(1/self.lami))
			priority = 0 # User is incumbant class
			'''
			serv_time - length of service. Use Gamma Distribution for service times; shape = 1 (K = 2) is special case of 
			Exponential distribution. SHAPE and SCALE are defined such that First moment of service is 1/MU, and second moment is K/MU^2.
			Gamma is not defined for shape, scale <= 0, so instead have hardcoded special case for deterministic 
			'''
			if self.ki == 1: 
				serv_time = 1/self.mui # Special case for Deterministic system
			else:
				serv_time = self.generator.gamma(self.shapei,self.scalei)
			# push onto the queue
			self.q.push(priority, env.now, serv_time) 
			# if server idle, wake it up
			if self.idle:
				self.server_wakeup.succeed() # reactivate server
				self.server_wakeup = env.event() # reset server wakeup trigger
			# otherwise, if new arrival has prioirty over customer currently in service, trigger preemption
			elif priority < self.next[0]:
				self.server_proc.interrupt()

		
	def server(self, env):
		'''
		Serve the packets being held in the queue
		Queue is implemented as a heap, with elements as tuples utilizing standard Python tuple sort
		tuple[0] - Priority: integer between 0-2 for incumbent, priority customer, general customer
		tuple[1] - Arrival Time: non negative float, representing initial arrival time to the queue
		tuple[2] - service: remaining service time
		'''
		self.idle = True
		while True:
			# if nothing in queue, put server to sleep - else next part breaks
			if self.q.empty():
				self.idle = True 
				yield self.server_wakeup # yield until reactivation event succeeds
			# serve job at head of queue - Priority queue automatically sorts by priority, then entry into system
			self.next = self.q.pop() 
			#print("priority: " + str(self.next[0]))
			#print("service remaining: " + str(self.next[2]))
			self.idle = False
			start = env.now
			try:
				yield env.timeout(self.next[2]) # run for remaining service
				if (env.now > self.tstart):
					# beyond threshold to record statistics
					self.w[self.next[0]] += env.now - self.next[1] # total wait time is exit time - initial queue entry - service time
					self.n[self.next[0]] += 1
			except simpy.Interrupt:
				# current job interrupted by higher priority arrival, reinsert into queue with time remaining updated
				self.q.push(self.next[0],self.next[1],self.next[2]-(env.now-start)) # decrement time remaining by amount of time passed
				#print("service elapsed: " + str(env.now-start))
				#print("service remaining: " + str(self.next[2]-(env.now-start)))


def main():
	# create and launch server
	PHI = 0.99 # Initial Belief, is updated via loop
	'''
	Main Simulator Loop
	'''
	for i in range(ITERATIONS):
		# Set Incumbent parameters based on ITERATIONS rather than have them as static values
		if i < 2*ITERATIONS/5:
			# customer statistics
			LAMc = 0.2 # Arrival rate 
			MUc = 1 # Service rate = 1/(first moment of service)
			RHOc = LAMc/MUc # traffic load, used for validation
			Kc = 3  # Service Distribution; defined such that second moment of service = K/MU^2
			# incumbent statistics
			LAMi = 2 # Arrival rate 
			MUi = 10 # Service rate = 1/(first moment of service)
			RHOi = LAMi/MUi # traffic load, used for validation
			Ki = 10 # Service Distribution; defined such that second moment of service = K/MU^2
		else:
			# customer statistics
			LAMc = 0.2 # Arrival rate 
			MUc = 1 # Service rate = 1/(first moment of service)
			RHOc = LAMc/MUc # traffic load, used for validation
			Kc = 3 # Service Distribution; defined such that second moment of service = K/MU^2
			# incumbent statistics
			LAMi = 0.5 # Arrival rate 
			MUi = 10 # Service rate = 1/(first moment of service)
			RHOi = LAMi/MUi # traffic load, used for validation
			Ki = 2 # Service Distribution; defined such that second moment of service = K/MU^2
		SIM_TIME = 5*(10**6)/LAMc # length of time to run simulation over; scales so that ~5,000,000 customers are generated in each round
		T_START = 0.05*SIM_TIME # time to begin collecting statistics to allow system to reach steady state
		# define respective Gamma Distributions using Shape, Scale 
		if Kc > 1:
			SHAPEc = 1/(Kc-1) # Shape of Gamma Distribution
			SCALEc = (Kc-1)/MUc # Scale of Gamma Distribution
		else:
			SHAPEc = 0 # Placeholder to prevent error
			SCALEc = 0 # Placeholder to prevent error
		if Ki > 1:
			SHAPEi = 1/(Ki-1) # Shape of Gamma Distribution
			SCALEi = (Ki-1)/MUi # Scale of Gamma Distribution
		else:
			SHAPEi = 0 # Placeholder to prevent error
			SCALEi = 0 # Placeholder to prevent error
		# Cost to join Premium class based on iteration; initially set based on origional parameters, updated sometime after incumbent statistics do
		if i < 4*ITERATIONS/5:
			C = 0.65 # actual value 0.694444 
		else:
			C = 0.40 # actual value 0.394854
		print('Iteration # %d' %(i)) # print to screen for visual indicator that loop is working
		#Establish Simply Enviornment and launch simulation
		env = simpy.Environment() # establish SimPy enviornment
		CBRS = Channel(env,PHI,LAMc,MUc,Kc,SHAPEc,SCALEc,LAMi,MUi,Ki,SHAPEi,SCALEi,T_START)
		env.run(until=SIM_TIME)
		# Record statistics, including mean wait time per class
		mean_wait_i = CBRS.w[0]/CBRS.n[0] # mean_wait of incumbents
		expected_i = 1/MUi+(Ki*RHOi)/(2*MUi*(1-RHOi))
		mean_wait_p = CBRS.w[1]/CBRS.n[1] # mean_wait of priority customers
		expected_p = 1/(MUc*(1-RHOi)) + (Ki*RHOi/MUi+PHI*Kc*RHOc/MUc)/(2*(1-RHOi)*(1-(RHOi+PHI*RHOc)))
		mean_wait_g = CBRS.w[2]/CBRS.n[2] # mean_wait of general custoemrs
		expected_g = 1/(MUc*(1-(RHOi+PHI*RHOc))) + (Ki*RHOi/MUi+Kc*RHOc/MUc)/(2*(1-(RHOi+PHI*RHOc))*(1-(RHOi+RHOc)))
		# determine update for PHI
		PHI_last = PHI
		if expected_p + C < expected_g:
			PHI = min(PHI+ALPHA*(1-PHI),1) # premium users better off, so general users incentivised to switch
		elif expected_g < expected_p + C:
			PHI = max(PHI-ALPHA*PHI,0) # general users better off, so premium users incentivised to switch
		# write current PHI to file to record output for later
		with open(resultout,'a') as file:
			writer = csv.writer(file, lineterminator='\n')
			writer.writerow([PHI_last,mean_wait_i,mean_wait_p,expected_p,mean_wait_g,expected_g])
		file.close()

		
	
if __name__ == "__main__":
	main()

