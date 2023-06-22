/* --------------------------------- */
/* --- Pin Mappings (Arduino Due) --- */
/* --------------------------------- */
// Analog scan chain
const int pin_scan_inb      = 34;  // ASC input data

const int pin_scan0_outb     = 28;  // ASC output data
const int pin_scan0_clk      = 30;  // ASC clock
const int pin_scan0_loadb    = 32;  // ASC load

const int pin_scan1_outb     = 7;  // ASC output data
const int pin_scan1_clk      = 6;  // ASC clock
const int pin_scan1_loadb    = 5;  // ASC load

// TDC SPI and other connections
const int pin_spi_din      = 43; // Data-in

const int pin_spi_main_single0_csb      = 38; // CSb
const int pin_spi_main_single0_dout     = 46; // Data-out
const int pin_spi_main_single0_clk      = 40;	// SPI clock
const int pin_tdc_main_single0_intrptb  = 48; // Interrupt
const int pin_tdc_main_single0_en       = 44; // Active high enable
const int pin_tdc_main_single0_trig     = 42; // Raises when TDC is ready

const int pin_spi_small_single0_csb     = 18; // CSb
const int pin_spi_small_single0_dout    = 19; // Data-out
const int pin_spi_small_single0_clk     = 17; // SPI clock
const int pin_tdc_small_single0_intrptb = 20; // Interrupt
const int pin_tdc_small_single0_en      = 24; // Active high enable
const int pin_tdc_small_single0_trig    = 22; // Raises when TDC is ready

const int pin_spi_main_single1_csb      = 4; // CSb
const int pin_spi_main_single1_dout     = 15; // Data-out
const int pin_spi_main_single1_clk      = 3; // SPI clock
const int pin_tdc_main_single1_intrptb  = 16; // Interrupt
const int pin_tdc_main_single1_en       = 14; // Active high enable
const int pin_tdc_main_single1_trig     = 2; // Raises when TDC is ready

const int pin_spi_small_single1_csb     = 12; // CSb
const int pin_spi_small_single1_dout    = 11; // Data-out
const int pin_spi_small_single1_clk     = 13; // SPI clock
const int pin_tdc_small_single1_intrptb = 10; // Interrupt
const int pin_tdc_small_single1_en      = 8; // Active high enable
const int pin_tdc_small_single1_trig    = 9; // Raises when TDC is ready

const int pin_spi_main_dual_csb      = 41; // CSb
const int pin_spi_main_dual_dout     = 37; // Data-out
const int pin_spi_main_dual_clk      = 39; // SPI clock
const int pin_tdc_main_dual_intrptb  = 35; // Interrupt
const int pin_tdc_main_dual_en       = 53; // Active high enable
const int pin_tdc_main_dual_trig     = 51; // Raises when TDC is ready

const int pin_spi_small_dual_csb     = 27; // CSb
const int pin_spi_small_dual_dout    = 25; // Data-out
const int pin_spi_small_dual_clk     = 29; // SPI clock
const int pin_tdc_small_dual_intrptb = 23; // Interrupt
const int pin_tdc_small_dual_en      = 33; // Active high enable
const int pin_tdc_small_dual_trig    = 31; // Raises when TDC is ready

// Analog I/O signal voltages
const int pin_dac_small0 	= 61;	// Resistive DAC for small chain
const int pin_dac_main0 	= 62;	// Resistive DAC for main chain
const int pin_bandgap0		= 64;	// Test structure bandgap voltage source
const int pin_pk_out0 		= 65;	// Peak detector output voltage
const int pin_preamp_vref0  = 63;	// Preamp reference voltage

const int pin_dac_small1 	= 56;	// Resistive DAC for small chain
const int pin_dac_main1 	= 57;	// Resistive DAC for main chain
const int pin_bandgap1		= 55;	// Test structure bandgap voltage source
const int pin_pk_out1 		= 54;	// Peak detector output voltage
const int pin_preamp_vref1  = 58;	// Preamp reference voltage

const int pin_vddmeas0		= 60; // Jumpered on-chip supply measurement pin
const int pin_vddmeas1		= 59; // Jumpered on-chip supply measurement pin

