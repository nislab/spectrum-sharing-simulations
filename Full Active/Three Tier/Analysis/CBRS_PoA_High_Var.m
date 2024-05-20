% Evaluation of PoA for Kc > 2

KI = 1;
Kc = 3;
MUI = 1;
MUc = 1;
RHOI = 0.3; % Incumbent traffic load
RHOc = .001:.001:.999-RHOI; % traffic load

hold on
% evaluate PoA limit expression
%if RHOI == 0
%    A = RHOc.^2./(RHOc.*(3-2.*sqrt(1-RHOc))-2.*(1-sqrt(1-RHOc)));
%else
%    A = RHOc.^2./(RHOc.*(3-3.*RHOI-2.*sqrt((1-RHOI).*(1-(RHOc+RHOI))))-2.*(1-RHOI).*(1-RHOI-sqrt((1-RHOI).*(1-(RHOc+RHOI)))));
%end

A = (KI.*RHOI)./(MUI.*(1-RHOI).*(1-(RHOc + RHOI)));
A = A - (1./MUc).*(2 - (4-2.*Kc)./RHOc - Kc./(1-(RHOc+RHOI))+(4.*(1-(RHOc+RHOI)))./(RHOc.*sqrt((1-RHOI).*(1-(RHOc+RHOI))))-(2.*Kc.*sqrt((1-RHOI).*(1-(RHOc+RHOI))))./(RHOc-RHOc*RHOI));
A = (MUc.*MUI.*(1-RHOI).*(1-(RHOc+RHOI))).*A;
A = (Kc*MUI*RHOc+KI*MUc*RHOI+2*MUI*RHOI*(1-(RHOc+RHOI)))./A;


plot(RHOc,A,'-.m')


