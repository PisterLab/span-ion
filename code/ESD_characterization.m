%% I-V Characterization of the ESD diodes 

Vpiezo_esd = [1.542 1.641 1.723 1.773 1.821 1.855 1.88 1.9 1.919 1.936 1.951 1.963 1.977];
Vin_esd = [1.542 1.644 1.745 1.8 1.9 2 2.1 2.2 2.3 2.3 2.5 2.6 2.7];
Vrect_esd = 1.03;
Vd_esd = Vpiezo_esd - Vrect_esd;
Res = 110.4;
Iin_esd = (Vin_esd - Vpiezo_esd)/Res;


figure()
plot(Vd_esd ,Iin_esd*1e3,'LineWidth',2);xlabel("Vd (V)", 'FontSize', 25);ylabel("Id (mA)",'FontSize', 25);title("ESD")
set(gca,'FontSize',20)
grid on