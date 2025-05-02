# spectrum-sharing-simulations

Simulations for Priority Purchasing Queuing Games modeling scenarios corresponding to coexistence scenarios between different tiers of users in Dynamic Spectrum Access scenarios, under the Open Access Spectrum framework with highest priority public interest incumbents.

Within the realm of the wireless spectrum space, much of the available useful spectrum has been previously allocated to various incumbents, complicaiting efforts to expand services. On top of this, services tend to receive over production from interference by virtue of channel assignemnts which do not take into account spatio-temporal occupancy rates. Thus, ongoing efforts are underway to evaluate the most effective means to share spectrum. One of the key questions is however how should commerical providers value access, particuarly if the Open Access framework is implemented and the fee is tied directly to occupancy.

A related question is one of how the provider/spectrum manager should implement the sharing framework given concerns over whether access should be granted to those willing to pay vs. allowing liscence-by-rule access with limited rights to prevent service gaps, and how various forms of state aid required to acheive desired utilization rates impact decision making.

The markets in question are those of wholesale industrial users (cellualr providers, smart city scale edge compute networks, etc.) rather than individual clients; thus we consider a mix of Non Preemptive and Preemptive resume based models for inter-customer interactions. We also do not consider a loss model within this specific setting as we are not concerned with the level of indvidual requests, although this is something to consider for work building off of this code base given the nature of the system model.

At the highest level, the purchasing game is modeled as a multi-tier M/G/1 (Poisson arrival, General Service, Single server) FIFO queue, where customers make their decision on whether to purchase upon entry. Such purchase decision is irrevocable, and cusotmers do not balk once joining (customers are assumed to not balk at all unless explicitly offered that as an option; it is implicitly assumed that customers otherwise balking simply do not approach the queue in the other scenarios as it is determined that service is required and therefore balking results in negative utility outweighting expected utility of joining either queuing class.) The version for the CBRS-type case with two customer tiers and the incumbent is diagrammed below<sup>[1]</sup>:

![An example of the queuing model with two customer tiers plus the incumbent.](/queue_model.png?raw=true "CBRS-type Model")



The models considered are a:
    - "Active-Passive Coexistence" model based on sharing between one or more customer classes and a higher tier incumbent based on the Earth Exploration Satellite Service-passive radiometers.
    - "Full Active Coexistence" model based on sharing between two customer classes and a highest tier incumbent, as in the Citiens Broadband Radio Service (CBRS) 
    - "Two Class" model based on sharing between two customer classes and no incumbents present. 

For additional reading on the finer details of the specfici underlying models, we direct you to the respetive references in the Lisence section.

[1] Chamberlain, Jonathan. *Economic Frameworks for Coexistence in Advanced Wireless Networks* p. 126. PhD Disseration, 2025.

--------------

# Usage

The simulation code consists of various scripts corresponding to various scenarios within the realm of spectrum sharing and co-existence. 

- Active-Passive-Coexstience contains the scripts corresponding to the EESS-passive sharing based models
- CBRS-Coexistence contains the scripts corresponding to the CBRS-like sharing based models
- No-Incumbent contains the scripts corresponding to the models with two customer classes without incumbents.

To run the No-Incumbent, Active-Passive, or CBRS-Coexistence/Learning simulations, the desired script can be run directly from the command line, with the inputs edited directly from file.

For the CBRS-Coexistence/Queuing-Delay simuatons, these are intended to be run using the wrapper functions, and thus the respective wrappers should be called form the command line, with inputs changed in the wrapper file; any global simulation parameters are still edited within the respective Sim file.

For implementation details on the specific scenarios, consult the README files within the respective folders.

## Dependencies

The main simulation utilizes Python code, specifically [SimPy](https://simpy.readthedocs.io/en/latest/contents.html)

The code was originally written in Python 3 using SimPy version 3. 

To utilize the code, in addition to SimPy, it is also necessary to install NumPy and SciPy for statistical analysis. These can be installed using pip:

```
pip install numpy
pip install scipy
pip install simpy
```

The code also used an earlier version of NumPy which utilizes an alternate syntax for the random number generation routine, and may require updates to function correctly.

For visualizations, [Matplotlib](https://matplotlib.org/) is utilized. The code was originally written in version 3.1. 

If necessary to install, Matplotlib can be installed via pip, or conda for users utilizing that method:

'''
python -m pip install -U pip
conda install matplotlib
'''

Any relevant matplotlib dependencies are automatically installed. Alternatively, the simualtor output as described below are CSV files which can be imported into elsewhere, e.g. MATLAB for visualization/analysis if one so chooses.


## Simulators

The functionality at a high level is similar to that of the [advance-reseravation-simulation](https://github.com/nislab/advance-reservation-simulation) project: using SimPy, streams of customers are created and then split into primary and secondary (also known as priority and general access) customer groups, or alternatively into groups of joining versus balking customers, based on a threshold equilibrium PHI. When incumbents are present, an independent stream of users are created with an alternative higher priority which always preemptions customers. Customers may or may not be able to preempt each other depending on the specifics of the scenario. The specific implementation details are left to the subfolders as while each are similar in nature, differences in implementation result in differing inputs and formatting of the outputs.

------------------------

# License


These materials may be freely used and distributed, provided that attribution to this original source is acknowledged. If you reuse the code in this repository, we kindly ask that you refer to the relevant work (cf. the included bib files in the citation directory of this repository):

* Active-Passive-Coexistence/Single-Customer:

Chamberlain, Jonathan, Joel T. Johnson, and David Starobinski. "Spectrum Sharing between Earth Exploration Satellite and Commercial Services: An Economic Feasibility Analysis." 2024 IEEE International Symposium on Dynamic Spectrum Access Networks (DySPAN). IEEE, 2024.

* Active-Passive-Coexistence/Two-Customer:

Chamberlain, Jonathan, David Starobinski, and Joel T. Johnson. "Facilitating Spectrum Sharing with Passive Satellite Incumbents." IEEE Journal on Selected Areas in Communications (2024).

* CBRS-Coexistence:

Chamberlain, Jonathan, and David Starobinski. "Game Theoretic Analysis of Citizens Broadband Radio Service." 2022 20th International Symposium on Modeling and Optimization in Mobile, Ad hoc, and Wireless Networks (WiOpt). IEEE, 2022.

* No-Incumbent:

Chamberlain, Jonathan, and David Starobinski. "Strategic Revenue Management of Preemptive versus Non-Preemptive Queues". Operations Research Letters, 2021.

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