% Simulate stategic learning by updating each epoch based
% on the current statistics of the system and resulting moves by each
% player

% CBRS Equilibria - static queue statistics and provider cost, used to
% validate claims of equilibria stability

EPOCHS = 20; % Number of epochs to run game over
PHI = zeros(EPOCHS,1); % Create array corresponding to PHI beliefs
ALPHA = 0.05; % fraction to vary phi by when updating
phi = 0.5; % Initial belief of customers
for i=1:EPOCHS
    PHI(i) = phi; % store current belief
    C = 0.16753; % cost of purchasing priority
    % customer statistics
    lam = 0.1; % arrival rate
    mu = 1; % service rate
    rho = lam/mu; % traffic rate
    K = 3; % service variance
    % incumbent statistics
    lami = 0.5; % arrival rate
    mui = 10; % service rate
    rhoi = lami/mui; % traffic rate
    Ki = 2; % service variance 
    % Compute expected wait times given statistics, values of phi and C
    P = 1/(mu*(1-rhoi))+(Ki*rhoi/mui+K*rho*phi/mu)/(2*(1-rhoi)*(1-(rhoi+rho*phi))) % Priority Customers
    G = 1/(mu*(1-(rhoi+phi*rho)))+(Ki*rhoi/mui+K*rho/mu)/(2*(1-(rhoi+rho*phi))*(1-(rhoi+rho))) % General Customers
    % update phi, if necessary
    if P+C < G
        phi = phi+ALPHA*(1-phi); % Priority better off, increase fraction of priority customers
    elseif G < P+C
        phi = phi-ALPHA*phi; % General better off, decrease fraction of priority customers
    end
end