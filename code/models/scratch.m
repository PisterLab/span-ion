clear all
close all
clc

filt_ord_vec = [2,4];
w0_vec = [1e9, 1.85e9];
w0_vec = w0_vec/2;

% ============================
zci = @(v) find(v(:).*circshift(v(:), [-1 0]) <= 0);
dat_plots = [1:numel(filt_ord_vec)];

for i = 1:numel(filt_ord_vec)
    filt_ord = filt_ord_vec(i);
    w0 = w0_vec(i);

    % Get group delay vs. frequency
    [b,a] = besself(filt_ord, w0, 'low');
    [H, w] = freqs(b, a, 1000);
    w_vec = 0.5 * (w(2:numel(w)) + w(1:numel(w)-1));
    grpdelay_vec = diff(unwrap(angle(H)))./diff(w);
    
    % Plot
    delay = grpdelay_vec(1);
    delay_fracPct = delay*0.90;
    idx_fracPct = zci(grpdelay_vec-delay_fracPct);
    hold on;
    dat_plots(i) = semilogx(w_vec, -grpdelay_vec);
    
    % Annotation
    semilogx(w_vec(idx_fracPct(1)), -delay_fracPct, 'ko', 'MarkerFaceColor', 'k');
    text(w_vec(idx_fracPct(1)), -delay_fracPct, sprintf('%.0fMHz', 1e-6*w_vec(idx_fracPct(1))), ...
        'VerticalAlignment', 'top', ...
        'HorizontalAlignment', 'center');
    
    set(gca, 'XScale', 'log');

    % Axis labels
    xlabel('Frequency');
    ylabel('Group Delay');
    
end

% ylim([0,1.1]);

legend(dat_plots, '2nd Order', '4th Order');   % How in the frickity frack do I avoid doing 
                                    % this sh*t by hand
%%
clear all;
close all;
clc


scale_C = 400;
R = 1e3;

R1 = R;
R2 = R;
C1 = 390e-12/scale_C;
C2 = 358e-12/scale_C;
R3 = R;
R4 = R;
C3 = 537e-12/scale_C;
C4 = 206.9e-12/scale_C;

sk_A = [1, 1/C1*(R1+R2)/(R1*R2), 1/(R1*R2*C1*C2)];
sk_B = [1, 1/C3*(R3+R4)/(R3*R4), 1/(R3*R4*C3*C4)];
filt_polynom = conv(sk_A, sk_B);

b = [filt_polynom(numel(filt_polynom))];
a = filt_polynom;

[H, w] = freqs(b, a, 1000);
grpdelay_vec = diff(unwrap(angle(H)))./diff(w);
    
delay = grpdelay_vec(1);
% display(-delay)

w_vec = (w(2:numel(w)) + w(1:(numel(w)-1)))*0.5;
semilogx(w_vec, -grpdelay_vec);
xlabel('Frequency (Hz)');
ylabel('Group Delay (s)')

sprintf('R1|R2|R3|R4 = %f | %f | %f | %f\nC1|C2|C3|C4 = %d | %d | %d | %d\n-> %d seconds', R1, R2, R3, R4, C1, C2, C3, C4, -delay)

figure()
bode(b, a)