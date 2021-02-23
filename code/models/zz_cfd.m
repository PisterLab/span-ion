clear all
close all
clc

% ---------------------------- START CHANGES ---------------------------- %
zc_list_idx = 3;    % nth zero crossing to use for annotation
N_pulse = 0.5;       % number of pulses to produce
A_pulse_vec = [100e-6];   % input current pulse max
% ----------------------------- STOP CHANGES ---------------------------- %

%%% Preamp
preamp_vars_map = containers.Map();
% ---------------------------- START CHANGES ---------------------------- %
preamp_type = 'RC';

preamp_vars_map('R')    = 'Rf = 800;';
preamp_vars_map('RC')   = 'Rf = 800; Cf = 1e-12;';
preamp_vars_map('C')    = 'Cf = 1e-12;';
% ----------------------------- STOP CHANGES ---------------------------- %
preamp_tf_num_map = containers.Map();
preamp_tf_num_map('R')  = '[Rf]';
preamp_tf_num_map('RC') = '[Rf]';
preamp_tf_num_map('C')  = '[1]';

preamp_tf_den_map = containers.Map();
preamp_tf_den_map('R')  = '[1]';
preamp_tf_den_map('RC') = '[Rf*Cf 1]';
preamp_tf_den_map('C')  = '[Cf 0]';

%%% CFD Shaping
cfd_vars_map = containers.Map();
% ---------------------------- START CHANGES ---------------------------- %
inject_pulse    = false;    % True to inject a square pulse at v_in
inject_height   = 10e-3;
inject_width    = 100e-12;
inject_tstart   = .5e-9;

shaper_type = 'delay_peakDet_oneShot_atten';
v_LED = .02;

cfd_vars_map('nowlin')              = 'f_attenuation = 0.5;';
cfd_vars_map('threshold')           = 'v_threshold = 0.04;';
cfd_vars_map('diff')                = 'v_threshold = 0.1;';
cfd_vars_map('delay_atten')         = 'f_attenuation = 0.5; t_delay = 1e-9;';
cfd_vars_map('delay_peakDet_oneShot_atten') = 'f_attenuation = 0.5; t_delay = 1e-9;';
cfd_vars_map('delayNonideal_atten') = 'f_attenuation = 0.5; H_delay_num = [1, -4e10, 7.2e20, -6.72e30, 2.668e40]; H_delay_den = [1, 4e10, 7.2e20, 6.72e30, 2.668e40];';
cfd_vars_map('delayNonideal_oneShot_atten') = 'f_attenuation = 0.5; H_delay_num = [1, -2e10, 1.8e20, -8.4e29, 1.68e39]; H_delay_den = [1, 2e10, 1.8e20, 8.4e29, 1.68e39];';
cfd_vars_map('delayNonideal_peakDet_oneShot_atten') = 'f_attenuation = 0.5; H_delay_num = [1, -2e10, 1.8e20, -8.4e29, 1.68e39]; H_delay_den = [1, 2e10, 1.8e20, 8.4e29, 1.68e39];';
% 1ns Bessel ord4: num = [1, -2e10, 1.8e20, -8.4e29, 1.68e39], den = [1, 2e10, 1.8e20, 8.4e29, 1.68e39]
% 500ps Bessel ord4: num = [1, -4e10, 7.2e20, -6.72e30, 22.688e40], den = [1, +4e10, 7.2e20, +6.72e30, 22.688e40]

% ----------------------------- STOP CHANGES ---------------------------- %
cfd_mdl_map = containers.Map();
cfd_mdl_map('nowlin')               = 'shape_nowlin';
cfd_mdl_map('threshold')            = 'shape_threshold';
cfd_mdl_map('diff')                 = 'shape_diff';
cfd_mdl_map('delay_atten')          = 'shape_delay_atten';
cfd_mdl_map('delay_peakDet_oneShot_atten') = 'shape_delay_peakDet_oneShot_atten';
cfd_mdl_map('delayNonideal_atten')  = 'shape_delayNonideal_atten';
cfd_mdl_map('delayNonideal_oneShot_atten')  = 'shape_delayNonideal_oneShot_atten';
cfd_mdl_map('delayNonideal_peakDet_oneShot_atten')  = 'shape_delayNonideal_peakDet_oneShot_atten';

cfd_reshape_map = containers.Map();
cfd_reshape_map('nowlin')               = '';
cfd_reshape_map('threshold')            = 'v_compInP=ones(size(t_out))*v_compInP;';
cfd_reshape_map('diff')                 = 'v_compInP=ones(size(t_out))*v_compInP;';
cfd_reshape_map('delay_atten')          = '';
cfd_reshape_map('delay_peakDet_oneShot_atten') = '';
cfd_reshape_map('delayNonideal_atten')  = '';
cfd_reshape_map('delayNonideal_oneShot_atten')  = '';
cfd_reshape_map('delayNonideal_peakDet_oneShot_atten')  = '';

