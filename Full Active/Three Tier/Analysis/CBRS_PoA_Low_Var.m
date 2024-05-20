% Evaluation of PoA for Kc < 2

KI = 1;
Kc = 1;
MUc = 1;
MUI = 1;
RHOI = 0.1; % Incumbent traffic load
RHOc = .001:.001:.999-RHOI; % traffic load

hold on
% evaluate PoA limit expression
%%%
%if RHOI == 0
%    A = (2-2.*(1-RHOc).^(3/2)-3.*RHOc)./(RHOc.^2)+2;
%else
%    A = (2.*RHOc.^2.*(1-RHOI)+2.*(1-RHOI).*(1-RHOI-sqrt((1-RHOI).*(1-(RHOc+RHOI))))-RHOc.*(3-2.*sqrt((1-RHOI).*(1-(RHOc+RHOI)))-RHOI.*(5-2.*RHOI)))./(RHOc.*(2.*(1-RHOI).*RHOI+RHOc.*(1-2*RHOI)));
%end

A = (KI.*RHOI)./(MUI.*(1-RHOI).*(1-(RHOc + RHOI)));
A = A - (1./MUc).*(2 - (4-2.*Kc)./RHOc - Kc./(1-(RHOc+RHOI))+(4.*(1-(RHOc+RHOI)))./(RHOc.*sqrt((1-RHOI).*(1-(RHOc+RHOI))))-(2.*Kc.*sqrt((1-RHOI).*(1-(RHOc+RHOI))))./(RHOc-RHOc*RHOI));
A = (MUc.*MUI.*(1-RHOI).*(1-(RHOc+RHOI))).*A;
A = A./(Kc.*MUI.*RHOc+KI.*MUc.*RHOI+2.*MUI.*RHOI.*(1-(RHOc + RHOI)));


plot(RHOc,A,'-.m')

