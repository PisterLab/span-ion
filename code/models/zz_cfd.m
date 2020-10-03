clear all
close all
clc

N_pulse = 2;        % number of pulses to produce
A_pulse = 100e-6;   % input current pulse max

%% Input current: square wave (for now)
% ---------------------------- START CHANGES ---------------------------- %
t_event = 10e-9;     % pulse period
t_pulse = 1e-9;     % pulse length
% ----------------------------- STOP CHANGES ---------------------------- %
dt      = t_pulse/100;
t0      = [0 : dt : N_pulse*t_event];
f_event = 1/t_event;
i_in0   = A_pulse * (1 + square(2*pi*f_event*t0, t_pulse/t_event*100)) / 2;

% Add time in front to avoid nonzero initial condition
t       = [0 : dt : N_pulse*t_event+dt]; % [t0 max(t0)+dt];
i_in    = [0 i_in0];

%% Preamp
preamp_vars_map = containers.Map();
% ---------------------------- START CHANGES ---------------------------- %
preamp_type = 'RC';

preamp_vars_map('R')    = 'Rf = 800;';
preamp_vars_map('RC')   = 'Rf = 800; Cf = 1e-12;';
preamp_vars_map('C')    = 'Cf = 1e-12;'
% ----------------------------- STOP CHANGES ---------------------------- %
preamp_tf_num_map = containers.Map();
preamp_tf_num_map('R')  = '[Rf]';
preamp_tf_num_map('RC') = '[Rf]';
preamp_tf_num_map('C')  = '[1]';

preamp_tf_den_map = containers.Map();
preamp_tf_den_map('R')  = '[1]';
preamp_tf_den_map('RC') = '[Rf*Cf 1]';
preamp_tf_den_map('C')  = '[Cf 0]';

eval(preamp_vars_map(preamp_type))
H_preamp = tf(eval(preamp_tf_num_map(preamp_type)), eval(preamp_tf_den_map(preamp_type)));

v_in = lsim(H_preamp, i_in, t);

%% CFD
cfd_vars_map = containers.Map();
% ---------------------------- START CHANGES ---------------------------- %
shaper_type = 'delay_atten';

cfd_vars_map('nowlin')      = 'f_attenuation = 0.5;';
cfd_vars_map('threshold')   = 'v_threshold = 0.05;';
cfd_vars_map('diff')        = 'v_threshold = 0.1;';
cfd_vars_map('delay_atten') = 'f_attenuation = 0.5; t_delay = 100e-9;';
% ----------------------------- STOP CHANGES ---------------------------- %
cfd_mdl_map = containers.Map();
cfd_mdl_map('nowlin')       = 'shape_nowlin';
cfd_mdl_map('threshold')    = 'shape_threshold';
cfd_mdl_map('diff')         = 'shape_diff';
cfd_mdl_map('delay_atten')  = 'shape_delay_atten';

cfd_reshape_map = containers.Map();
cfd_reshape_map('nowlin')       = '';
cfd_reshape_map('threshold')    = 'v_compInP=ones(size(t_out))*v_compInP;';
cfd_reshape_map('diff')         = 'v_compInP=ones(size(t_out))*v_compInP;';
cfd_reshape_map('delay_atten')  = '';

mdl = cfd_mdl_map(shaper_type);
eval(cfd_vars_map(shaper_type));

simOut  = sim(mdl, ...
              'StartTime', sprintf('%g', min(t)), ...
              'StopTime', sprintf('%g', max(t)), ...
              'FixedStep', sprintf('%g', dt), ...
              'SaveTime', 'on', ...
              'Solver', 'FixedStepDiscrete', ...
              'LoadExternalInput', 'on', ...
              'ExternalInput', '[t'', v_in]');

y_out       = simOut.get('yout');
t_out       = simOut.get('tout');
d_out       = y_out.get(1).Values.Data;
v_compIn    = y_out.get(2).Values.Data;
v_compInN   = y_out.get(3).Values.Data;
v_compInP   = y_out.get(4).Values.Data;

eval(cfd_reshape_map(shaper_type));
%% All wrapped into a function
preamp_struct = struct('type', 'RC', ...
                       'Rf', 800, ...
                       'Cf', 1e-12);
shaper_struct = struct('type', 'nowlin', ...
                       'f_attenuation', 0.5, ...
                       'v_threshold', 0.05, ...
                       't_delay', 100e-12);
% Simulate the preamp
[t, v_preampOut] = sim_preamp(t, i_in, preamp_struct);

% Simulate the shaper
[t_out, v_compInP, v_compInN, d_out] = sim_shaper(t, shaper_struct);
%% Plot results
num_plt = 4;

idx_plt = 1;
plt_iin = subplot(num_plt, 1, idx_plt);
plot(t, i_in);
ylim(plt_iin, [-max(i_in)*0.01, max(i_in)*1.1]);
xlim(plt_iin, [min(t), max(t)]);
ylabel({'Input', 'Current', '(A)'});
% xlabel('Time (s)')
idx_plt = idx_plt + 1;

plt_vpreampOut = subplot(num_plt, 1, idx_plt);
plot(t, v_preampOut);
ylim(plt_vpreampOut, [-max(v_preampOut)*0.01, max(v_preampOut)*1.1]);
xlim(plt_vpreampOut, [min(t), max(t)]);
ylabel({'Preamp', 'Output', '(V)'});
% xlabel('Time (s)')
idx_plt = idx_plt + 1;

plt_vcompInSplit = subplot(num_plt, 1, idx_plt);
plot(t_out, v_compInP, 'r');
hold on;
plot(t_out, v_compInN, 'b');
ylim(plt_vcompInSplit, [min([v_compInN; v_compInP]), ...
                        max([v_compInN; v_compInP])*1.1]);
xlim(plt_vcompInSplit, [min(t_out), max(t_out)]);
ylabel({'Comparator', 'Inputs', '(V)'});
% xlabel('Time (s)')
idx_plt = idx_plt + 1;

plt_dout = subplot(num_plt, 1, idx_plt);
plot(t_out, d_out);
ylim(plt_dout, [-max(d_out)*0.01, max(d_out)*1.1]);
xlim(plt_dout, [min(t_out), max(t_out)]);
ylabel({'Comparator', 'Output'});
% xlabel('Time (s)')
idx_plt = idx_plt + 1;