%% Input current: square wave (for now)
% ---------------------------- START CHANGES ---------------------------- %
t_event = 15e-9;     % pulse period
t_pulse = 1e-9;      % pulse length
snr     = inf;% 20;       % SNR wrt -80dBW signal (dB)
% ----------------------------- STOP CHANGES ---------------------------- %
dt      = t_pulse/100;
t0      = [0 : dt : N_pulse*t_event];
f_event = 1/t_event;

% Add time in front to avoid nonzero initial condition
t       = [0 : dt : N_pulse*t_event+dt];

% Keeping track of the different scenarios
i_in_vec        = [];
v_in_vec        = [];
v_compInP_vec   = [];
v_compInN_vec   = [];
d_out_vec       = [];
t_out_vec       = [];

for i = 1:numel(A_pulse_vec)
    A_pulse = A_pulse_vec(i);
    i_in0   = A_pulse * (1 + square(2*pi*f_event*t0, t_pulse/t_event*100)) / 2;
    i_in    = [0 i_in0];
    i_in    = awgn(i_in, snr, -80);
    
    % Preamp
    eval(preamp_vars_map(preamp_type));
    H_preamp = tf(eval(preamp_tf_num_map(preamp_type)), eval(preamp_tf_den_map(preamp_type)));

    v_in = lsim(H_preamp, i_in, t);
    
    if inject_pulse
        idx_start                       = cast(inject_tstart/dt, 'uint16');
        idx_stop                        = cast((inject_tstart + inject_width)/dt, 'uint16');
        v_inject                        = zeros(1, numel(t));
        v_inject(idx_start: idx_stop)   = inject_height;
        v_in                            = v_in + v_inject';
    end

    % CFD
    mdl = cfd_mdl_map(shaper_type);
    eval(cfd_vars_map(shaper_type));

    if ~contains(shaper_type, 'delayNonideal')
        simOut  = sim(mdl, ...
                      'StartTime', sprintf('%g', min(t)), ...
                      'StopTime', sprintf('%g', max(t)), ...
                      'FixedStep', sprintf('%g', dt), ...
                      'SaveTime', 'on', ...
                      'Solver', 'FixedStepDiscrete', ...
                      'LoadExternalInput', 'on', ...
                      'ExternalInput', '[t'', v_in]');
    else
        H_delay = tf(H_delay_num, H_delay_den);
        v_inDelay = lsim(H_delay, v_in, t);
        simOut  = sim(mdl, ...
                      'StartTime', sprintf('%g', min(t)), ...
                      'StopTime', sprintf('%g', max(t)), ...
                      'FixedStep', sprintf('%g', dt), ...
                      'SaveTime', 'on', ...
                      'Solver', 'FixedStepDiscrete', ...
                      'LoadExternalInput', 'on', ...
                      'ExternalInput', '[t'', v_in, v_inDelay]');
    end

    y_out       = simOut.get('yout');
    t_out       = simOut.get('tout');
    d_out       = y_out.get(1).Values.Data;
    v_compIn    = y_out.get(2).Values.Data;
    
    if contains(shaper_type, 'delayNonideal')
        v_compInN = interp1(t, v_inDelay, t_out);
        v_compInP = y_out.get(3).Values.Data;
        idx_start = 4;
    else
        v_compInN = y_out.get(3).Values.Data;
        v_compInP = y_out.get(4).Values.Data;
        idx_start = 5;
    end
    
    if contains(shaper_type, 'oneShot')
        v_ZCD_oneShot = y_out.get(idx_start).Values.Data;
        v_LED_oneShot = y_out.get(idx_start + 1).Values.Data;
    end
    

    eval(cfd_reshape_map(shaper_type));
    
    % Storing data for plotting later
    i_in_vec{i}         = i_in;
    v_in_vec{i}         = v_in;
    v_compInP_vec{i}    = v_compInP;
    v_compInN_vec{i}    = v_compInN;
    d_out_vec{i}        = d_out;
    t_out_vec{i}        = t_out;
end

%% Plot results
num_plt_rows = 4;
num_plt_cols = numel(A_pulse_vec);

ylim_min = [inf inf inf inf];
ylim_max = [-inf -inf -inf -inf];
xlim_min = [inf inf inf inf];
xlim_max = [-inf -inf -inf -inf];

