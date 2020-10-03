function [t_out, s_out] = sim_preamp(t, s_in, preamp_struct);

i_in = s_in;

preamp_type = preamp_struct.type;

preamp_vars_map = containers.Map();
preamp_vars_map('R')    = 'Rf = preamp_struct.Rf;';
preamp_vars_map('RC')   = 'Rf = preamp_struct.Rf; Cf = preamp_struct.Cf;';
preamp_vars_map('C')    = 'Cf = preamp_struct.Cf;';

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

s_out = lsim(H_preamp, i_in, t);
t_out = t;

end