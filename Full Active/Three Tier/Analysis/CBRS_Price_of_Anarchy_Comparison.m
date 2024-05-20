% Incumbent parameters
KI = 1; % Service variance, defined in terms of second moment
RHOI = .01; % traffic load
MUI = 100; % service rate
% Customer parameters
Kc = 10; % Service variance, defined in terms of second moment
RHOc = .001:.001:1-RHOI; % traffic load
MUc = 1; % Service rate


S0 = (Kc.*MUI.*RHOc.*(1-RHOI)+KI.*MUc.*(1-RHOI).*RHOI+2.*MUI.*(1-RHOI).*RHOI*(1.-(RHOc+RHOI)))./(2.*MUc.*MUI.*(1-RHOI).^2.*(1-(RHOc+RHOI))); % Welfare when phi=0
SDS = (1/2).*(KI.*RHOI./(MUI.*(1-RHOI).*(1-(RHOc+RHOI)))+(1/MUc).*(-2+(4-2.*Kc)./RHOc+Kc./(1-(RHOc+RHOI))-(4.*(1-(RHOc+RHOI)))./(RHOc.*sqrt((1-RHOI).*(1-(RHOc+RHOI))))+(2.*Kc.*sqrt((1-RHOI).*(1-(RHOc+RHOI))))./(RHOc.*(1-RHOI)))); % Welfare when phi = phi**

% evaluate ratio
if Kc < 2
    A = SDS./S0;
else
    A = S0./SDS;
end

plot(RHOc,A)

