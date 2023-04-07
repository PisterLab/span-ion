#include <InternalTemperature.h> // include the InternalTemperature library
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

const int pin_spi_main_single0_csb      = ; // CSb
const int pin_spi_main_single0_dout     = ; // Data-out
const int pin_spi_main_single0_clk      = ;	// SPI clock
const int pin_tdc_main_single0_intrptb  = ; // Interrupt
const int pin_tdc_main_single0_en       = ; // Active high enable
const int pin_tdc_main_single0_trig     = ; // Raises when TDC is ready
const int pin_tdc_main_single0_start    = ; // For triggering the TDC's start pulse

const int pin_spi_small_single0_csb     = ; // CSb
const int pin_spi_small_single0_dout    = ; // Data-out
const int pin_spi_small_single0_clk     = ; // SPI clock
const int pin_tdc_small_single0_intrptb = ; // Interrupt
const int pin_tdc_small_single0_en      = ; // Active high enable
const int pin_tdc_small_single0_trig    = ; // Raises when TDC is ready
const int pin_tdc_small_single0_start   = ; // For triggering the TDC's start pulse

const int pin_spi_main_single1_csb      = ; // CSb
const int pin_spi_main_single1_dout     = ; // Data-out
const int pin_spi_main_single1_clk      = ; // SPI clock
const int pin_tdc_main_single1_intrptb  = ; // Interrupt
const int pin_tdc_main_single1_en       = ; // Active high enable
const int pin_tdc_main_single1_trig     = ; // Raises when TDC is ready
const int pin_tdc_main_single1_start    = ; // For triggering the TDC's start pulse

const int pin_spi_small_single1_csb     = 12; // CSb
const int pin_spi_small_single1_dout    = 11; // Data-out
const int pin_spi_small_single1_clk     = 13; // SPI clock
const int pin_tdc_small_single1_intrptb = 10; // Interrupt
const int pin_tdc_small_single1_en      = 8; // Active high enable
const int pin_tdc_small_single1_trig    = 9; // Raises when TDC is ready
const int pin_tdc_small_single1_start   = ; // For triggering the TDC's start pulse

const int pin_spi_main_dual_csb      = ; // CSb
const int pin_spi_main_dual_dout     = ; // Data-out
const int pin_spi_main_dual_clk      = ; // SPI clock
const int pin_tdc_main_dual_intrptb  = ; // Interrupt
const int pin_tdc_main_dual_en       = ; // Active high enable
const int pin_tdc_main_dual_trig     = ; // Raises when TDC is ready
const int pin_tdc_main_dual_start    = ; // For triggering the TDC's start pulse

const int pin_spi_small_dual_csb     = ; // CSb
const int pin_spi_small_dual_dout    = ; // Data-out
const int pin_spi_small_dual_clk     = ; // SPI clock
const int pin_tdc_small_dual_intrptb = ; // Interrupt
const int pin_tdc_small_dual_en      = ; // Active high enable
const int pin_tdc_small_dual_trig    = ; // Raises when TDC is ready
const int pin_tdc_small_dual_start   = ; // For triggering the TDC's start pulse

// Analog I/O signal voltages
const int pin_dac_small0 	= ;	// Resistive DAC for small chain
const int pin_dac_main0 	= ;	// Resistive DAC for main chain
const int pin_bandgap0		= ;	// Test structure bandgap voltage source
const int pin_pk_out0 		= ;	// Peak detector output voltage
const int pin_preamp_vref0  = ;	// Preamp reference voltage
const int pin_vref_atten0	= ;	// Attenuator reference voltage

const int pin_dac_small1 	= ;	// Resistive DAC for small chain
const int pin_dac_main1 	= ;	// Resistive DAC for main chain
const int pin_bandgap1		= ;	// Test structure bandgap voltage source
const int pin_pk_out1 		= ;	// Peak detector output voltage
const int pin_preamp_vref1  = ;	// Preamp reference voltage
const int pin_vref_atten1	= ;	// Attenuator reference voltage

const int pin_vddmeas0		= ; // Jumpered on-chip supply measurement pin
const int pin_vddmeas1		= ; // Jumpered on-chip supply measurement pin

// Resets, enables, and the like
const int pin_pk_rst		= ;	// Reset for test structure peak detector
const int pin_latch_rstb	= 26;	  // Reset for TDC input latch

// For getting a reference clock
const int pin_clk_ref = 45;