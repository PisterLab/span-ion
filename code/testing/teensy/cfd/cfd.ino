
#include "scan.h"
#include "tdc7200.h"
#include "test_structs.h"
/* --------------------------------- */
/* --- Pin Mappings (Teensy 3.6) --- */
/* --------------------------------- */
// Analog scan chain
const int pin_scan_inb 			= A15;	// ASC input data
const int pin_scan_outb 		= A18;	// ASC output data
const int pin_scan_clk 			= A17;	// ASC clock
const int pin_scan_loadb 		= A16;	// ASC load

// Analog I/O signal voltages
const int pin_dac_small 		= A20; 	// Resistive DAC for small chain
const int pin_dac_main 			= A7;	  // Resistive DAC for main chain
const int pin_bandgap			  = A9;	  // Test structure bandgap voltage source
const int pin_pk_out 			  = A8; 	// Peak detector output voltage
const int pin_preamp_vref   = A21;  // Preamp reference voltage
const int pin_vref_atten    = A22;  // Attenuator reference voltage

// On-chip supply voltages
const int pin_vddaon 			= A6;	  // Always-on LDO output
const int pin_vddmain			= A5;	  // Main signal chain LDO output
const int pin_vddsmall 		= A19; 	// Small signal chain LDO output

// Resets, enables, and the like
const int pin_pk_rst			  = A14;	// Reset for test structure peak detector
const int pin_latch_rstb 		= A3;	  // Reset for TDC input latch

// TDC SPI and other connections
const int pin_spi_main_csb 		  = 10;	// CSb for the main signal chain TDC
const int pin_spi_main_din		  = 11; // Data-in pin for the main signal chain TDC
const int pin_spi_main_dout 	  = 12;	// Data-out pin for the main signal chain TDC
const int pin_spi_main_clk		  = 13;	// SPI clock for the main signal chain TDC
const int pin_tdc_main_intrptb	= 9;	// Interrupt pin for the TDC for the main signal chain
const int pin_tdc_main_en 		  = 8;	// Active high enable for main chain TDC
const int pin_tdc_main_trig		  = 7; 	// Raises when TDC for main chain is ready
const int pin_tdc_main_start    = 6;  // For triggering the TDC's start pulse

const int pin_spi_small_csb 	  = A12;	// CSb for the small signal chain TDC
const int pin_spi_small_din		  = 0; 	  // Data-in pin for the small signal chain TDC
const int pin_spi_small_dout 	  = 1;	  // Data-out pin for the small signal chain TDC
const int pin_spi_small_clk		  = A13;	// SPI clock for the small signal chain TDC
const int pin_tdc_small_intrptb	= 27;	  // Interrupt pin for the TDC for the small signal chain
const int pin_tdc_small_en 		  = 28;	  // Active high enable for small chain TDC
const int pin_tdc_small_trig 	  = 29;	  // Raises when TDC for small chain is ready
const int pin_tdc_small_start   = 30;   // For triggering the TDC's start pulse

const int pin_tdc_clk           = A0;   // TDC reference clock

// Constants
const int B_ADC 				        = 16;	  // Number of bits (precision) for Teensy analogRead

/* ----------------------------- */
/* --- Runs once at power-on --- */
/* ----------------------------- */
// Variables for command interpreter
String inputString = "";
boolean stringComplete = false;

