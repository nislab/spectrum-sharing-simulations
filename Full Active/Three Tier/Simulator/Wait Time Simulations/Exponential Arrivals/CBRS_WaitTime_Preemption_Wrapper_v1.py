"""
Wrapper to define values for CBRS_WaitTime_Preemption_Sim Simulator, define save files for statistics
Author: Jonathan Chamberlain, 2021 jdchambo@bu.edu
"""

from CBRS_WaitTime_Preemption_Sim_v1 import Simulator
import os

'''
Define loop for simulators
Loop over values of lam and phi for customer arrivals, PU fraction, respectively
Define quantities for both customer and incumbent statistics plus server configuation
'''

lam = [0.0627845] # customer arrival rate
mu = 0.627845 # customer service rate
#k = 1.30018 # customer service distribution
k = 3.90054 # customer service distribution

lami = 0.00163492 # incument arrival rate
mui = 0.0326984 # incumbent service rate
ki = 1.85499 # incumbent service distribution

#vp_under = 1.07752, vp* = 1.20429, vp_over = 1.34
vp = 1.5 # cost of preemption
phi = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9] # fraction of PU customers


for i in range(len(lam)):
	l = lam[i]
	for j in range(len(phi)):
		p = phi[j]
		# define files and directories to save files
		workingdir = os.path.dirname(__file__) # absolute path to current directory
		costfile = os.path.join(workingdir, 'costfiles/results_k_{0}_vp_{1}.csv'.format(k, vp))
		os.makedirs(os.path.dirname(costfile), exist_ok = True)
		print('Starting phi = {0}'.format(p))
		Simulator(l, mu, p, k, lami, mui, ki, vp, costfile)
print('Simulations Complete')