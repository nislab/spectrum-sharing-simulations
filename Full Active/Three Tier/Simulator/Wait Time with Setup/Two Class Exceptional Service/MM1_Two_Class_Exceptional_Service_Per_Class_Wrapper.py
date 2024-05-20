"""
Wrapper to define values for MM1_Two_Class_Exceptional_Service_Sim Simulator, define save files for statistics
Author: Jonathan Chamberlain, 2021 jdchambo@bu.edu
"""

from MM1_Two_Class_Exceptional_Service_Per_Class_Sim import Simulator
import os

'''
Define loop for simulators
Loop over values of lambda, phi
Save Mean wait times
Save figures for each run
'''

lam = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]
mu = 1
phi = [0.05, 0.1, 0.15, 0.2, 0.25, 0.3, 0.35, 0.4, 0.45, 0.5, 0.55, 0.6, 0.65, 0.7, 0.75, 0.8, 0.85, 0.9, 0.95]
sigma = 1


for i in range(len(lam)):
	l = lam[i]
	for j in range(len(phi)):
		p = phi[j]
		# define files and directories to save files
		workingdir = os.path.dirname(__file__) # absolute path to current directory
		PUfile = os.path.join(workingdir, 'waittimefiles/wait_pu_lambda_{0}.csv'.format(l))
		os.makedirs(os.path.dirname(PUfile), exist_ok = True)
		GUfile = os.path.join(workingdir, 'waittimefiles/wait_gu_lambda_{0}.csv'.format(l))
		os.makedirs(os.path.dirname(GUfile), exist_ok = True)
		print('Starting lambda = {0}, phi = {1}'.format(l,p))
		Simulator(l, mu, p, sigma, PUfile, GUfile)

print('Simulations Complete')