void setup() {
	// Open USB serial port
	Serial.begin(9600);

	// Reserve 200 bytes for the inputString
	inputString.reserve(200);

	// Set up pins
	// - Analog Scan Chain
	pinMode(pin_scan_inb, 			OUTPUT);
	pinMode(pin_scan_outb, 			INPUT);
	pinMode(pin_scan_clk, 			OUTPUT);
	pinMode(pin_scan_loadb, 		OUTPUT);

	digitalWrite(pin_scan_inb, 		LOW);
	digitalWrite(pin_scan_clk, 		LOW);
	digitalWrite(pin_scan_loadb, 	HIGH);

	// - Test Structures
	pinMode(pin_pk_rst, 			OUTPUT);

	digitalWrite(pin_pk_rst, 		LOW);

	// - Chip Analog I/O
  pinMode(pin_dac_small, 		INPUT);
  pinMode(pin_dac_main, 		INPUT);
  pinMode(pin_bandgap, 			INPUT);
  pinMode(pin_pk_out, 			INPUT);
  pinMode(pin_preamp_vref,  INPUT);
  pinMode(pin_vref_atten,   INPUT);

  // - On-Chip Supply Voltages
  pinMode(pin_vddaon, 			INPUT);
  pinMode(pin_vddmain, 			INPUT);
  pinMode(pin_vddsmall, 		INPUT);

  // Resets, Enables, and the Like
  pinMode(pin_pk_rst, 			  OUTPUT);
  pinMode(pin_latch_rstb, 	  OUTPUT);
  pinMode(pin_tdc_main_en,	  OUTPUT);
  pinMode(pin_tdc_main_trig,  INPUT);
  pinMode(pin_tdc_small_en,   OUTPUT);
  pinMode(pin_tdc_small_trig, INPUT);

  digitalWrite(pin_pk_rst, 	      LOW);
  digitalWrite(pin_latch_rstb, 		HIGH);
  digitalWrite(pin_tdc_main_en,   LOW);
  digitalWrite(pin_tdc_small_en,  LOW);

  // - TDC SPI and Such
  pinMode(pin_spi_main_csb, 		OUTPUT);
  pinMode(pin_spi_main_din, 		OUTPUT);
  pinMode(pin_spi_main_dout, 		INPUT);
  pinMode(pin_spi_main_clk, 		OUTPUT);
  pinMode(pin_tdc_main_intrptb, INPUT);
  pinMode(pin_tdc_main_start,   OUTPUT);

  digitalWrite(pin_spi_main_csb,  HIGH);
  digitalWrite(pin_spi_main_din, 	LOW);
  digitalWrite(pin_spi_main_clk, 	LOW);
  digitalWrite(pin_tdc_main_start,LOW);

  pinMode(pin_spi_small_csb, 		  OUTPUT);
  pinMode(pin_spi_small_din, 		  OUTPUT);
  pinMode(pin_spi_small_dout, 	  INPUT);
  pinMode(pin_spi_small_clk, 		  OUTPUT);
  pinMode(pin_tdc_small_intrptb,  INPUT);
  pinMode(pin_tdc_small_start,    OUTPUT);

  digitalWrite(pin_spi_small_csb,   HIGH);
  digitalWrite(pin_spi_small_din,   LOW);
  digitalWrite(pin_spi_small_clk,   LOW);
  digitalWrite(pin_tdc_small_start, LOW);

  // - TDC Reference Clock
  pinMode(pin_tdc_clk,            OUTPUT);

  analogWriteFrequency(pin_tdc_clk, 3750000);
  analogWriteResolution(B_ADC);
  analogWrite(pin_tdc_clk,  1<<(B_ADC-1));

  // Setting the ADC precision
	analogReadResolution(B_ADC);	// 16B -> 13ENOB
  
} // end setup()