for cidx = 1:num_plt_cols
    i_in        = i_in_vec{cidx};
    v_in        = v_in_vec{cidx};
    v_compInP   = v_compInP_vec{cidx};
    v_compInN   = v_compInN_vec{cidx};
    d_out       = d_out_vec{cidx};
    t_out       = t_out_vec{cidx};
    
    % Input current
    plt_iin = subplot(num_plt_rows, num_plt_cols, cidx);
    plot(t, i_in);
    ylabel({'Input', 'Current', '(A)'});
    xlabel('Time (s)');
    
    % -- annotate pulse height -- 
    if snr == inf
        [i_in_pk, i_in_pk_idx] = max(i_in);
        title(sprintf('%0-#1.0d uA Peak Current', i_in_pk*1e6));
    end
    
    ylim_min(1) = min(ylim_min(1), min(i_in));
    ylim_max(1) = max(ylim_max(1), max(i_in)*1.1);
    xlim_min(1) = min(xlim_min(1), min(t));
    xlim_max(1) = max(xlim_max(1), max(t));

    % Preamp output
    plt_vpreampOut = subplot(num_plt_rows, num_plt_cols, num_plt_cols + cidx);
    plot(t, v_in);
    ylabel({'Preamp', 'Output', '(V)'});
    xlabel('Time (s)');
    
    preamp_title = '';
    if contains(preamp_type, 'R')
        preamp_title = strcat(preamp_title, sprintf('\nR = %d Ohm', Rf));
    end
    if contains(preamp_type, 'C')
        preamp_title = strcat(preamp_title, sprintf('\nC = %d pF', Cf*1e12));
    end
    
    % -- add thresholding -- 
    if v_LED > 0
        hold on;
        plot(t, ones(1, numel(t))*v_LED);
        preamp_title = strcat(preamp_title, sprintf('\nLED Threshold = %d mV', v_LED*1e3));
    end
    
    % -- annotate peak --
    if contains(shaper_type, 'delayNonideal')
        [pk_in, pk_in_loc] = max(v_in);
        plot(t_out(pk_in_loc), pk_in, 'rp');
        text(t(pk_in_loc), pk_in, sprintf('peak=%0-#1.3f mV', pk_in*1000));
    end
    
    title(preamp_title);
    
    ylim_min(2) = min(ylim_min(2), min(v_in));
    ylim_max(2) = max(ylim_max(2), max(v_in)*1.1);
    xlim_min(2) = min(xlim_min(2), min(t));
    xlim_max(2) = max(xlim_max(2), max(t));

    % Comparator inputs
    plt_vcompInSplit = subplot(num_plt_rows, num_plt_cols, 2*num_plt_cols + cidx);
    plot(t_out, v_compInP);
    hold on;
    plot(t_out, v_compInN);
    
    ylabel({'Comparator', 'Inputs', '(V)'});
    xlabel('Time (s)');
    
    ylim_min(3) = min(ylim_min(3), min([v_compInN; v_compInP]));
    ylim_max(3) = max(ylim_max(3), max([v_compInN; v_compInP])*1.1);
    xlim_min(3) = min(xlim_min(3), min(t_out));
    xlim_max(3) = max(xlim_max(3), max(t_out));

    % -- annotate peak --
    if contains(shaper_type, 'delay')
        [pkN, pkN_loc] = max(v_compInN);
        [pkP, pkP_loc] = max(v_compInP);
%         plot(t_out(pkN_loc), pkN, 'rp');
%         text(t_out(pkN_loc), pkN, sprintf('peak=%0-#1.3f mV', pkN*1000));
    end
    % -- annotate intersection point -- 
    zci = @(v) find(v(:).*circshift(v(:), [-1 0]) <= 0);
    v_compIn = v_compInP - v_compInN;
    zc_idx_list = zci(v_compIn);
    
    if snr == inf && numel(zc_idx_list) > 0
        zc_idx = zc_idx_list(zc_list_idx); % max(zc_idx_list);
        plot(t_out(zc_idx), min(v_compInP(zc_idx), v_compInN(zc_idx)), 'bp');
%         text(t_out(zc_idx), v_compInP(zc_idx), sprintf('t=%0-#1.2f ns', t(zc_idx)*1e9), ...
%             'VerticalAlignment', 'bottom');
        text(t_out(zc_idx), v_compInP(zc_idx), sprintf('f=%0.2f', v_compInP(zc_idx)/pkN), ...
            'VerticalAlignment', 'bottom');
    end
    
    if contains(shaper_type, 'delay') && ~contains(shaper_type, 'delayNonideal')
        title(sprintf('Delay = %#2.2f ps', t_delay*1e12));
    end

    % Comparator output
    plt_dout = subplot(num_plt_rows, num_plt_cols, 3*num_plt_cols + cidx);
    plot(t_out, d_out);
    ylabel({'Final', 'Output'});
    xlabel('Time (s)');
    
    ylim_min(4) = min(ylim_min(4), min(d_out));
    ylim_max(4) = max(ylim_max(4), max(d_out)*1.1);
    xlim_min(4) = min(xlim_min(4), min(t_out));
    xlim_max(4) = max(xlim_max(4), max(t_out));
