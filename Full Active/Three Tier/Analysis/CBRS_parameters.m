% Input to CBRS Formulas

phi = .001:.001:.999;

% Customer statistics
lam = 0.0627845;
% lam = 0.251138;
% lam = 0.502276;
mu = 0.627845;
rho = lam/mu; 
P = 1.25; % Price of Preemption

% K = 1.30018;
% K = 2.60036; 
K = 3.90054;

% Incumbent statistics
lami = 0.00163492;
% lami = 0.00326984;
% lami = 0.00938444;
mui = 0.0326984;
rhoi = lami/mui;
Ki = 1.85499;

% Formula shorthand
alpha = 1 - rhoi;
beta = 1 - (rhoi+rho.*phi);
gamma = 1 - (rhoi+rho);


% Cost
C = (rho.*(Ki.*mu.*rhoi+2.*mui.*phi.*gamma+K.*mui.*(alpha-phi.*gamma)))./(2.*mu.*mui.*alpha.*beta.*gamma) + P.*phi.*rho;
