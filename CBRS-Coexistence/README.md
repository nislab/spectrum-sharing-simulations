# Usage

To Run the simulations in this folder, the usage depends on the scenario:

The Queuing-Delay simulations are intended to be run via their wrapper functions, and should be called via the corresponding wrappers, with inputs modified via said wrapper files. However, the Sim files can be called directly provided the inputs are all specified on the command line.

The primary difference between the two functions is in the statistics output

* CBRS_Queuing_Sim_Standard.py - Contains the main code for the CBRS-Coexistence simulations, used to simulate the queuing interactions between user agents, and returns  costs and revenues associated with a desired fraction of Primary/Priority customers.
* CBRS_Starndard_Wrapper.py - The wrapper associated with the above, defining the input variables and specifying the relative file locations to save the output costs and revenues for later analysis.
* CBRS_Queuing_Sim_Preemption_Counter.py - A modified version of the simulation code, which instead returns statistics broken out per-class on the number of agents generated, their wait times, and the number of preemptions faced by users compared to the expected values.
* CBRS_Preemption_Wrapper.py - The wrapper associated with the above, again defining the input variables, and specifying the relative file locations to save outputs related to each class's statistics.

The Learning simulations can be called via the command line, with their inputs modified via the script files directly.

* CBRS_Base.py - Runs the action learning algorithm and returns a file consisting of the progression of the equilibrium belief at each step as well as the actual system delays and expected delays for each customer class.
* CBRS_Customer_Action_Learning.py - Runs the action learning algorithm and returns a file consisting of the progression of the equilibrium belief at each step as well as a Confidence Interval as the simulation is repeated multiple times before making the decision

Note that CBRS_Base and CBRS_Customer_Action_Learning use slightly different comparisons, as the latter also considers preemption as a cost while the former only considers the cost of system delay/wait time.
------------

# Inputs

In the case of the Queuing-Delay scripts, certain of the inputs are accepted via the wrapper files and should be edited there:

The functions in CBRS Like/CBRS Queuing Delays accept inputs via the wrapper functions:

* lam - the customer arrival rate lambda, lam > 0 is required. lam is generally assumed to be a vector of arrival rates.
* mu - the customer service rate mu, 0 < LAM < MU is required for a stable system; currently the default value is 1 (i.e. service is normalized)
* phi - the fraction of customers joining the primary service class, this must be a fraction in [0,1]. phi is generally assumed to be a vector of multiple candidate fractions.
* k - a parameter tied to the service variance, K is specifically defined in terms of the second moment of the service distribution, such that the second moment is k/mu^2. Thus, k >= 1 follows. 

The combination of k and mu determine the specific service distribution. k = 1 will result in a deterministic distribution. Otherwise, a Gamma distribution is utilized by default; k and mu are utilized to define the corresponding SHAPE and SCALE parameters of the Gamma - note that k = 2 will result in an Exponential distribution, itself a special case of the Gamma.

