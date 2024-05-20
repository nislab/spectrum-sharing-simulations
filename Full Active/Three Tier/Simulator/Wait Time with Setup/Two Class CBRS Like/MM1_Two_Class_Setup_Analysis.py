'''
MM1_PR_eqanalysis - plots to support the equilibrium analysis for MM1 with preemptive resume and setup times
'''

import matplotlib.pyplot as plt
from matplotlib import rc
import os
import numpy as np
import csv

'''
Define loop for plots
Lambda varies between 0.1 and 0.9, mu is fixed at 1
Plot analytical curve with respect to Phi from 0 to 1, in increments of 1/1000
Plot simulated results at given thresholds from 0.1 to 0.9
'''
rc('text', usetex = True) # use LaTeX font and formatting
font = {'family' : 'sans-serif',
        'weight' : 'bold',
        'size'   : 12}
rc('font', **font)

# define values of Phi to plot analytical function
PHI = np.zeros(1001)
for p in range(1001):
	PHI[p] = p/1000

# define values of Phi to plot simulated results
PHI_SIM = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]
LAM = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]
MU = 1
SIGMA = 1

for l in range(len(LAM)):
	lam = LAM[l]
	rho = lam/MU
	# create figure
	workingdir = os.path.dirname(__file__) # absolute path to current directory
	figfile = os.path.join(workingdir, 'eqanalysisfiles/test_lambda_{0}.png'.format(lam))
	os.makedirs(os.path.dirname(figfile), exist_ok = True)
	fig = plt.figure()
	ax = plt.subplot(111)
	# plot analytical Cost for given lambda
	C = np.zeros(1001) 
	for p in range(1001):
		C[p] = (MU**2+lam*(SIGMA+lam*(1-2*PHI[p])*PHI[p]))/((MU-lam*PHI[p])*(SIGMA*(MU-lam)-lam**2*PHI[p]*(1-PHI[p])))
		#C[p] = (lam*(SIGMA+PHI[p]*(lam+MU-2*lam*PHI[p])))/((MU-lam*PHI[p])*(SIGMA*(MU-lam)-(lam**2)*(1-PHI[p])*PHI[p]))
	plt.plot(PHI, C, label='C($\\phi$) analytical') 
	# plot simulated results
	C_sim = np.zeros(len(PHI_SIM))
	C_err = np.zeros(len(PHI_SIM))
	i = 0
    	# read in from CSV files
	costfile = os.path.join(workingdir, 'costfiles/costs_lambda_{0}.csv'.format(lam)) # CSV file containing mean costs - uses default separator, line termination values
	with open(costfile, 'r') as costcsv:
		costs = csv.reader(costcsv)
		for row in costs:
			costvals = [float(m) for m in row]
			C_sim[i] = costvals[0]
			C_err[i] = costvals[1]
			i += 1
	plt.errorbar(PHI_SIM, C_sim, yerr = C_err, fmt = 'x', label = 'C($\\phi$) simulated')
	# from simulated data, plot results
	plt.xlabel('$\\phi$')
	plt.ylabel('$C$')
	box = ax.get_position()
	ax.set_position([box.x0, box.y0, box.width, box.height*0.9])
	ax.legend(loc = 'upper center', bbox_to_anchor=(0.5,1.2), fancybox = True, shadow=True, ncol=3)
	plt.savefig(figfile)
	plt.close()



