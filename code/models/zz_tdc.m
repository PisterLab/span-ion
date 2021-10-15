clear all
close all
clc

%%
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% General purpose inputs that may or may not get used depending on the
% model
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% ---------------------------- START CHANGES ---------------------------- %
vdd             = 1.8;
vmid_digital    = vdd/2;
% ----------------------------- STOP CHANGES ---------------------------- %
%%
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% Initial input pulses (after 1-shot pulse generator)
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% ---------------------------- START CHANGES ---------------------------- %
tstart      = 10e-9; % s, rising edge of START pulse
tstop       = tstart + 50e-9; % s, rising edge of STOP pulse
tconvert    = 20e-9; % s, time required for ADC to convert

toneshot_start  = 25e-9; % s, length of START 1shot pulse
toneshot_stop   = 25e-9; % s, length of STOP 1shot pulse
tpulse_rst      = 20e-9; % s, length of reset pulse for integrator

dt  = .1e-9;
t   = 0:dt:100e-9;
% ----------------------------- STOP CHANGES ---------------------------- %
pulse_start = zeros(size(t));
pulse_stop  = zeros(size(t));
reset_int   = zeros(size(t));
trst        = tstop + tconvert;

for i = 1:numel(t)
    if t(i) > tstart && t(i) < tstart+toneshot_start
        pulse_start(i) = vdd;
    end
    if t(i) > tstop && t(i) < tstop+toneshot_stop
        pulse_stop(i) = vdd;
    end
    if t(i) > trst && t(i) < trst + tpulse_rst
        reset_int(i) = vdd;
    end
end

% % plotting
% hold on;
% plot(t, pulse_start, 'DisplayName', 'START Pulse');
% plot(t, pulse_stop, 'DisplayName', 'STOP Pulse');
% legend
%% 
mdl = 'tdc_analog';
gain_int = 1;

simOut = sim(mdl, ...
            'StartTime', sprintf('%g', min(t)), ...
            'StopTime', sprintf('%g', max(t)), ...
            'LoadExternalInput', 'on', ...
            'ExternalInput', '[t'', reset_int'', pulse_start'', pulse_stop'']');
        
y_out = simOut.get('yout');
t_out = simOut.get('tout');

v_TAC = y_out.get(1).Values.Data;
v_ramp = y_out.get(2).Values.Data;

subplot(3,1,1);
hold on;
plot(t, pulse_start, 'DisplayName', 'START Pulse');
plot(t, pulse_stop, 'DisplayName', 'STOP Pulse');
legend;

subplot(3,1,2);
plot(t, reset_int, 'DisplayName', 'Reset');

subplot(3,1,3);
plot(t_out, v_TAC, 'DisplayName', 'S/H Ramp');
hold on;
plot(t_out, v_ramp, 'DisplayName', 'Ramp');
ylabel('TAC Output Voltage [V]');
xlabel('Time [s]');
legend;