"""
Wrapper to define values for CBRS_WaitTime_Preemption_Sim Simulator, define save files for statistics
Author: Jonathan Chamberlain, 2021 jdchambo@bu.edu
"""

from CBRS_WaitTime_Sim import Simulator
import os

'''
Define loop for simulators
Loop over values of lam and phi for customer arrivals, PU fraction, respectively
Define quantities for both customer and incumbent statistics plus server configuation
'''

phi = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9] # fraction of PU customers

lam = [0.0627845,0.251138,0.502276] # customer arrival rates
mu = 0.627845 # customer service rate
k = 3.90054 # customer service distribution

lami = 0.00163492 # incument arrival rate
mui = 0.0326984 # incumbent service rate
ki = 1.85499 # incumbent service distribution


for i in range(len(lam)):
	l = lam[i]
	for j in range(len(phi)):
		p = phi[j]
		# define files and directories to save files
		workingdir = os.path.dirname(__file__) # absolute path to current directory
		costfile = os.path.join(workingdir, 'costfiles/cost_stats_lambda_{0}.csv'.format(l))
		os.makedirs(os.path.dirname(costfile), exist_ok = True)
		print('Starting lambda = {0}, phi = {1}'.format(l,p))
		Simulator(l, mu, p, k, lami, mui, ki, costfile)
print('Simulations Complete')