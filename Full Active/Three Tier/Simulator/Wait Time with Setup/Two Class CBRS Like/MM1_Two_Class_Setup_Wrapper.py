"""
Wrapper to define values for MM1_Two_Class_Setup_Sim Simulator, define save files for statistics
Author: Jonathan Chamberlain, 2021 jdchambo@bu.edu
"""

from MM1_Two_Class_Setup_Sim import Simulator
import os

'''
Define loop for simulators
Loop over values of lambda from 0.1 to 0.9
Loop over values of phi from 0.1 to 0.9
Fix Mu at 1
Save Mean wait times, error bounds, normalized error per threshold
Save figures for each run
'''

lam = [0.04, 0.055]
mu = 0.1
phi = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]
sigma = 1.5


for i in range(2):
	l = lam[i]
	for j in range(9):
		p = phi[j]
		# define files and directories to save files
		workingdir = os.path.dirname(__file__) # absolute path to current directory
		costfile = os.path.join(workingdir, 'costfiles/costs_lambda_{0}.csv'.format(l))
		os.makedirs(os.path.dirname(costfile), exist_ok = True)
		print('Starting lambda = {0}, phi = {1}'.format(l,p))
		Simulator(l, mu, p, sigma, costfile)

print('Simulations Complete')