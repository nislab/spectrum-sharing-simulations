# spectrum-sharing-simulations

Simulations for Priority Purchasing Queuing Games with a focus on Wireless Spectrum Coexistence.

Within the realm of wireless spectrum, much of available useful spectrum has already been allocated to various incumbents. On top of this, there exists a 

------------

# Dpendencies

The main simulations utilize Python code, specifically [SimPy](https://simpy.readthedocs.io/en/latest/contents.html)

To utilize the code, in addition to SimPy, it is also necessary to install NumPy and SciPy for statistical analysis. These can be installed using pip:

```
pip install numpy
pip install scipy
pip install simpy
```

--------------

# Usage

The simulation code consists of various scripts corresponding to various scenarios within the realm of spectrum sharing and co-existence. 

1. The Full Active directory corresponds to secnarios wherein all users are considered to be active users of spectrum, corresponding to the standard M/G/1 multi-tier queue. 

1a. The Two-Class subdirectory consists of four scripts featuring varying policies and service distributions where there exist a Primary and Secondary class of customer making the purchasing decision:

* MD1_NP_Two_Class.py - M/D/1 (Deterministic Service) with Non Preemptive service policy
* MM1_NP_Two_Class.py - M/M/1 (Exponential Service) with Non Preemptive service policy
* MG1_NP_Two_Class.py - M/G/1 (General Service) with Non Preemptive service policy - as a policy must be specified, the script utilizes the Gamma Distribution with a user controlled parameter representing the second moment of service to control the empricial service distribution.
* MG1_PR_Two_Class.py - M/G/1 with Preemptive Resume service policy - as with the NP version, the Gamma Distribution with user controlled parameter is used to control the empirical service distribution

Each of these scripts can be run standalone, with the parameters edited directly as needed.

1b. The CBRS Like subdirectory consists of scripts based on a CBRS Like structure, which incorporates a third, independent Incumbent class with higher priority compared to the Primary and Secondary class users. 

The main simulation is contained in the CBRS Queuing Delays folder, consisting of the following files:

* CBRS_WaitTime_Sim.py - Contains the main simulation code for the CBRS-Like simulations, used to simulate for costs and revenues associated with a desired fraction of Primary customers.
* CBRS_WaitTime_Wrapper.py - A wrapper to call the simulator associated with the CBRS_WaitTime_Sim file to loop over input variables, and specifiy relative file location/name to save the costs and revenues.
* CBRS_WaitTime_Preemption_Sim.py - Contains a modified version of the main simulation code, instead returns statistics on the number, waittimes, and number of preemptions for each class of user to compare against expected values.
* CBRS_WaitTime_Preemption_Wrapper.py - A wrapper for the above to loop over input variables and specifie relative file locations/names for the user class information. 


The Learning Games folder contains standalone scripts which iterate the simulation itself to validate claims on the equilibrium stability updating the equilibrium beleief by comparing simulated costs and adjusting in favor of the class with the lower cost. The scripts consist of the following:

* CBRS_Base.py - Runs the action learning algorithm and returns a file consisting of the progression of the equilibrium belief at each step as well as the actual system delays and expected delays for each customer class.
* CBRS_Customer_Action_Learning.py - Runs the action learning algorithm and returns a file consisting of the progression of the equilibrium belief at each step as well as a Confidence Interval as the simulation is repeated multiple times before making the decision. 

Note that CBRS_Base and CBRS_Customer_Action_Learning use slightly different comparisons, as the latter also considers preemption as a cost while the former only considers the cost of system delay/wait time.


2. The Active-Passive Sharing directory corresponds to scenarios wherein there exists an incumbent passive class of spectrum users, such as the Earth Exploration Satellite Service radiometers, resulting in an *on-off* M/G/1 Queuing Model, cf. Avi-Itzhak, B., and P. Naor. "Some queuing problems with the service station subject to breakdown." *Operations Research* 11.3 (1963): 303-320. Specifically, we consider Model A from the cited paper, where Preemptive Resume behavior is in effect.

2a. The Single Class subdirectory consists of standalone scripts wherein there is a single customer class attempting to join the queue, and are presented with a join-or-balk decision vs the primary-vs-secondary class decision typical of our other simulators:

* 2_mg1_sbd_model_A.py - Simulates the *on-off* (a/k/a service breakdown) M/G/1 queue with preemptive resume, for fixed parameters related to the breakdowns. The "2" refers to the breakdowns being caused by an incumbent tier, resulting in a total of two classes.
* 2_mg1_sbd_model_A_traces.py - Modifies the previous script to accept csv files containing processed trace data corresponding to the arrival times between breakdown periods and the lengths of the breakdowns. The traces can be from any source but were originally intended as a means to validate our models against data collected in the [passive-radiometer-trace-data](https://github.com/nislab/passive-radiometer-trace-data) respository, processed to determine the interarrival times between overpasses and the lengths of the satellite overpass periods.

2b. The Two Class subdirectory consists of standalone scripts wherein there are once again two customer classes attempting to join the queue, and are presented with the deicsion of which class to join:

* 3_mg1_sbd_model_A.py - Simulates the *on-off* (a/k/a service breakdown) M/G/1 queue with preemptive resume, for fixed parameters related to the breakdowns. Similar to the script in the Single Class subdirectory, the "3" represents the total number of classes present; the Incumbents causing the breakdowns, and the Primary and Secondary user classes in the service queue itself.
* 3_mg1_sbd_model_A_traces.py - Modifies the previous script to accept csv files containing processed trace data, similarly to its Single Class counter part.
* 3_mg1_sbd_model_A_traces_rev_sw.py - Similar to the previous script, but instead calculates the resulting revenue from admissions, and the social welfare of the users active in the system
* 3_mg1_sbd_model_A_traces_action_learning.py - A dyanmic game played within the M/G/1 on-off setting, incorporating trace data.

------------------------

# Inputs


# Parameters


# Outputs



------------------------

# License


These materials may be freely used and distributed, provided that attribution to this original source is acknowledged. If you reuse the code in this repository, we kindly ask that you refer to the relevant work (cf. the included bib files in the citation directory of this repository):


-----------------
# References

If you are leveraging this code in your work and would like to be featured in this list, kindly create an issue in this repository and provide us with the reference.

-----------------
# Acknowledgment

Support by the US National Science Foundation is gratefully acknoweldged 

* 
* 
* 