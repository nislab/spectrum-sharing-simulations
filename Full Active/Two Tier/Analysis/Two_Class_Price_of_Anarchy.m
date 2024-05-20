K = 1000; % Service variance, defined in terms of second moment
RHO = .001:.001:.999; % traffic load

if K < 2
    A = ((2-K).*(2-2.*(1-RHO).^(3/2)-3.*RHO))./(K*RHO.^2)+2./K;
elseif K == 2
    A = ones(1,999);
else
    A = (K.*RHO.^2)./((2-K).*(2-2.*(1-RHO).^(3/2)-3.*RHO)+2.*RHO.^2);
end

hold on
plot(RHO,A,'g-.')
