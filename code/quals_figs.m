%% Threshold 
clear all;
close all;
clc;
% Set parameters
A_pulse_vec = [.5, 1];
sigma_pulse = 200e-12;
mu_pulse    = 1e-9; % center of pulse
tper        = 10e-9;
N_pulse     = .3;
tpulse      = 10e-9;
td          = 1e-9;
v_threshold = .4;

% Setting up timing
dt          = td/100;
t0          = [0 : dt : N_pulse*tper];
t           = [0 : dt : N_pulse*tper+dt]; % Avoid nonzero initial cond.
gaus        = @(x,mu,sig,amp,vo)amp*exp(-(((x-mu).^2)/(2*sig.^2)))+vo;

v_compare   = ones(size(t)) * v_threshold;
t_int_vec   = zeros(size(A_pulse_vec));
% Rf          = 300;
% Cf          = 1e-12;
% H_preamp    = tf([Rf], [Rf*Cf 1]);
figure('Position', [10, 10, 800, 600]);
plot(t, v_compare, '--');
hold on;

for i = 1:numel(A_pulse_vec)
    % Setting up input pulse
    A_pulse = A_pulse_vec(i);
%     sr_rise = A_pulse / td;
%     sr_fall = -A_pulse / td;
%     i_in0   = A_pulse * (1 + square(2*pi/tper*t0, tpulse/tper*100)) / 2;
    i_in0   = gaus(t0, mu_pulse, sigma_pulse, A_pulse, 0); % gaussmf(t0, [sigma_pulse, [sigma_pulse, mu_pulse]]);
    i_in    = [0 i_in0];
%     v_in    = lsim(H_preamp, i_in, t);
    v_in    = i_in;

    % Using the model
    mdl = 'toy_shape_threshold';
    simOut  = sim(mdl, ...
                  'StartTime', sprintf('%g', min(t)), ...
                  'StopTime', sprintf('%g', max(t)), ...
                  'FixedStep', sprintf('%g', dt), ...
                  'SaveTime', 'on', ...
                  'Solver', 'FixedStepDiscrete', ...
                  'LoadExternalInput', 'on', ...
                  'ExternalInput', '[t'', v_in'']');

    y_out       = simOut.get('yout');
    t_out       = simOut.get('tout');
    d_out       = y_out.get(1).Values.Data;
    v_compIn    = y_out.get(2).Values.Data;
    v_compInN   = y_out.get(3).Values.Data;
    v_compInP   = y_out.get(4).Values.Data;

    % Plotting
    plot(t, v_compInN, 'LineWidth', 2);
    hold on;
    
    % Intersection
    [x_int, y_int]  = intersections(t, v_compare, t, v_compInN);
    t_int_vec(i)    = x_int(1);
%     xline(t_int_vec(i), '--', 'LineWidth', 2);
    
    % Labels
    xlabel('Time (s)', 'FontSize', 16);
    ylabel('Signal', 'FontSize', 16);
    set(gca, 'FontSize', 16)
end

xlim([min(t), max(t)]);
ylim([0, max(A_pulse_vec)*1.01]);
% x_annotate = [min(t_int_vec), max(t_int_vec)]/max(t);
% y_annotate = [v_threshold, v_threshold]/max(A_pulse_vec);

% annArrow = annotation('arrow');
% anArrow.Parent = gca;  % or any other existing axes or figure
% anArrow.Position = [min(t_int_vec), v_threshold, range(t_int_vec), 0] ;
% text(x_int, y_int, sprintf('t=%0-#1.2f ns',x_int));

%% CFD
clear all;
clc;
% Set parameters
A_pulse_vec = [.5, 1];
sigma_pulse = 200e-12;
mu_pulse    = 1e-9; % center of pulse
tper        = 10e-9;
N_pulse     = .3;
tpulse      = 10e-9;
td          = 1e-9;
frac        = 0.5;

% Setting up timing
dt          = td/100;
t0          = [0 : dt : N_pulse*tper];
t           = [0 : dt : N_pulse*tper+dt]; % Avoid nonzero initial cond.
gaus        = @(x,mu,sig,amp,vo)amp*exp(-(((x-mu).^2)/(2*sig.^2)))+vo;

t_int_vec   = zeros(size(A_pulse_vec));
% Rf          = 300;
% Cf          = 1e-12;
% H_preamp    = tf([Rf], [Rf*Cf 1]);

figure('Position', [10, 10, 800, 600]);

for i = 1:numel(A_pulse_vec)
    % Setting up input pulse
    A_pulse = A_pulse_vec(i);
    v_threshold = frac*A_pulse;
    v_compare = ones(size(t))*v_threshold;
%     sr_rise = A_pulse / td;
%     sr_fall = -A_pulse / td;
%     i_in0   = A_pulse * (1 + square(2*pi/tper*t0, tpulse/tper*100)) / 2;
    i_in0   = gaus(t0, mu_pulse, sigma_pulse, A_pulse, 0); % gaussmf(t0, [sigma_pulse, [sigma_pulse, mu_pulse]]);
    i_in    = [0 i_in0];
%     v_in    = lsim(H_preamp, i_in, t);
    v_in    = i_in;

    % Using the model
    mdl = 'toy_shape_threshold';
    simOut  = sim(mdl, ...
                  'StartTime', sprintf('%g', min(t)), ...
                  'StopTime', sprintf('%g', max(t)), ...
                  'FixedStep', sprintf('%g', dt), ...
                  'SaveTime', 'on', ...
                  'Solver', 'FixedStepDiscrete', ...
                  'LoadExternalInput', 'on', ...
                  'ExternalInput', '[t'', v_in'']');

    y_out       = simOut.get('yout');
    t_out       = simOut.get('tout');
    d_out       = y_out.get(1).Values.Data;
    v_compIn    = y_out.get(2).Values.Data;
    v_compInN   = y_out.get(3).Values.Data;
    v_compInP   = y_out.get(4).Values.Data;

    % Plotting
    plot(t, v_compInN, 'LineWidth', 2);
    hold on;
    plot(t, v_compare, '--');
    
    % Intersection
    [x_int, y_int]  = intersections(t, v_compare, t, v_compInN);
    t_int_vec(i)    = x_int(1);
%     xline(t_int_vec(i), '--', 'LineWidth', 2);
    
    % Labels
    xlabel('Time (s)', 'FontSize', 16);
    ylabel('Signal', 'FontSize', 16);
    set(gca, 'FontSize', 16)
end

xlim([min(t), max(t)]);
ylim([0, max(A_pulse_vec)*1.01]);

%%
tdelay  = 1.5e-9;
n       = 2;
w0 = 1/tdelay;

[b, a] = besself(n, w0);
sys = tf(b,a);
fb = bandwidth(sys);

freqs(b,a);

[h,w] = freqs(b,a,1000);
grpdel = diff(unwrap(angle(h)))./diff(w);

clf
semilogx(w(2:end),grpdel)
xlabel('Frequency (rad/s)')
ylabel('Group delay (s)')