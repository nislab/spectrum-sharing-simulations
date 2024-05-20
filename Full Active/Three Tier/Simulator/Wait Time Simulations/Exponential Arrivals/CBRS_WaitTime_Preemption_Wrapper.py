"""
Wrapper to define values for CBRS_WaitTime_Preemption_Sim Simulator, define save files for statistics
Author: Jonathan Chamberlain, 2021 jdchambo@bu.edu
"""

from CBRS_WaitTime_Preemption_Sim import Simulator
import os

'''
Define loop for simulators
Loop over values of lam and phi for customer arrivals, PU fraction, respectively
Define quantities for both customer and incumbent statistics plus server configuation
'''

#lam = [0.1,0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9] # customer arrival rates
lam = [0.1, 0.4, 0.8]
mu = 1 # customer service rate
phi = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9] # fraction of PU customers
k = 2 # service distribution
lami = 0.5 # incument arrival rate
mui = 10 # incumbent service rate
ki = 2 # incumbent service distribution
c = 1 # capacity of the server


for i in range(len(lam)):
	l = lam[i]
	for j in range(len(phi)):
		p = phi[j]
		# define files and directories to save files
		workingdir = os.path.dirname(__file__) # absolute path to current directory
		incfile = os.path.join(workingdir, 'statfilefiles/inc_stats_lambda_{0}.csv'.format(l))
		os.makedirs(os.path.dirname(incfile), exist_ok = True)
		pufile = os.path.join(workingdir, 'statfilefiles/pu_stats_lambda_{0}.csv'.format(l))
		os.makedirs(os.path.dirname(pufile), exist_ok = True)
		gufile = os.path.join(workingdir, 'statfilefiles/gu_stats_lambda_{0}.csv'.format(l))
		os.makedirs(os.path.dirname(gufile), exist_ok = True)
		print('Starting lambda = {0}, phi = {1}'.format(l,p))
		Simulator(l, mu, p, k, lami, mui, ki, c, incfile, pufile, gufile)
print('Simulations Complete')