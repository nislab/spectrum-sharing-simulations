# spectrum-sharing-simulations

Simulations for Priority Purchasing Queuing Games with a focus on Wireless Spectrum Coexistence.

Within the realm of wireless spectrum, much of available useful spectrum has already been allocated to various incumbents. On top of this, said incumbents are given overprotection from interference and secondary use with hampers sharing. Our goal is to evaluate an Open Access Spectrum market as an alternative for allocation of frequencies, particularly in settings where incumbent allocations with minimal (< 5% utilization) exist, leaving whitespace available for commerical markets to form. 

The markets in question are those of wholesale industrial users (cellular providers, edge compute networks managing city scale smart infrastructure, transportation authorities operating positive train control systems, etc.) rather than those of the indvidual clients who connect to the applications and services established by service providers among these industrial users. 

For further reading, we direct you to the papers referenced in the Liscence section.

------------

# Dpendencies

The main simulations utilize Python code, specifically [SimPy](https://simpy.readthedocs.io/en/latest/contents.html).

To utilize the code, in addition to SimPy, it is also necessary to install NumPy and SciPy for statistical analysis. These can be installed using pip:

```
pip install numpy
pip install scipy
pip install simpy
```

The pyplot module from [matplotlib](https://matplotlib.org/stable/) is also required to run certain scripts; matplotlib can also be installed using pip:

```
pip install matplotlib
```

--------------

# Usage

The simulation code consists of various scripts corresponding to various scenarios within the realm of spectrum sharing and co-existence. 

1. The Full Active directory corresponds to scenarios wherein all users are considered to be active users of spectrum, corresponding to the standard M/G/1 multi-tier queue. 

1a. The Two-Class subdirectory consists of four scripts featuring varying policies and service distributions where there exist a Primary and Secondary class of customer making the purchasing decision:

* MD1_NP_Two_Class.py - M/D/1 (Deterministic Service) with Non Preemptive service policy.
* MM1_NP_Two_Class.py - M/M/1 (Exponential Service) with Non Preemptive service policy.
* MG1_NP_Two_Class.py - M/G/1 (General Service) with Non Preemptive service policy - as a policy must be specified, the script utilizes the Gamma Distribution with a user controlled parameter representing the second moment of service to control the empricial service distribution.
* MG1_PR_Two_Class.py - M/G/1 with Preemptive Resume service policy - as with the NP version, the Gamma Distribution with user controlled parameter is used to control the empirical service distribution.

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
* 3_mg1_sbd_model_A_traces_rev_sw.py - Similar to the previous script, but instead calculates the resulting revenue from admissions, and the social welfare of the users active in the system.
* 3_mg1_sbd_model_A_traces_action_learning.py - A dyanmic game played within the M/G/1 on-off setting, incorporating trace data.

------------------------

# Inputs

The functions in CBRS Like/CBRS Queuing Delays accept inputs via the wrapper functions:

* LAM - the customer arrival rate lambda, LAM > 0.
* MU - the customer service rate mu, 0 < MU < LAM is required for a stable system.
* K - the customer second moment of service paremter defining the empirical service distribution, K >= 1.  
* LAMi - the incumbent arrival rate.
* MUi - the incumbent service rate.
* Ki - the incumbent second moment of service paraemter defining the empirical service distribution.
* PHI - the fraction of customers joining the primary service class.

CBRS_WaitTime_Sim.py has the following additional input to specify the path to store its output, defined in its wrapper by default as follows:

* costfile = costfiles/cost_stats_lambda_{0} - path to the file storing cost and revenue data.

CBRS_WaitTime_Preemption_Sim.py has the following additional inputs, including paths to store outs with defaults defined in its corresponding wrapper:

* CAPACITY - Total capacity of the server, enables multiserver queues to be considered.
* incfile = statfilefiles/inc_stats_lambda_{0}.csv - path to the file storing incumbent statistics.
* pufile = statfilefiles/pu_stats_lambda_{0}.csv - path to the file storing primary/priority customer statistics.
* gufile = statfilefiles/gu_stats_lambda_{0}.csv - path to the file storing secondary/general customer statistics.


# Parameters

In addition to the Inputs above serving as parameters to standalone scripts where applicable, the following parameters are common to all scripts:

* SIM_TIME - The length of time to run the simulation over. The default is typically set on a scale such that on the order of ~100,000 customers are created. If using a script with traces, SIM_TIME should be set to the exact length of time the traces cover to avoid errors.
* FRAC - The fraction of time elapsed before statistics are collected, to allow the system to reach steady state conditions. By default this is set to 0.1 so that the related T_START variable is set to a value of 10% of the value of SIM_TIME. 
* ITERATIONS - The number of indepdendent simulations, by default this is 30. 
* ALPHA - Used to set the confidence interval. By default this is 0.05 corresponding to CIs of 95%.

The following parameters are common to scripts involving trace data. Technically these parameters are coded as empty vectors extended by the reader function in order to pass the data in a usable format. The related files are specified in the loop on the line below the parameter declaration.

* IN_ARRIVALS - the csv containing the interarrival times of the on/off periods; a/k/a the interarrival times between incumbent arrivals. By default this expects a file named interArrival.csv.
* IN_SERVICE - the csv containing the breakdown lengths of the on/off periods; a/k/a the service periods of the incumbents. By default this expects a file named sweepPeriod.csv.

The following parameters are common to scripts involving the Learning games 

* C/F - the fixed cost to join the Primary/Priority queue. 
* ROUNDS - the number of rounds to repeat the game over, as distinct from the number of repeated simulations within a round. Rounds are the outer loops controlling the decision over how to update the equilibrium belief and by what amount based on the results obtained, which may be the result of repeated iterations to observe for outliers. 
* Cp/Vp - the "cost of preemption", i.e. the valuation placed on the costs of service interruptions caused by interruptions by higher class users.


# Outputs

1a. The scripts in the Full Active/Two Class Directory generate plots of the simulated results compared against the expected results.

1b. The scripts in the Full Active/CBRS Like/CBRS Queing Delays directory generate CSV files containing the products described in the inputs section:

* costfile - consists of vectors of simulated mean costs to join the Primary class and resultant revenues and the error bound, under the assumption that PHI is an equilibrium state for the given parameters, in the form [Mean Costs, Cost error delta, Mean Revenue, Revenue error delta].
* incfile - consists of vectors of the mean wait times, mean number of incumbents, and mean number of preemptions of incumbents and accompanying error bounds, in the form [Mean wait times, Wait time error Delta, Mean number of incumbents, number of incumbent error Delta, Mean number of preemptions, number of preemptions error Delta].
* pufile - consists of vectors of the mean wait times, mean number of primary/priority customers, and mean number of preemptions of incumbents and accompanying error bounds, in the form [Mean wait times, Wait time error Delta, Mean number of primary customers, number of primary customer error Delta, Mean number of preemptions, number of preemptions error Delta].
* gufile - consists of vectors of the mean wait times, mean number of secondary/general customers, and mean number of preemptions of incumbents and accompanying error bounds, in the form [Mean wait times, Wait time error Delta, Mean number of secondary customers, number of secondary customer error Delta, Mean number of preemptions, number of preemptions error Delta].

The scripts in the Full Active/CBRS Like/Learning Games directory return a csv, named by default 'results.csv', consisting of the products of the learning game simulations as described in the Usage section:

* CBRS_Base.py returns vectors of the customers' chosen equilibrium strategy belief, mean wait times of each user class, and the corresponding expected wait times for each customer class based on the given choice of equilibrium strategy in the form [PHI, incumbent mean wait, primary mean wait, primary expected wait, secondary mean wait, secondary expected wait].
* CBRS_Customer_Action_Learning.py returns vectors of the customers' chosen strategy and the corresponding error from the simulations undertaken in each round, in the form [PHI, PHI error delta].

2a. The scripts in Active-Passive Sharing/Single Class folder return csv files detailing statistics related to each user type, with the following default names specified in the scripts themselves:

* eess_data.csv - consists of vectors of the statistical system delay data and number of preemptions by the incumbent class (as represented by Earth Exploration Satellite Service, for example) and corresponding error ranges for the condfidence intervals, in the form [Incumbent mean wait, Incumbent mean error Delta, Incumbent mean preemption, Incumbent mean error Delta].
* customer_data.csv - consists of vectors of the stasitical system delay data and number of preemptions by the customer class, and corresponding error ranges for the confidence intervals, in the form [Customer mean wait, Customer mean error Delta, Customer mean preemption, Customer mean error Delta].

2b. The scripts in Active-Passive Sharing/Two Class folder return csv files which depend on the script being run.

3_mg1_sbd_Model_A.py and 3_mg1_sbd_Model_A_traces.py return the following files, with the follwing default names specified in the file itself:

* passive_incumbent_data.csv - consists of vectors of the statistical system delay data and number of preemptions by the incumbent class and corresponding error ranges for the condfidence intervals, in the form [Incumbent mean wait, Incumbent mean error Delta, Incumbent mean preemption, Incumbent mean error Delta].
* premium_customer_data.csv - consists of vectors of the stasitical system delay data and number of preemptions by the primary/premium customer class, and corresponding error ranges for the confidence intervals, in the form [Customer mean wait, Customer mean error Delta, Customer mean preemption, Customer mean error Delta].
* standard_customer_data.csv - consists of vectors of the stasitical system delay data and number of preemptions by the secondary/standard customer class, and corresponding error ranges for the confidence intervals, in the form [Customer mean wait, Customer mean error Delta, Customer mean preemption, Customer mean error Delta].

3_mg1_sbd_Model_A_rev_sw.py returns the following files, with the follwing default names specified in the file itself:

* revenue_data.csv - consists of vectors of the statistical mean revenue generated and corresponding errors, in the form [Mean revenue, Revenue error Delta]. 
* social_data.csv - consists of vectors of the statistical mean social welfare corresponding to the specified parameters, in the form [Mean Social Welfare, Social Welfare error Delta].

3_mg1_sbd_Model_A_traces_action_learning.py returns vectors of the customers' chosen strategy and the corresponding error from the simulations undertaken in each round, in the form [PHI, PHI error delta].

------------------------

# License


These materials may be freely used and distributed, provided that attribution to this original source is acknowledged. If you reuse the code in this repository, we kindly ask that you refer to the relevant work (cf. the included bib files in the citation directory of this repository):

* Full Active/CBRS Like scripts

Chamberlain, Jonathan, and David Starobinski. "Game Theoretic Analysis of Citizens Broadband Radio Service." 2022 20th International Symposium on Modeling and Optimization in Mobile, Ad hoc, and Wireless Networks (WiOpt). IEEE, 2022.

* Active-Passive Sharing/Single Class scripts

Chamberlain, Jonathan, Joel T. Johnson, and David Starobinski. "Spectrum Sharing between Earth Exploration Satellite and Commercial Services: An Economic Feasibility Analysis." 2024 IEEE International Symposium on Dynamic Spectrum Access Networks (DySPAN). IEEE, 2024.

* Active-Passive Sharing/Two Class scripts

Chamberlain, Jonathan, David Starobinski, and Joel T. Johnson. "Facilitating Spectrum Sharing with Passive Satellite Incumbents." IEEE Journal on Selected Areas in Communications (2024).

-----------------
# References

If you are leveraging this code in your work and would like to be featured in this list, kindly create an issue in this repository and provide us with the reference.

-----------------
# Acknowledgment

Support by the US National Science Foundation is greatfully acknoweldged, with these scripts developed in support of work which is supported in part by the following grants: 

* CNS-1717858
* CNS-1908087
* AST-2229103  
* AST-2229104