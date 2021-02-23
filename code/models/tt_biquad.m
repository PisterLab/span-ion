function [delay, f3dB, gain, R, C, k, Hscaled] = tt_biquad(w0, scale_num, k1, k2, C1, C2, R8)

    [b, a] = besself(2, w0, 'low');
    [H, w] = freqs(b, a, 1000);
    grpdelay_vec = diff(unwrap(angle(H)))./diff(w);
    
    delay = grpdelay_vec(1);
   
    norm_factor = a(1);
    b2 = b(1);
    b1 = b(2);
    b0 = b(3);
    a1 = a(2);
    a0 = a(3);
        
    if scale_num
        b2 = b2 * norm_factor;
        b1 = b1 * norm_factor;
        b0 = b0 * norm_factor;
    else
        a1 = a1 / norm_factor;
        a0 = a0 / norm_factor;
    end
    
    gain = b0 / a0;
    
    R1 = 1/(a1*C1);
    R2 = k1/(sqrt(a0)*C2);
    R3 = 1/(k1*k2) * 1/(sqrt(a0)*C1);
    R4 = 1/k2 * 1/(a1*b2-b1) * 1/C1;
    R5 = k1*sqrt(a0)/(b0*C2);
    R6 = R8/b2;
    R7 = k2*R8;
    
    R = [R1, R2, R3, R4, R5, R6, R7, R8];
    C = [C1, C2];
    k = [k1, k2];
    
    Hscaled = tf([b2, b1, b0], [1, a1, a0]);
    f3dB = bandwidth(Hscaled) / (2*pi);
end