clear all;
close all;
clc;

tdelay = 1.0e-9;
w0 = 1/tdelay;
scale_num = false;
k1 = 0.75;
k2 = 2;
C1 = 5e-15;
C2 = 5e-15;
R8 = 20e3;

%%%
[delay, f3dB, gain, R, C, k, Hscaled] = tt_biquad(w0, scale_num, k1, k2, C1, C2, R8);