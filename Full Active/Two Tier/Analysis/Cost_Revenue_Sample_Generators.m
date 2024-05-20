% Input to Two Tier Spectrum Sharing formulas for Cost, Revenue

phi = .001:.001:.999;

% Customer statistics
lam = 0.1;
mu = 1;
rho = lam/mu; 
K = 3.90054;

% Non Preemptive Cost
% C = (K*rho.^2)./(2.*mu.*(1-rho).*(1-rho.*phi));

% Preemptive Resume Cost
C = (K*rho+ (2-K).*(1-rho).*rho.*phi)./(2.*mu.*(1-rho).*(1-rho.*phi));

% Revenue
R = lam.*phi.*C;