// Resets, enables, and the like
const int pin_pk_rst		  = 36;	// Reset for test structure peak detector
const int pin_latch_rstb	= 26;	  // Reset for TDC input latch

// For getting a reference clock
const int pin_clk_ref = 45;

// Constants
const int B_ADC             = 12;   // Resolution for ADC read/write
const int CHAIN_MAIN        = 0;    // Used to indicate the main signal chain
const int CHAIN_SMALL       = 1;    // Used to indicate the small signal chain
const int CHANNEL_START     = 0;    // Used to indicate the START channel
const int CHANNEL_STOP      = 1;    // Used to indicate the STOP channel
const int CHANNEL_DUAL      = 2;    // Used to indicate both channels used

/* ----------------------------- */
/* --- Runs once at power-on --- */
/* ----------------------------- */
void setup() {
  Serial.begin(115200);

  analogReadResolution(B_ADC); 
  analogWriteResolution(B_ADC);

  pinMode(pin_scan_inb,         OUTPUT);
  digitalWrite(pin_scan_inb,    LOW);
  
  pinMode(pin_scan0_outb,       INPUT);
  pinMode(pin_scan0_clk,        OUTPUT);
  pinMode(pin_scan0_loadb,      OUTPUT);
  digitalWrite(pin_scan0_clk,   LOW);
  digitalWrite(pin_scan0_loadb, HIGH);
  
  pinMode(pin_scan1_outb,       INPUT);
  pinMode(pin_scan1_clk,        OUTPUT);
  pinMode(pin_scan1_loadb,      OUTPUT);
  digitalWrite(pin_scan1_clk,   LOW);
  digitalWrite(pin_scan1_loadb, HIGH);

  pinMode(pin_spi_din,          OUTPUT);
  digitalWrite(pin_spi_din,     LOW);

  pinMode(pin_spi_main_single0_csb,       OUTPUT);
  pinMode(pin_spi_main_single0_dout,      INPUT);
  pinMode(pin_spi_main_single0_clk,       OUTPUT);
  pinMode(pin_tdc_main_single0_intrptb,   INPUT);
  pinMode(pin_tdc_main_single0_en,        OUTPUT);
  pinMode(pin_tdc_main_single0_trig,      INPUT);
  digitalWrite(pin_spi_main_single0_csb,  HIGH);
  digitalWrite(pin_spi_main_single0_clk,  LOW);
  digitalWrite(pin_tdc_main_single0_en,   LOW);

  pinMode(pin_spi_small_single0_csb,       OUTPUT);
  pinMode(pin_spi_small_single0_dout,      INPUT);
  pinMode(pin_spi_small_single0_clk,       OUTPUT);
  pinMode(pin_tdc_small_single0_intrptb,   INPUT);
  pinMode(pin_tdc_small_single0_en,        OUTPUT);
  pinMode(pin_tdc_small_single0_trig,      INPUT);
  digitalWrite(pin_spi_small_single0_csb,  HIGH);
  digitalWrite(pin_spi_small_single0_clk,  LOW);
  digitalWrite(pin_tdc_small_single0_en,   LOW);

  pinMode(pin_spi_main_single1_csb,       OUTPUT);
  pinMode(pin_spi_main_single1_dout,      INPUT);
  pinMode(pin_spi_main_single1_clk,       OUTPUT);
  pinMode(pin_tdc_main_single1_intrptb,   INPUT);
  pinMode(pin_tdc_main_single1_en,        OUTPUT);
  pinMode(pin_tdc_main_single1_trig,      INPUT);
  digitalWrite(pin_spi_main_single1_csb,  HIGH);
  digitalWrite(pin_spi_main_single1_clk,  LOW);
  digitalWrite(pin_tdc_main_single1_en,   LOW);

  pinMode(pin_spi_small_single1_csb,       OUTPUT);
  pinMode(pin_spi_small_single1_dout,      INPUT);
  pinMode(pin_spi_small_single1_clk,       OUTPUT);
  pinMode(pin_tdc_small_single1_intrptb,   INPUT);
  pinMode(pin_tdc_small_single1_en,        OUTPUT);
  pinMode(pin_tdc_small_single1_trig,      INPUT);
  digitalWrite(pin_spi_small_single1_csb,  HIGH);
  digitalWrite(pin_spi_small_single1_clk,  LOW);
  digitalWrite(pin_tdc_small_single1_en,   LOW);

  pinMode(pin_spi_main_dual_csb,       OUTPUT);
  pinMode(pin_spi_main_dual_dout,      INPUT);
  pinMode(pin_spi_main_dual_clk,       OUTPUT);
  pinMode(pin_tdc_main_dual_intrptb,   INPUT);
  pinMode(pin_tdc_main_dual_en,        OUTPUT);
  pinMode(pin_tdc_main_dual_trig,      INPUT);
  digitalWrite(pin_spi_main_dual_csb,  HIGH);
  digitalWrite(pin_spi_main_dual_clk,  LOW);
  digitalWrite(pin_tdc_main_dual_en,   LOW);

  pinMode(pin_spi_small_dual_csb,       OUTPUT);
  pinMode(pin_spi_small_dual_dout,      INPUT);
  pinMode(pin_spi_small_dual_clk,       OUTPUT);
  pinMode(pin_tdc_small_dual_intrptb,   INPUT);
  pinMode(pin_tdc_small_dual_en,        OUTPUT);
  pinMode(pin_tdc_small_dual_trig,      INPUT);
  digitalWrite(pin_spi_small_dual_csb,  HIGH);
  digitalWrite(pin_spi_small_dual_clk,  LOW);
  digitalWrite(pin_tdc_small_dual_en,   LOW);

  pinMode(pin_dac_small0,   INPUT);
  pinMode(pin_dac_main0,    INPUT);
  pinMode(pin_bandgap0,     INPUT);
  pinMode(pin_pk_out0,      INPUT);
  pinMode(pin_preamp_vref0, INPUT);

  pinMode(pin_dac_small1,   INPUT);
  pinMode(pin_dac_main1,    INPUT);
  pinMode(pin_bandgap1,     INPUT);
  pinMode(pin_pk_out1,      INPUT);
  pinMode(pin_preamp_vref1, INPUT);

  pinMode(pin_vddmeas0,   INPUT);
  pinMode(pin_vddmeas1,   INPUT);

  pinMode(pin_pk_rst,           OUTPUT);
  pinMode(pin_latch_rstb,       OUTPUT);
  digitalWrite(pin_pk_rst,      LOW);
  digitalWrite(pin_latch_rstb,  HIGH);
  
  // TODO 8MHz-16MHz, 50% duty cycle clock
  pinMode(pin_clk_ref, OUTPUT);
  analogWrite(pin_clk_ref, 1<<(B_ADC-1));
  // analogWriteFrequency(pin_clk_ref, 16000000);
}

