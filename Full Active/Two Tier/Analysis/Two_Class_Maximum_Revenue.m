RHO = .70:.01:.90; %traffic load
K = 4; % Service variance, defined in terms of second moment
RNP = zeros(1,21); % max revenue under NP
RPR = zeros(1,21); % max revenue under PR

% compute revenues
for i = 1:21
    rho = RHO(i);
    % computing RNP - always monotone function
    RNP(i) = (K*rho^3)/(2*(1-rho));
    % computing RPR, depends whether function is monotone or unimodal
    if K > 4 && rho < (3/2)-(1/2)*sqrt(((5*k-2)/(k-2)))
        % R_PR unimodal
        RPR(i) = ((2*(K-2)-rho*(3*K-4))/(2*(1-rho))) - (K-2)*sqrt((K-2-2*rho*(K-1))/((K-2)*(1-rho)));
    else
        % R_PR monotone
        RPR(i) = (K*rho^2+(2-K)*rho^2*(1-rho))/(2*(1-rho)^2);
    end
end
