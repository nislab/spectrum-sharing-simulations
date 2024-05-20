% Input to CBRS Formulas

phi = 0:.001:1;

% Customer statistics
lam = 0.0627845; % rho = 0.1
% lam = 0.125569; % rho = 0.2
% lam = 0.1883535; % rho = 0.3
% lam = 0.251138; % rho = 0.4
% lam = 0.502276; % rho = 0.8
mu = 0.627845;
rho = lam/mu; 

K = 1.30018; 
% K = 3.90054;

% Incumbent statistics
lami = 0.00163492; % rhoi = 0.05
% lami = 0.00326984; % rhoi = 0.1
% lami = 0.00938444; % rhoi = 0.15
mui = 0.0326984;
rhoi = lami/mui;
Ki = 1.85499;

% Cost of preemption
% V = 0;
V = 1.15;
% V = 1.25;
% V = 1.5;

% Formula shorthand
alpha = 1 - rhoi;
beta = 1 - (rhoi+rho*phi);
gamma = 1 - (rhoi+rho);

% Cost
C = (rho.*(Ki.*mu.*rhoi+2.*mui.*phi.*gamma+K.*mui.*(alpha-phi.*gamma)))./(2.*mu.*mui.*alpha.*beta.*gamma) + V.*rho.*phi;