end

% Set limits so plots of the same type of signal have the same limits
for ridx = 1:num_plt_rows
    for cidx = 1:num_plt_cols
        subplot(num_plt_rows, num_plt_cols, (ridx-1)*num_plt_cols + cidx);
        ylim([ylim_min(ridx), ylim_max(ridx)]);
        xlim([xlim_min(ridx), xlim_max(ridx)]);
    end
end


super_title = '';
%%
figure('Position', [10 10 600 300]);
norm_factor = 1;
v_compInP = v_compInP/norm_factor;
v_compInN = v_compInN/norm_factor;
plot(t_out, v_compInP);
hold on;
plot(t_out, v_compInN);

ylabel({'Comparator Inputs', '(V)'}, 'Fontsize', 12);
xlabel('Time (s)', 'Fontsize', 12);

ylim_min(3) = min(ylim_min(3), min([v_compInN; v_compInP]));
ylim_max(3) = max(ylim_max(3), max([v_compInN; v_compInP])*1.1);
xlim_min(3) = min(xlim_min(3), min(t_out));
xlim_max(3) = max(xlim_max(3), max(t_out));

% -- annotate peak --
if contains(shaper_type, 'delay')
    [pkN, pkN_loc] = max(v_compInN);
    [pkP, pkP_loc] = max(v_compInP);
%         plot(t_out(pkN_loc), pkN, 'rp');
%         text(t_out(pkN_loc), pkN, sprintf('peak=%0-#1.3f mV', pkN*1000));
end
% -- annotate intersection point -- 
zci = @(v) find(v(:).*circshift(v(:), [-1 0]) <= 0);
v_compIn = v_compInP - v_compInN;
zc_idx_list = zci(v_compIn);

if snr == inf && numel(zc_idx_list) > 0
    zc_idx = zc_idx_list(zc_list_idx); % max(zc_idx_list);
    plot(t_out(zc_idx), min(v_compInP(zc_idx), v_compInN(zc_idx)), 'bp');
        text(t_out(zc_idx), v_compInP(zc_idx), sprintf('t=%0-#1.2f ns', t(zc_idx)*1e9), ...
            'VerticalAlignment', 'bottom');
%     text(t_out(zc_idx), v_compInP(zc_idx), sprintf('f=%0.2f', v_compInP(zc_idx)/pkN), ...
%         'VerticalAlignment', 'bottom', ...
%         'Fontsize', 12);
end

%%
figure('Position', [10 10 600 300]);
norm_factor = max(v_compInN);
v_compInP = v_compInP/norm_factor;
v_compInN = v_compInN/norm_factor;
plot(t_out, v_compInP);
hold on;
plot(t_out, v_compInN);

ylabel({'Normalized', 'Comparator Inputs', '(V)'}, 'Fontsize', 12);
xlabel('Time (s)', 'Fontsize', 12);

ylim_min(3) = min(ylim_min(3), min([v_compInN; v_compInP]));
ylim_max(3) = max(ylim_max(3), max([v_compInN; v_compInP])*1.1);
xlim_min(3) = min(xlim_min(3), min(t_out));
xlim_max(3) = max(xlim_max(3), max(t_out));

% -- annotate peak --
if contains(shaper_type, 'delay')
    [pkN, pkN_loc] = max(v_compInN);
    [pkP, pkP_loc] = max(v_compInP);
%         plot(t_out(pkN_loc), pkN, 'rp');
%         text(t_out(pkN_loc), pkN, sprintf('peak=%0-#1.3f mV', pkN*1000));
end
% -- annotate intersection point -- 
zci = @(v) find(v(:).*circshift(v(:), [-1 0]) <= 0);
v_compIn = v_compInP - v_compInN;
zc_idx_list = zci(v_compIn);

if snr == inf && numel(zc_idx_list) > 0
    zc_idx = zc_idx_list(zc_list_idx); % max(zc_idx_list);
    plot(t_out(zc_idx), min(v_compInP(zc_idx), v_compInN(zc_idx)), 'bp');
%         text(t_out(zc_idx), v_compInP(zc_idx), sprintf('t=%0-#1.2f ns', t(zc_idx)*1e9), ...
%             'VerticalAlignment', 'bottom');
    text(t_out(zc_idx), v_compInP(zc_idx), sprintf('f=%0.2f', v_compInP(zc_idx)/pkN), ...
        'VerticalAlignment', 'bottom', ...
        'Fontsize', 12);
end