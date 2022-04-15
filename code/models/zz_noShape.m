clear all;
close all;
clc;

% ---------------------------- START CHANGES ---------------------------- %
t_delay     = 13.37e-9;             % Coax cable/delay line delay (s)
f_atten     = 0.1;                  % Attenuator reduction (V/V)
t_rise      = 100e-12;              % Input pulse rise time
v_threshold = (1.8/(2^9)) * 71;     % Leading edge detector DAC voltage
v_high      = 0.9;                  % Voltage which constitutes digital high
voff_led    = 0.0;                  % LED comparator input-referred offset (+)
voff_zcd    = 0.0;                  % ZCD comparator input-referred offset (+)
tau         = 50e-9;                % First pass estimate of a single amp's tau
mdl         = 'shape_delay_atten_noComp';

A_in_vec    = [0.75, 0.8, 0.8500000000000001, 0.9000000000000001, 0.9500000000000002, 1.0000000000000002, 1.0500000000000003, 1.1000000000000003, 1.1500000000000004, 1.2000000000000004, 1.2500000000000004, 1.3000000000000005];
tcross_raw_vec = [1.0538198327923982e-07, 1.049211319631543e-07, 1.0435747467409628e-07, 1.0418152244161038e-07, 1.039207284188152e-07, 1.0353367183931971e-07, 1.0318523802927354e-07, 1.0285229409599763e-07, 1.0272498529736095e-07, 1.0242971712898494e-07, 1.0219647702023626e-07, 1.0197615416890798e-07];
tcross_real_vec = tcross_raw_vec - 85e-9; % Correcting DG535 delay

num_plots = 4;

A0_stage = 2;           % Gain of a single amp stage
num_LED = 6;
num_ZCD = 5;
error_tol = 1e-12;

pth_data = 'C:/Users/lydialee/Box Sync/Research/SSL/span-ion/data/testing/noShape'; % Data directory path
timestamp = datestr(now, 'yyyymmdd_HHMMSS');
fname = strcat(timestamp, '_zcdSmall_timeConsts.yaml'); % Output file name
% ----------------------------- STOP CHANGES ---------------------------- %

dt = t_rise/100;

% Values to populate in simulation
tau_vec = zeros(size(A_in_vec));
tcross_sim_vec = zeros(size(A_in_vec));

plt_zcdIn = subplot(num_plots, 1, 1);
plt_ledIn = subplot(num_plots, 1, 2);
plt_vLED = subplot(num_plots, 1, 3);
plt_vZCD = subplot(num_plots, 1, 4);

