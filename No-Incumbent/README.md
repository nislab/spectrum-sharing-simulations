# Usage

To run the simulators in this folder, simply run the scripts directly on the command line. The scripts are named for the corresponding M/G/1 scenario:

Non-Preemptive for the queue without preemptions, thus lower priority customers are not preempted even if higher priority customers arrive
Preemptive-Resume for the queue with preemptions, where lower priority customers resume service from the point of interruption



## Inputs

The Inputs and Parameters are contained within the top of the files, and are updated via simply editing the scripts:

* LAM - the customer arrival rate lambda, LAM > 0 is required. LAM can accept a vector of multiple values, which the simulator will loop over to produce results for each specified arrival rate; NUMLAM checks for the length of the vector to determine the number of loops required.
* MU - the customer service rate mu, 0 < LAM < MU is required for a stable system; currently the default value is 1 (i.e. service is normalized)
* PHI - the fraction of customers joining the primary service class, this must be a fraction in [0,1].
* K - a parameter tied to the service variance, K is specifically defined in terms of the second moment of the service distribution, such that the second moment is K/MU^2. Thus, K >= 1 follows. 

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

The remaining parameters are:
* FRAC - The fraction of time elapsed before statistics are collected, to allow the system to reach steady state conditions. By default this is set to 0.1 so that the related variable t_start within the simulator loop is set to a value of 10% of the value of the simulation time. 
* ITERATIONS - The number of indepdendent simulations, by default this should be 30. 
* ALPHA - Used to set the confidence interval. By default this is 0.05 corresponding to CIs of 95%.


## Simulators

The Simulators run over a number of loops, based on the number of ITERATIONS, for each value of LAM specified, and compute the wait time statistics for each class of user.

The code *technically* has the capacity to simulate multi-server conditions by updating the processor variable to a capacity of greater than 1. However, this has been observed to have mixed results in SimPy 3 even for scenarios where analysis should be tractible. This is potentially related to bugged code regarding priority sort order which has not been re-tested in SimPy 4.

The sim_time variable in the main loop controls the length of time to run the simulation over; by default a sliding scale to generate 500,000 samples, based on the arrival rate LAM, is utilized.

Within the server environment, there are two independent streams, those of customer arrivals and the provider/server. Arrivals are generated based on exponential delay, and then are compared against the threshold PHI according to a uniform RNG. Based on this comparison, they are sorted into the primary or secondary class, with class 0 being the higher priority and customers joining this class when the RNG returns a result less than PHI. The total serv_time for the customer is generated according to the service distribution and is passed as one of the customer's attributes when they join the queue. If the queue was previously empty, a trigger is sent to wake up the provider process.

In the provider stream, the provider takes the next customer off the queue in priority sort order, and waits for the duration of the customer's specified service length. Upon service completion, the wait time statistics are recorded and the customer exits. In the Preemptive Resume case, if a higher priroity customer enters the queue while a lower priority customer is in service, the process is interrupted, the lower priority cusotmer is sent back to the queue, with the time in service recorded, and the higher priority customer replacing them in service.

At the end of the interation, the mean wait times for each class of users are computed.

## Outputs

Following the end of the simulations, the sample wait and error and computed per class for each specified value of lambda and printed to screen, with corresponding plots generated using matplotlib - the plots are not automatically saved to file.