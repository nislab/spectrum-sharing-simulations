% Input to CBRS Formulas

phi = .001:.001:.999;

% Customer statistics
lam = 0.0627845; % rho = 0.1
% lam = 0.251138; % rho = 0.4
% lam = 0.502276; % rho = 0.8
mu = 0.627845;
rho = lam/mu; 
% K = 1.30018; 
% K = 3.90054;
K = 5.20072;

% Incumbent statistics
mui = 0.0326984; % fixed
% rhoi = .001:.001:1-rho; % demonstarte how changing rhoi impacts other parameters
Ki = 1.85499; % fixed

% threshold rho for possible non-monotone increasing behavior
syms rhoimax
rhoT = ((K-2).*mui.*(1-rhoimax).^2)./(2.*(K-1).*mui.*(1-rhoimax)+Ki.*mu.*rhoimax) == rho;
S = vpasolve(rhoT,rhoimax,[0 1]);
rhoi = .001:.001:S;  

% Formula shorthand
alpha = 1 - rhoi;
gamma = 1 - (rhoi+rho);

% boundary values for preemption
VpL = (mui.*alpha.*(K.*(gamma-rho)-2.*gamma)-Ki.*mu.*rho.*rhoi)./(2.*mu.*mui.*alpha.^3.*gamma);
VpM = (mui.*alpha.*(K.*(gamma-rho)-2.*gamma)-Ki.*mu.*rho.*rhoi)./(2.*mu.*mui.*alpha.^2.*gamma.^2);
VpH = (mui.*alpha.*(K.*(gamma-rho)-2.*gamma)-Ki.*mu.*rho.*rhoi)./(2.*mu.*mui.*alpha.*gamma.^3);

% boundary value for unimodal R(phi)
VpU = (K.*mui.*(rho.^2-3.*rho.*alpha+alpha.^2)-Ki.*mu.*alpha.*rhoi-2.*mui.*gamma.*(alpha+gamma))./(4.*mu.*mui.*alpha.*gamma.^3);
