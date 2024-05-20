K = 1; % Service variance, defined in terms of second moment
RHO = .001:.001:.999; % traffic load
SMAX = zeros(1,999); % Welfare under revenue maximizing provider
SOPT = zeros(1,999); % Welfare under social optimal state

for i=1:999
    rho = RHO(i); % current value of rho
    % evaluate variance, traffic load to determine if revenue function is
    % unimodal or monotone
    if K > 4 && rho < (3/2)-(1/2)*((5*K-2)/(K-2))^(1/2)
        phi_max = (1/rho)-((K-2-2*(K-1)*rho)/((K-2)*(1-rho)*rho^2))^(1/2);
    else
        phi_max = 1;
    end
    % determine corresponding social welfare
    SMAX(i) = (rho*(K-2*phi_max*rho+(2-K)*phi_max*(1-phi_max*(1-rho))))/(2*(1-rho)*(1-phi_max*rho));
    % determine socially optimal condition
    phi_opt = (1-(1-rho)^(1/2))/rho;  
    SOPT(i) = (rho*(K-2*phi_opt*rho+(2-K)*phi_opt*(1-phi_opt*(1-rho))))/(2*(1-rho)*(1-phi_opt*rho));
end

% evaluate ratio of SMAX to SOPT
A = SMAX./SOPT;

