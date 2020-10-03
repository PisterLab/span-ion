function [t_out, s_compInP, s_compInN, d_out] = sim_shaper(t, shaper_struct);

dt = t(2) - t(1);
shaper_type = shaper_struct.type;

cfd_vars_map = containers.Map();
cfd_vars_map('nowlin')      = 'f_attenuation = shaper_struct.f_attenuation;';
cfd_vars_map('threshold')   = 'v_threshold = shaper_struct.v_threshold;';
cfd_vars_map('diff')        = 'v_threshold = shaper_struct.v_threshold;';
cfd_vars_map('delay_atten') = 'f_attenuation = shaper_struct.f_attenuation; t_delay = shaper_struct.t_delay;';

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
              'ExternalInput', '[t'', v_preampOut]');

y_out       = simOut.get('yout');
t_out       = simOut.get('tout');
d_out       = y_out.get(1).Values.Data;
v_compIn    = y_out.get(2).Values.Data;
v_compInN   = y_out.get(3).Values.Data;
v_compInP   = y_out.get(4).Values.Data;

eval(cfd_reshape_map(shaper_type));

% Final assignments
s_compInP       = v_compInP;
s_compInN       = v_compInN;

end