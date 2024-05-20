% Plot Revenues in M/G/1-PR queue for varying levels of Incumbant Class
% service

% customer statistics (letting muc = 1)
rhoc = 0.2; % traffic load
Kc = 10; % service distribution; 1 = deterministic, 2 = exponential
% incumbent statistics (letting muI = 1)
rhoI = 0.3; % traffic load
KI = 1; % service distribution; 1 = deterministic, 2 = exponential

phi = 0:.001:1;

if rhoI == 0
    R = (Kc.*rhoc.^2.*phi+(2-Kc).*phi.^2.*rhoc.^2.*(1-rhoc))./(2.*(1-rhoc).*(1-phi.*rhoc)); % two class case
else
    R = (rhoc.^2.*phi.*(KI.*rhoI+(Kc.*(phi.*rhoc+(1-phi).*(1-rhoI))+2.*phi.*(1-(rhoc+rhoI)))))./(2.*(1-rhoI).*(1-(rhoc+rhoI)).*(1-(phi.*rhoc+rhoI)));
end

hold on % plot all on same chart
plot(phi,R,'-.m')

