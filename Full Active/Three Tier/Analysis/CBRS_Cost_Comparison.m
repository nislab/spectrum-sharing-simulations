% Plot costs in M/G/1-PR queue for varying levels of Incumbant Class
% service

% customer statistics (letting muc = 1)
rhoc = 0.235; % traffic load
Kc = 3; % service distribution; 1 = deterministic, 2 = exponential
muc = 1; % service rate
% incumbent statistics (letting muI = 1)
rhoI = 0.1 ; % traffic load
KI = 1; % service distribution; 1 = deterministic, 2 = exponential
muI = 2; % service rate

phi = 0:.001:1;

if rhoI == 0
    C = (Kc.*rhoc+(2-Kc).*phi.*rhoc.*(1-rhoc))./(2.*(1-rhoc).*(1-phi.*rhoc)); % two class case
else
    C = rhoc.*(KI.*muc.*rhoI+2.*muI.*phi.*(1-rhoc-rhoI)+Kc.*muI.*(1-rhoI-phi.*(1-rhoc-rhoI)))./(2.*muI.*muc.*(1-rhoI).*(1-(rhoc+rhoI)).*(1-(phi.*rhoc+rhoI)));
end

hold on % plot all on same chart
plot(phi,C,'--r')



