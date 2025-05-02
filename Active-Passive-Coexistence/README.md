# Usage

To Run the simulations in this folder, run the corresponding script on the command line. 

The Single-Customer code corresponds to the base EESS-passive scenario, where comparisons are against only a single class of customer, thus customers join-or-balk:

* EESS_Single_Customer_Base.py - Contains the base code featuring fully synthetically generated customers and incumbents
* EESS_Single_Customer_Traces.py - Contains code which accepts processed trace data as inputs to the code for the incumbent data
* EESS_Sinlge_Customer_Var_Latitude.py - Contains code which performs simulations based on (sythetically generated) incumbent arrivals at varying locations

The Two-Customer code corresponds to the scenario variant where the secondary customer class is present and customers choose between which class to join:

* EESS_Two_Customer_Base.py - Contains the base code for the two customer scenario
* EESS_Two_Customer_Traces.py - Contains code accepting processed trace data as inputs to the code for incumbent data
* EESS_Two_Customer_Traces_Rev_Sw.py - A modified version of the above evaluating the revenue and social welfare data for a given configuration
* EESS_Two_Customer_Traces_Action_Learning.py - A modified version of the above where customers determine the optimal equilibrium decision via an action learning game.


## Dependencies

In addition to the dependencies listed in the main folder, the Traces scripts require formatted input corresponding to EESS-passive arrival and overpass patterns. These take the form of vectors processed from data in the [passive-radiometer-trace-data](https://github.com/nislab/passive-radiometer-trace-data) repository. 

## Inputs

Inputs and parameters are sepecified directly within the script files and can be updated via direct edits:

* LAM - the customer arrival rate lambda, LAM > 0. In the single customer case, this can be passed in as a vector of multiple values to loop over; for the Two customer case the code will require modification to accomodate this
* MU - the customer service rate mu, 0 < MU < LAM is required for a stable system.
* PHI - the fraction of customers joining the (primary) service class. In the Single customer case this is assumed part of Lambda and not a distinct variable. 
* K - the customer second moment of service paremter defining the empirical service distribution, K >= 1.  

The combination of K and MU determine the specific service distribution. K = 1 will result in a deterministic distribution. Otherwise, a Gamma distribution is utilized by default; K and MU are utilized to define the corresponding SHAPE and SCALE parameters of the Gamma - note that K = 2 will result in an Exponential distribution, itself a special case of the Gamma.

To update the distribution utilized to one of the other supported [NumPy random sampling distributions](https://numpy.org/doc/stable/reference/random/index.html), it is necessary to change the line(s) where customer serv_time are determined, as well as update dependant parameters. Given the nature of the simulators in relation to the queuing delay formulas, it is recommended that these be defined in terms of K and MU. For instance, if leveraging lognormal distributions, the line

'''
serv_time = np.random.gamma(SHAPE,SCALE)
'''

must be replaced with

'''
serv_time = np.random.lognormal(mean,stddev)
'''

With mean set equal to 1/MU, and stddev defined in terms of variance, which is in turn defined in terms of the first and second moments. (This may also require redefining the generator functions due to the code using an earlier version of NumPy)

* LAMBDA_IN - the incumbent arrival rate.
* MU_IN - the incumbent service rate.
* K_IN - the incumbent second moment of service paraemter defining the empirical service distribution.

* SIM_TIME - The length of time to run the simulation over. The default is typically set on a scale such that on the order of ~100,000 customers are created. If trace files are being used, SIM_TIME should equal the length of the period the traces cover to avoid errors.
* FRAC - The fraction of time elapsed before statistics are collected, to allow the system to reach steady state conditions. By default this is set to 0.1 so that the related T_START variable is set to a value of 10% of the value of SIM_TIME. 
* ITERATIONS - The number of indepdendent simulations, by default this is 30. 
* ALPHA - Used to set the confidence interval. By default this is 0.05 corresponding to CIs of 95%.
* Cp - the cost of preemption; i.e. the explicit cost of being interrupted in addition to implict costs incurred due to additional delays.

For the Action Learning script, there are three additional parameters:

* F - the cost to join the primary class
* ROUNDS - the number of rounds in the game; by default this is 10
* EPSILON - a test of whether the costs in each class are sufficently close as to be considered equal due to approximation errors; by default this is 0.00005

For the Var_Latitude script, there are parameters related to latidude and custom service distribution:

* LAT - the latitude of the location being tested, e.g. 42.36 degrees north for Boston, or 19.36 north for Mexico City; LAT determines the first and second moments of interarrival, or the "on time" of the system for customers
* DIST - a parameter controlling the distribution used for testing radiometer service distribution, either Exponential, Gamma, or Log-Log


## Simulators

The simulators function similarly to the simulators for the other cases, however the simulators are based primarily on a M/G/1 queue with breakdowns, which explains certain of the parameter definitions in the code. 

The code itself functions by defining indepdent processes for service, the "provider", and PU and SU user processes. The PU are the incumbents, distributed according to an M/G/1 process - in the case of the trace file scripts, the inputs come from files which populate the IN_ARRIVALS and IN_SERVICE parameters, which are by default expected to be named "interArrival.csv" and "sweepPeriod.csv" contained in the same directory as the script, defining the time to next arrival and the duration of the next sweep period.

Otherwise, each arrival loop processes by taking the next user, sorting into classes as necessary, and processing onto the queue. Incumbents/PU_arrivals are given priority 0, customers/SU_arrivals are given priority 1, with priroity 2 utilized in the Two_customer case for the lowest priority customers. Users are added to the queue, triggering the Provider to wake up if the queue was previously empty. The provider process meanwhile takes the next user off the top in priority sort order and waits the amount of time genererated according to the specified service distribution. Wait time statistics are recoreded upon users exiting. If a preemption occurs, the length the current user has been in service is subtracted from the amount of remaining service time and the user returns to the queue.

In the case of the Action Learning game, the simulations are repeated over multiple rounds; each round the customers' strategy is updated based on which class incurred the lower cost in the previous round, as determined by the mean of the resulting strategy outcomes over each iteration.

## Outputs

The Single-Customer scripts return csv files detailing statistics related to each user type; the default names are specified in line and the files will be generated in the current working directory:

* eess_data.csv - consists of vectors of the statistical system delay data and number of preemptions by the incumbent class (as represented by Earth Exploration Satellite Service, for example) and corresponding error ranges for the condfidence intervals, in the form [Incumbent mean wait, Incumbent mean error Delta, Incumbent mean preemption, Incumbent mean error Delta].
* customer_data.csv - consists of vectors of the stasitical system delay data and number of preemptions by the customer class, and corresponding error ranges for the confidence intervals, in the form [Customer mean wait, Customer mean error Delta, Customer mean preemption, Customer mean error Delta].

The Two_Customer_Base.py and Two_Customer_Traces.py scripts return similar csv files, also specified in line:

* passive_incumbent_data.csv - consists of vectors of the statistical system delay data and number of preemptions by the incumbent class and corresponding error ranges for the condfidence intervals, in the form [Incumbent mean wait, Incumbent mean error Delta, Incumbent mean preemption, Incumbent mean error Delta].
* premium_customer_data.csv - consists of vectors of the stasitical system delay data and number of preemptions by the primary/premium customer class, and corresponding error ranges for the confidence intervals, in the form [Customer mean wait, Customer mean error Delta, Customer mean preemption, Customer mean error Delta].
* standard_customer_data.csv - consists of vectors of the stasitical system delay data and number of preemptions by the secondary/standard customer class, and corresponding error ranges for the confidence intervals, in the form [Customer mean wait, Customer mean error Delta, Customer mean preemption, Customer mean error Delta].

Two_Customer_Traces_Rev_Sw returns csv files tied to revenue and social welfare analysis, specified in line:

* revenue_data.csv - consists of vectors of the statistical mean revenue generated and corresponding errors, in the form [Mean revenue, Revenue error Delta]. 
* social_data.csv - consists of vectors of the statistical mean social welfare corresponding to the specified parameters, in the form [Mean Social Welfare, Social Welfare error Delta].

Two_Customer_Traces_Action_Learning.py returns a csv file specified in the resultout variable prior to the simulation loop, by default this is the following file written to the current working directory

* results.csv - vectors of the customers' chosen strategy and the corresponding error from the simulations undertaken in each round in the form [PHI, PHI error delta].