/* ----------------------- */
/* --- Runs repeatedly --- */
/* ----------------------- */
void loop() {
	if (stringComplete){
		if (inputString == "ascwrite\n"){
			asc_write(pin_scan_clk, pin_scan_inb);
		}
		else if (inputString == "ascread\n"){
			asc_read(pin_scan_clk, pin_scan_outb);
		}
		else if (inputString == "ascload\n"){
			asc_load(pin_scan_loadb);
		}
		else if (inputString == "tdcmainread\n") {
			tdc_read_print(pin_spi_main_csb, pin_tdc_main_en, 
			              pin_spi_main_din, pin_spi_main_dout, 
			              pin_spi_main_clk);
		}
		else if (inputString == "tdcsmallread\n") {
			tdc_read_print(pin_spi_small_csb, pin_tdc_small_en, 
                    pin_spi_small_din, pin_spi_small_dout, 
                    pin_spi_small_clk);
		}
		else if (inputString == "tdcmainconfig\n") {
			tdc_config(pin_spi_main_csb, pin_tdc_main_en, 
			          pin_spi_main_din, pin_spi_main_clk, 
			          pin_tdc_main_trig);
		}
    else if (inputString == "tdcsmallconfig\n") {
      tdc_config(pin_spi_small_csb, pin_tdc_small_en, 
                pin_spi_small_din, pin_spi_small_clk, 
                pin_tdc_small_trig);
    }
    else if (inputString == "tdcmainstart\n") {
      tdc_start(pin_tdc_main_start, pin_latch_rstb);
    }
    else if (inputString == "tdcsmallstart\n") {
      tdc_start(pin_tdc_small_start, pin_latch_rstb);  
    }
    else if (inputString == "tdcmainreset\n") {
      tdc_reset(pin_tdc_main_en);  
    }
    else if (inputString == "tdcsmallreset\n") {
      tdc_reset(pin_tdc_small_en);  
    }
		else if (inputString == "peakreset\n") {
			peak_reset(pin_pk_rst);
		}
    else if (inputString == "peakread\n") {
      peak_read(pin_pk_out);
    }
		else if (inputString == "bandgaptest\n") {
		  bandgap_test(pin_bandgap);
		}
    else if (inputString == "dacreadvddaon\n") {
      dac_read(pin_vddaon);
    }
    else if (inputString == "dacreadvddmain\n") {
      dac_read(pin_vddmain);
    }
    else if (inputString == "dacreadvddsmall\n") {
      dac_read(pin_vddsmall);
    }
    else if (inputString == "dacreadmain\n") {
      dac_read(pin_dac_main);
    }
    else if (inputString == "dacreadsmall\n") {
      dac_read(pin_dac_small);
    }
    else if (inputString == "dacreadpreamp\n") {
      dac_read(pin_preamp_vref);
    }
    else if (inputString == "attenread\n") {
      vref_read_safe(pin_vref_atten);
    }
    else if (inputString == "attenwrite\n") {
      vref_write_safe(pin_vref_atten);
    }

		// Reset to listen for a new '\n' terminated string over serial
		inputString = "";
		stringComplete = false;
	}
} // end loop()


/* ----------------- */
/* --- DAC Tests --- */
/* ----------------- */
void dac_read(int pin) {
/* 
 * Inputs:
 *  pin: Integer. Designation of the pin to analogRead.
 * Returns:
 *  None.
 * Notes:
 * Prints result in LSB over Serial.
*/
  Serial.println(analogRead(pin));
}

/* ------------------------- */
/* --- Main Signal Chain --- */
/* ------------------------- */
void vref_rw_safe(int pin_vref) {
  // Set the pin to an input
  pinMode(pin_vref, INPUT);

  // Read the voltage
  int code = analogRead(pin_vref);

  // Set the pin to an output
  pinMode(pin_vref, OUTPUT);

  // Write the voltage to the pin
  analogWrite(pin_vref, code);
}

void vref_read_safe(int pin_vref) {
/*
 * Inputs:
 * Returns:
 *  None.
 * Notes:
 *  Sets the pin to an input.
 *  Prints analogRead result in LSB over serial.
 *  Considered safe because it sets the pin to an input
 *  first.
*/
    // Set the pin to an input
    pinMode(pin_vref, INPUT);

    // Read the voltage and print over serial in LSB
    Serial.println(analogRead(pin_vref));
}

void vref_write_safe(int pin_vref) {
/*
 * Inputs:
 * Returns:
 *  None.
 * Notes:
 *  Sets the pin to an output.
 *  Writes the analog value.
*/
  // Read the target code over serial one bit at a time, MSB first
  int count = 0;
  int code = 0;
  char readbits[B_ADC];

  while (count != B_ADC) {
    if (Serial.available()) {
      readbits[count] = Serial.read();
      count ++;
    }
  }

  // Get the code into integer form
  for (int x=0; x<B_ADC; x++) {
    code = code << 1;
    if (readbits[x] == '1') {
      code += 1;
    }
  }
  
  // Set the pin to an output
  pinMode(pin_vref, OUTPUT);

  // Write the value to the pin
  analogWrite(pin_vref, code);
  Serial.println(code);
}

/* ------------- */
/* --- Other --- */
/* ------------- */
void serialEvent() {
/* 
 *  Inputs:
 *    None
 *  Returns:
 *    None
 *  Notes:
 *    SerialEvent occurs whenever new data comes in the hardware serial RX. This
 *    routine is run between each time loop() runs, so using delay inside loop
 *    can delay response. Multiple bytes of data may be available.
*/
	if (Serial.available()) {
		char inChar = (char)Serial.read();
		inputString += inChar;

		// String terminates with \n
		if (inChar == '\n') {
			stringComplete = true;
		}
	}
} // end serialEvent()