void loop() {
  // --- Serial port connection ---
  if (true) {
    Serial.println("blep");
  }

  // --- Reading internal temperature ---
  if (false) {
    check_internalTemp();
  }
/*
  // --- Reading Nonzero Value from TDC Register ---
  if (false) {
    for (char addr=0; addr<0x0A; addr++) {
      tdc_read_reg(CHAIN_SMALL, addr);
    }
  }

  // --- Reading Data Out from TDC Registers During Write ---
  if (false) {
    for (char addr=0; addr<0x02; addr++) {
      tdc_write_reg(CHAIN_SMALL, addr);  
    }
  }

  // --- Writing to and Reading out from Registers ---
  if (true) {
      tdc_rw_reg(CHAIN_SMALL);
  }

  // --- Arm the TDC for Measurement ---
  if (false) {
    tdc_arm(CHAIN_SMALL);
  }

  // --- Toggle Pin Up and Down ---
  if (false) {
    digitalWrite(TODO pin, HIGH);
    delayMicroseconds(100);
    digitalWrite(TODO pin, LOW);
    delayMicroseconds(100);
  }
*/
}

/* ---------------------------- */
/* --- Internal Thermometer --- */
/* ---------------------------- */
void check_internalTemp() {
/*
 * Inputs:
 *   None.
 * Returns:
 *   None.
 * Notes:
 *  - Reads the internal temperature from the Arduino and prints it over serial.
 *    Recommend .decode() on the receiving side.
 */
  for (int i=0; i<100; i++) {
    ADC->ADC_ACR |= ADC_ACR_TSON; // Enable temperature sensor
    Serial.println(analogRead(15)); 
  }

}