To update the distribution utilized to one of the other supported [NumPy random sampling distributions](https://numpy.org/doc/stable/reference/random/index.html), it is necessary to change the line(s) where customer serv_time are determined, as well as update dependant parameters. Given the nature of the simulators in relation to the queuing delay formulas, it is recommended that these be defined in terms of K and MU. For instance, if leveraging lognormal distributions, the line

'''
serv_time = np.random.gamma(SHAPE,SCALE)
'''

must be replaced with

'''
serv_time = np.random.lognormal(mean,stddev)
'''

With mean set equal to 1/mu, and stddev defined in terms of variance, which is in turn defined in terms of the first and second moments. (This may also require redefining the generator functions due to the code using an earlier version of NumPy)

* lami - the incumbent arrival rate.
* mui - the incumbent service rate.
* ki - the incumbent second moment of service paraemter defining the empirical service distribution. The same comments relating to mu and k also apply to mui and ki (with corresponding SHAPEi and SCALEi parameters)

CBRS_Preemption_Wrapper has the ability to specify multi-server scenarios:

* cap - controls the server capacity and is passed to the corresponding CAPACITY input variable in the file; by default this is 1 and attempts to validate for c > 1 even for known cases have returned errors in prior instances in SimPy 3. Currently unknown if works as intended for known cases in SimPy 4.

The wrappers also specify the output file destinations, where lambda_{0} denotes the current value of lambda (and thus if the primary loop uses a different variable, the defualt file names should be updated accordingly):

* workingdir - the path to the root directory to store the files; by default this is the current directory, specified using os.path.dirname(__file__) 
* costfile - in CBRS_Preemption_Wrapper, the path to store the cost and revenue data file; by default this is costfiles/cost_stats_lambda_{0}
* incfile - in CBRS_Preemption_Wrapper, the path to the incumbent statistics; by default statfilefiles/inc_stats_lambda_{0}.csv 
* pufile - in CBRS_Preemption_Wrapper, the path to the primary/priority statistics statfilefiles/pu_stats_lambda_{0}.csv 
* gufile - in CBRS_Preemption_Wrapper, the path to the secondary/general statistics, statfilefiles/gu_stats_lambda_{0}.csv 

# Parameters

In addition to the Inputs above the following parameters are editable within the scripts (in addition to lam, mu, k, phi, lami, mui, ki, and CAPACITY being parameters in the Learning scripts):

* SIM_TIME - The length of time to run the simulation over. The default is typically set on a sliding scale such that on the order of ~500,000 customers are created.
* FRAC - The fraction of time elapsed before statistics are collected, to allow the system to reach steady state conditions. By default this is set to 0.1 so that the related T_START variable is set to a value of 10% of the value of SIM_TIME. 
* ITERATIONS - The number of indepdendent simulations, by default this is usually 30. 
* ALPHA - Used to set the confidence interval. By default this is 0.05 corresponding to CIs of 95%. (In the Learning Games this is also used to determine how many customers can switch their strategy between rounds)

The Learning Games have the following additional parameters:

* C - the fixed cost to join the Primary/Priority queue
* ROUNDS - the number of rounds to repeat the game over, as distinct from the number of repeated simulations within a round. Rounds are the outer loops controlling the decision over how to update the equilibrium belief and by what amount based on the results obtained, which may be the result of repeated iterations to observe for outliers. 
* Vp - the Quality of Service "value of preemption"; i.e. the valuation placed on the costs of service interruptions caused by higher class users, in addition to the implicit costs of extended delay.

# Simulators

As with the other simulation types, the simulators operate via looping over the duration of SIM_TIME over a series of independent processes:

provider - consisting of the actual server processing each user agent
(cust)arrivals - the arrival process corresponding to the customers
incumbent/incarrivals - the arrival process corresponding to the incumbents

The primary difference between this and the No-Incumbent code is the existence of incumbents as a distinct process with their own statistics, and who are not split into separate subclasses. Otherwise, the main loop functions near identically to that of the No-Incumbent/Preemptive_Resume.py code, where users are generated according to exponential delay, and in the case of customers sorted into the priority classes with probability PHI. The sole difference being that the priroities are 1 and 2 with the incumbents automatically having priority 0. All users are fed into the queue with service times generated according to the specified distribution, with preemptions handled as appropriate. Statistics are collected upon customers exiting the queue.

For the Queuing-Delay scripts, these are processed and saved to the specified files.

For the Learning scripts, these are used to update the strategy decision in the next ROUND. The observed costs being in one class versus the other are compared, with ALPHA percent of customers switching in favor of the strategy with the lower cost each round. The difference between the two scripts is that in CBRS_Base, each Round consists of a single iteration, while in CBRS_Customer_Action_Learning, each round consists of a full series of iterations - with the new value of PHI depending on the average of what the players determine after each iteration. That is, each iteration in the same round uses the same value of PHI as the equilibrium belief, with the updated PHI being based on the average of PHI +/- ALPHA across all iterations in the round.


# Outputs

The outputs in the Queuing-Delay scripts are CSV files corresponding to the file paths specified in the Inputs section:

costfile - a file of vectors of the costs to join the Primary class, the corresponding revenue, and the 95% CI error, in the form [Mean Costs, Cost error delta, Mean Revenue, Revenue error delta]
incfile - a file of vectors of statistics related to incumbent data, in the form [Mean wait times, Wait time error Delta, Mean number of incumbents, number of incumbent error Delta, Mean number of preemptions, number of preemptions error Delta].
pufile - a file of vectors of statistics related to primary/priority customer data, in the form [Mean wait times, Wait time error Delta, Mean number of primary customers, number of primary customer error Delta, Mean number of preemptions, number of preemptions error Delta].
gufile - a file of vectors of statistics related to secondary/general access data, in the form [Mean wait times, Wait time error Delta, Mean number of secondary customers, number of secondary customer error Delta, Mean number of preemptions, number of preemptions error Delta].

Files append entires, thus under the default structure each line corresponds to the PHI value specified in the wrapper for the lambda in the file name.

The outputs in the Learning scripts are also CSV files, specified in the script files directly and named by default results.csv in the current working directory, consisting of the relevant products of the learning game simulations:

* CBRS_Base.py returns vectors of the customers' chosen equilibrium strategy belief, mean wait times of each user class, and the corresponding expected wait times for each customer class based on the given choice of equilibrium strategy in the form [PHI, incumbent mean wait, primary mean wait, primary expected wait, secondary mean wait, secondary expected wait].
* CBRS_Customer_Action_Learning.py returns vectors of the customers' chosen strategy and the corresponding error from the simulations undertaken in each round, in the form [PHI, PHI error delta].