"""
Analysis for the outputs of the MM1_Two_Class_Switchover_Sim Simulator
Generates figures based on the output files from the simulation
Files are CSVs containing the mean flow times and confidence intervals for a given value of
lambda and phi; per class of user.
Author: Jonathan Chamberlain, 2021 jdchambo@bu.edu
"""


import matplotlib.pyplot as plt
from matplotlib import rc
import os
import numpy as np
import csv

# Define fonts and formatting for the plots.
rc('text', usetex = True) # use LaTeX font and formatting
font = {'family' : 'sans-serif',
        'weight' : 'bold',
        'size'   : 12}
rc('font', **font)

# define PHI over which to plot the analytical curves; PHI is [0,1]
PHI = np.zeros(1001)
for p in range(1001):
	PHI[p] = p/1000

# define the values of PHI to plot the simualted results
PHI_SIM = [0.05, 0.1, 0.15, 0.2, 0.25, 0.3, 0.35, 0.4, 0.45, 0.5, 0.55, 0.6, 0.65, 0.7, 0.75, 0.8, 0.85, 0.9, 0.95]

'''
Indicate the values of the remaining parameters
lam - arrival rate(s)
mu - service rate
sigma - switchover rate
'''
LAM = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]
MU = 1
SIGMA = 1

# Loop over desired values of LAM to generate plots based on simulator results
for l in range(len(LAM)):
	lam = LAM[l]
	rho = lam/MU
	# create figure
	workingdir = os.path.dirname(__file__) # absolute path to current directory
	figfile = os.path.join(workingdir, 'waitanalysisfiles/test_lambda_{0}.png'.format(lam))
	os.makedirs(os.path.dirname(figfile), exist_ok = True)
	fig = plt.figure()
	ax = plt.subplot(111)
	# plot analytical PU Wait curve for given lambda
	WPU = np.zeros(1001) 
	for p in range(1001):
		phi = PHI[p]
		WPU[p] = 1/(MU*(1-rho*phi))
	plt.plot(PHI, WPU, label='E[W_{PU}] analytical')
	# plot analytical GU Wait curve for given lambda
	WGU = np.zeros(1001) 
	for p in range(1001):
		phi = PHI[p]
		#WGU[p] = 1/(MU*(1-rho*phi)) + rho/(MU*(1-rho*phi)*(1-rho)) # without switchovers, used for comparison plot
		WGU[p] = (SIGMA**2+lam*phi*(MU+lam*phi)*(1-rho*phi)+SIGMA*phi*(3*lam-2*lam*rho*phi))/(MU*(SIGMA+lam*phi)*(1-rho*phi)*(SIGMA*(1-rho)-lam*rho*phi*(1-phi)))
	plt.plot(PHI, WGU, label='E[W_{GU}] analytical') 
	# plot simulated PU Waits for given lambda
	WPU_sim = np.zeros(len(PHI_SIM))
	WPU_err = np.zeros(len(PHI_SIM))
	i = 0
    # read in from CSV files
	waitfile = os.path.join(workingdir, 'waittimefiles/wait_pu_lambda_{0}.csv'.format(lam)) # CSV file containing mean costs - uses default separator, line termination values
	with open(waitfile, 'r') as waitcsv:
		wait = csv.reader(waitcsv)
		for row in wait:
			waitvals = [float(m) for m in row]
			WPU_sim[i] = waitvals[0]
			WPU_err[i] = waitvals[1]
			i += 1
	plt.errorbar(PHI_SIM, WPU_sim, yerr = WPU_err, fmt = 'x', label = 'E[W_{PU}] simulated')
	# plot simulated GU Waits for given lambda
	WGU_sim = np.zeros(len(PHI_SIM))
	WGU_err = np.zeros(len(PHI_SIM))
	i = 0
    # read in from CSV files
	waitfile = os.path.join(workingdir, 'waittimefiles/wait_gu_lambda_{0}.csv'.format(lam)) # CSV file containing mean costs - uses default separator, line termination values
	with open(waitfile, 'r') as waitcsv:
		wait = csv.reader(waitcsv)
		for row in wait:
			waitvals = [float(m) for m in row]
			WGU_sim[i] = waitvals[0]
			WGU_err[i] = waitvals[1]
			i += 1
	plt.errorbar(PHI_SIM, WGU_sim, yerr = WGU_err, fmt = 'x', label = 'E[W_{GU}] simulated')
	# Lable axes and include legend
	plt.xlabel('$\\phi$')
	plt.ylabel('$Normalized Wait Times$')
	box = ax.get_position()
	ax.set_position([box.x0, box.y0, box.width, box.height*0.9])
	ax.legend(loc = 'upper center', bbox_to_anchor=(0.5,1.2), fancybox = True, shadow=True, ncol=3)
	plt.savefig(figfile)
	plt.close()