for i = 1:numel(A_in_vec)
    % Empty plots 
    cla(plt_zcdIn);
    cla(plt_ledIn);

    A_in = A_in_vec(i);
    fprintf('\nA_in = %e V', A_in);
    tcross_real = tcross_real_vec(i);
    
    % Initial input pulse
    tflip_cfd_max = t_delay + max(A_in_vec)*f_atten/(max(A_in_vec)/t_rise);
    tflip_led_max = v_threshold/(max(A_in_vec)/t_rise);
    t_vec = transpose(0:dt:max([tflip_cfd_max, tflip_led_max])*1.5);

    tflip_led = v_threshold/(A_in/t_rise);
    tflip_cfd = t_delay + A_in*f_atten/(A_in/t_rise);
    
    vin = A_in/t_rise * t_vec;
    vin(vin>A_in) = A_in;
    
    % Begin with starting guess of time constant
    val_low = 0;
    val_high = tau * 2;

    is_increasing = true;
    done = false;
    
    t_transp = t_out';
    v_high_vec = ones(size(t_transp))*v_high;

    while ~done
        % Printing for sanity checking
        fprintf('\n\t%e -> %e -> %e', val_low, tau, val_high);

        % Estimate the comparators' transfer functions
        omega0 = -2*pi/tau; % Mind the sign!
        [b_LED, a_LED] = zp2tf([], ones(num_LED,1)*omega0, 1);
        [b_ZCD, a_ZCD] = zp2tf([], ones(num_ZCD,1)*omega0, 1);

        scale_LED = a_LED(numel(a_LED)) * A0_stage^num_LED;
        scale_ZCD = a_ZCD(numel(a_ZCD)) * A0_stage^num_ZCD;

        % Pass through Simulink model of DG535 + coax
        simOut = sim(mdl, ...
                'StartTime', sprintf('%g', min(t_vec)), ...
                'StopTime', sprintf('%g', max(t_vec)), ...
                'FixedStep', sprintf('%g', dt), ...
                'SaveTime', 'on', ...
                'Solver', 'FixedStepDiscrete', ...
                'LoadExternalInput', 'on', ...
                'ExternalInput', '[t_vec, vin]');
        
        y_out       = simOut.get('yout');
        t_out       = simOut.get('tout');
        
        v_zcdN = y_out.get(1).Values.Data;
        v_zcdP = y_out.get(2).Values.Data;
        v_zcdIn = y_out.get(3).Values.Data;
        v_ledIn = y_out.get(4).Values.Data;
        v_zcdOut = y_out.get(5).Values.Data;
        v_ledOut = y_out.get(6).Values.Data;

        % Get the simulated crossing time
        cross_LED = InterX([t_transp;v_ledOut'],[t_transp;v_high_vec]);
        cross_ZCD = InterX([t_transp;v_zcdOut'],[t_transp;v_high_vec]);
    
        if isempty(cross_LED)
            tcross_LED = [];
        else
            tcross_LED = cross_LED(1);
        end
        if isempty(cross_ZCD)
            tcross_ZCD = [];
        else
            tcross_ZCD = cross_ZCD(1);
        end

        % If there's no crossing point, assume that the cross is much later
        if isempty(tcross_LED) || isempty(tcross_ZCD)
            tcross_sim = [];
        else
            tcross_sim = max([tcross_LED, tcross_ZCD]);
        end
        fprintf('\n\t%e vs. %e', tcross_sim, tcross_real);

        % Keep increasing tau until it's too slow; once we've overshot, binary search
        if is_increasing
            if ~isempty(tcross_sim) && tcross_sim < tcross_real
                val_low = tau;
                tau = val_high;
                val_high = tau * 2;
            else
                is_increasing = false;
            end
        else
            if (val_high <= val_low)
                done = true;
            elseif ~isempty(tcross_sim)
                if (abs(tcross_sim - tcross_real) < error_tol)
                    done = true;
                elseif tcross_sim < tcross_real
                    tau = (tau + val_high)/2;
                    val_low = tau;
                else
                    tau = (val_low + tau)/2;
                    val_high = tau;
                end
            else
                tau = (val_low + tau)/2;
                val_high = tau;
            end
        end
    end
    
%     % Plot inputs
%     subplot(plt_zcdIn);
%     plot(t_out, v_zcdIn);
%     xlabel("Time (s)");
%     ylabel("ZCD Input (V)");
%     ylim([min(v_zcdIn), max(v_zcdIn)*1.1]);
%     xlim([min(t_out), max(t_out)]);
%     
%     subplot(plt_ledIn);
%     subplot(num_plots, 1, 2);
%     plot(t_out, v_ledIn);
%     xlabel("Time (s)");
%     ylabel("LED Input (V)");
%     ylim([min(v_ledIn), max(v_ledIn)*1.1]);
%     xlim([min(t_out), max(t_out)]);
    
%     while ~done
%         cla(plt_vLED);
%         cla(plt_vZCD);
        
        
%         % Plotting
%         subplot(plt_vLED);
%         plot(t_out, v_LED);
%         hold on;
%         plot(t_out, ones(size(t_vec))*v_high);
%         xlabel("Time (s)");
%         ylabel("LED Output (V)");
%         ylim([min(v_LED), max(v_LED)*1.1]);
%         xlim([min(t_out), max(t_out)]);
%         
%         subplot(plt_vZCD);
%         plot(t_out, v_ZCD);
%         hold on;
%         plot(t_out, ones(size(t_vec))*v_high);
%         xlabel("Time (s)");
%         ylabel("ZCD Output (V)");
%         ylim([min(v_ZCD), max(v_ZCD)*1.1]);
%         xlim([min(t_out), max(t_out)]);
    
    tau_vec(i) = tau;
    tcross_sim_vec(i) = tcross_sim;
    disp(tau);
    disp(tcross_sim);
end

% Data dump
data.tau_vec = tau_vec;
data.tcross_sim_vec = tcross_sim_vec;
data.A_in_vec = A_in_vec;
data.tcross_raw_vec = tcross_raw_vec;
data.tcross_real_vec = tcross_real_vec;

yaml.dumpFile(strcat(pth_data, '/', fname), data);