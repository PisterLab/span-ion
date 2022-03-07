#include <InternalTemperature.h>
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
const int pin_preamp_vref   = 21;   // Preamp reference voltage

// On-chip supply voltages
const int pin_vddaon 			= A6;	  // Always-on LDO output
const int pin_vddmain			= A5;	  // Main signal chain LDO output
const int pin_vddsmall 		= A19; 	// Small signal chain LDO output

// Resets, enables, and the like
const int pin_pk_rst			= A14;	// Reset for test structure peak detector
const int pin_tdc_rstb 		= A3;	  // Reset for TDC input latch

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
const int pin_spi_small_din		  = 1; 	  // Data-in pin for the small signal chain TDC - switched on board
const int pin_spi_small_dout 	  = 0;	  // Data-out pin for the small signal chain TDC - switched on board
const int pin_spi_small_clk		  = A13;	// SPI clock for the small signal chain TDC
const int pin_tdc_small_intrptb	= 27;	  // Interrupt pin for the TDC for the small signal chain
const int pin_tdc_small_en 		  = 28;	  // Active high enable for small chain TDC
const int pin_tdc_small_trig 	  = 29;	  // Raises when TDC for small chain is ready
const int pin_tdc_small_start   = 30;   // For triggering the TDC's start pulse

const int pin_tdc_clk           = A0;   // 16MHz reference for TDC

// Constants
const int N_SCAN 				    = 44;   // Number of scan bits
const int N_TDC_CONFIG 			= 2; 	  // Number of TDC config bytes (not bits!)
const int N_TDC_DOUT 			  = 3;	  // Number of TDC data out bytes (not bits!)
const int B_ADC 				    = 16;	  // Number of bits (precision) for Teensy analogRead
const int CHAIN_MAIN			  = 0;	  // Used to indicate the main signal chain
const int CHAIN_SMALL       = 1;	  // Used to indicate the small signal chain

// Access address for the TDC
char ADDR_TDC;
const char ADDR_TIME1 = 0x10;
const char ADDR_TIME2 = 0x12;
const char ADDR_TIME3 = 0x14;
const char ADDR_TIME4 = 0x16;
const char ADDR_TIME5 = 0x18;
const char ADDR_TIME6 = 0x1A;
const char ADDR_CLOCK_COUNT1 = 0x11;
const char ADDR_CLOCK_COUNT2 = 0x13;
const char ADDR_CLOCK_COUNT3 = 0x15;
const char ADDR_CLOCK_COUNT4 = 0x17;
const char ADDR_CLOCK_COUNT5 = 0x19;
const char ADDR_CALIBRATION1 = 0x1B;
const char ADDR_CALIBRATION2 = 0x1C;

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

  // - On-Chip Supply Voltages
  pinMode(pin_vddaon, 			INPUT);
  pinMode(pin_vddmain, 			INPUT);
  pinMode(pin_vddsmall, 		INPUT);

  // Resets, Enables, and the Like
  pinMode(pin_pk_rst, 			  OUTPUT);
  pinMode(pin_tdc_rstb, 		  OUTPUT);
  pinMode(pin_tdc_main_en,	  OUTPUT);
  pinMode(pin_tdc_main_trig,  INPUT);
  pinMode(pin_tdc_small_en,   OUTPUT);
  pinMode(pin_tdc_small_trig, INPUT);

  digitalWrite(pin_pk_rst, 	      LOW);
  digitalWrite(pin_tdc_rstb, 		  HIGH);
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

  analogWriteFrequency(pin_tdc_clk, 15000000);
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
			asc_write();
		}
		else if (inputString == "ascread\n"){
			asc_read();
		}
		else if (inputString == "ascload\n"){
			asc_load();
		}
		else if (inputString == "tdcmainread\n") {
			tdc_read_meas(CHAIN_MAIN);
		}
		else if (inputString == "tdcsmallread\n") {
			tdc_read_meas(CHAIN_SMALL);
		}
		else if (inputString == "tdcmainconfig\n") {
			tdc_write(CHAIN_MAIN);
		}
    else if (inputString == "tdcsmallconfig\n") {
      tdc_write(CHAIN_SMALL);
    }
    else if (inputString == "tdcmainstart\n") {
      tdc_start(CHAIN_MAIN);
    }
    else if (inputString == "tdcsmallstart\n") {
      tdc_start(CHAIN_SMALL);  
    }
		else if (inputString == "peakreset\n") {
			peak_reset();
		}
    else if (inputString == "peakread\n") {
      peak_read();
    }
		else if (inputString == "bandgaptest\n") {
		  bandgap_test();
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
    else if (inputString == "compoffsetsmall\n") {
      comp_offset(CHAIN_SMALL);  
    }

		// Reset to listen for a new '\n' terminated string over serial
		inputString = "";
		stringComplete = false;
	}
} // end loop()

/* ------------------------- */
/* --- Analog Scan Chain --- */
/* ------------------------- */
void atick() {
/*
	10kHz clock, 50% duty cycle.
*/
	digitalWrite(pin_scan_clk, LOW);
	delayMicroseconds(100);

	// Read
	digitalWrite(pin_scan_clk, HIGH);
	delayMicroseconds(100);
} // end atick()

void asc_write() {
/*
	Writes the data into the on-chip shift register.
	NB: The inversion is handled internally! That is, if bits=000
	or bitsb=111, the input should be 000 and code here will feed in 111.
*/
	Serial.println("Executing ASC write");
	int count = 0;
	char scanbits[N_SCAN];

	// loop until all scan bits are received over serial
	while (count != N_SCAN) {
		
		// read one bit at a time over serial
		if (Serial.available()) {
			scanbits[count] = Serial.read();
			count ++;
		}
	}

	// Once all bits are received, bitbang to ASC input
	for (int x=0; x<N_SCAN; x++) {
		if (scanbits[x] == '1') {
			digitalWrite(pin_scan_inb, LOW);
		}
		else if (scanbits[x] == '0') {
			digitalWrite(pin_scan_inb, HIGH);
		}
		else {
			Serial.println("Error in ASC write");
		}

		// Pulse clock
		atick();
	}
	Serial.println("ASC write complete");
}

void asc_load() {
/*
	Latches the loaded data to the outputs of the scan chain.
	You must call asc_write() before calling this!
*/
	Serial.println("Executing ASC load");
	digitalWrite(pin_scan_loadb, LOW);
	digitalWrite(pin_scan_loadb, HIGH);
} // end asc_write()

void asc_read() {
/*
	Reads data from the single pin on the output of the scan chain. Sends
	the data (not datab) back through to the serial.
*/
	String st = "";
	int valb = 1;

	// First bit should be available
	valb = digitalRead(pin_scan_outb);
	if (valb) {
		st = String(st + "0");
	}
	else {
		st = String(st + "1");
	}

	// Send the first bit back
	Serial.print(st);
	st = "";

	// Rest of the bits
	for (int i=1; i<N_SCAN; i=i+1) {
		atick();
		valb = digitalRead(pin_scan_outb);
		if (valb) {
			st = String(st + "0");
		}
		else {
			st = String(st + "1");
		}
	}

	// Send the rest of the bits
	Serial.print(st);
	st = "";

	// Terminator
	Serial.println();
} // end asc_read()

/* ----------------------------------- */
/* --- TDC Control & Communication --- */
/* ----------------------------------- */
void spitick(int pin_clk) {
/*
*/
  digitalWrite(pin_clk, HIGH);
  delayMicroseconds(100);
  digitalWrite(pin_clk, LOW);
  delayMicroseconds(100);
} // end spitick()

void bitbang_byte_in(char msg_byte, int pin_din, int pin_clk) {
/*
 * Inputs:
 *  msg_byte: Character. Byte that's going to be sent MSB-first.
 *  pin_spi_din: Integer. Pin for SPI data-in to the other device from
 *    the Teensy.
 *  pin_spi_clk: Integer. Pin on the Teensy associated with the SPI clock.
 * Returns:
 *  None.
 * Notes:
 *  Bit-bangs the byte to the device in question, MSB-first.
*/
  for (int j=0; j<8; j++) {
    // NB: bitRead starts from the LSB
    if (bitRead(msg_byte, 7-j)) {digitalWrite(pin_din, HIGH);}
    else {digitalWrite(pin_din, LOW);}
    spitick(pin_clk);
  }
} // end bitbang_byte_in

char bitbang_byte_out(int pin_dout, int pin_clk) {
/*
 * Inputs:
 *  pin_dout: Integer. Pin on the Teensy associated with TDC data-out.
 *  pin_clk: Integer. Pin on the Teensy associated with the SPI clock.
 * Returns:
 *  Character. The byte (MSB reads out first) read out.
 * Notes:
 *  MSB comes out first.
*/  
  char msg_byte = 0;
  int valb = 0;
  
  for (int j=0; j<8; j++) {
    valb = digitalRead(pin_dout);
    if (valb) {bitSet(msg_byte, 7-j);}
    else {bitClear(msg_byte, 7-j);}
    spitick(pin_clk);
  }
  return msg_byte;
} // end bitbang_byte_out

void tdc_write(int chain) {
/*
	Bit bangs SPI communication to the TDC.
	TI TDC device documentation:
		https://www.ti.com/lit/ds/symlink/tdc7200.pdf?ts=1636125541217 

	Inputs:
		chain: CHAIN_MAIN or CHAIN_SMALL. The former indicates that
			we'd like to program the TDC associated with the 
			main signal chain; the latter indicates we'd like to 
			program the TDC associated with the small signal
			chain.
*/
	Serial.println("Executing TDC config");
 
	// get bytes (sent as bytes! MSB first) over serial
	char configbytes[N_TDC_CONFIG];
	int count = 0;
	
	// loop until all bytes are received over serial from the computer
	while (count != N_TDC_CONFIG) {
		// read one byte at a time over serial
		if (Serial.available()) {
			configbytes[count] = Serial.read();
			count ++;
		}
	}

	// select signal chain-specific SPI pins
	int pin_spi_csb;
	int pin_tdc_en;
	int pin_tdc_trig;
  int pin_spi_din;
  int pin_spi_clk;
	if (chain == CHAIN_MAIN){
		pin_spi_csb 	= pin_spi_main_csb;
		pin_tdc_en 		= pin_tdc_main_en;
		pin_tdc_trig 	= pin_tdc_main_trig;
    pin_spi_din   = pin_spi_main_din;
    pin_spi_clk   = pin_spi_main_clk;
	} else {
		pin_spi_csb 	= pin_spi_small_csb;
		pin_tdc_en 		= pin_tdc_small_en;
		pin_tdc_trig 	= pin_tdc_small_trig;
    pin_spi_din   = pin_spi_small_din;
    pin_spi_clk   = pin_spi_small_clk;
	}
	
	// bring TDC enable high if it isn't already
	digitalWrite(pin_tdc_en, HIGH);

	// enforce that it's a write
  if ((configbytes[0] | 0x40) != configbytes[0]) {
    Serial.println("WARNING: Encforcing write in TDC");
    configbytes[0] |= 0x40;
  } else {
    Serial.println("OK: TDC write setting correct");  
  }

  // enforce no auto-increment
  if (configbytes[0] >> 7) {
    Serial.println("WARNING: Enforcing no increment in TDC");
    configbytes[0] &= ~(0x1 << 7);
  } else {
    Serial.println("OK: TDC no auto-increment setting correct");  
  }
  
	// store the address being written to
	ADDR_TDC = configbytes[0] & 0x3F;

	// bit-bang over SPI to the TDC, MSB first
	digitalWrite(pin_spi_csb, LOW);
	count = 0;
  char msg_byte;
  while (count != N_TDC_CONFIG) {
    msg_byte = configbytes[count];
    bitbang_byte_in(msg_byte, pin_spi_din, pin_spi_clk);
		count ++;
	}

	// end write process to TDC
	digitalWrite(pin_spi_csb, HIGH);

	Serial.println("TDC config complete");

	// wait for indication that TDC is armed
	elapsedMillis waiting;
	while (waiting < 5000) {
		if (digitalRead(pin_tdc_trig) == HIGH) {
			// tell the computer that the TDC is armed
			Serial.println("OK: TDC armed");
			return;
		}
	}

	// if timeout, warn the computer
	Serial.println("WARNING: TDC trigger not high");
} // end tdc_write()

void tdc_read_meas(int chain) {
/*
 * Uses the Teensy's SPI library to read from the TDC
 * using the TDC's SPI interface.
 * Inputs:
 *  chain: CHAIN_MAIN or CHAIN_SMALL to indicate which
 *    communicate with. CHAIN_MAIN (the variable name)
 *    indicates that we'd like to read from the TDC
 *    that's connected to the main signal chain. CHAIN_SMALL
 *    indicates that we'd like to read from the TDC that's 
 *    connected to the small signal chain.
*/
	// select signal chain-specific SPI pins
	int pin_spi_csb;
  int pin_tdc_en;
	int pin_tdc_intrptb;
  int pin_spi_din;
  int pin_spi_dout;
  int pin_spi_clk;

  if (chain == CHAIN_MAIN){
  	pin_spi_csb 	  = pin_spi_main_csb;
    pin_tdc_en      = pin_tdc_main_en;
  	pin_tdc_intrptb = pin_tdc_main_intrptb;
    pin_spi_din     = pin_spi_main_din;
    pin_spi_dout    = pin_spi_main_dout;
    pin_spi_clk     = pin_spi_main_clk;
  } else {
		pin_spi_csb 	  = pin_spi_small_csb;
    pin_tdc_en      = pin_tdc_small_en;
		pin_tdc_intrptb	= pin_tdc_small_intrptb;
    pin_spi_din     = pin_spi_small_din;
    pin_spi_dout    = pin_spi_small_dout;
    pin_spi_clk     = pin_spi_small_clk;
	}

	// wait until interrupt indicates measurement data is available
	elapsedMillis waiting;
	bool meas_done = false;
	while (waiting < 1000 && !meas_done) {
		meas_done = !digitalRead(pin_tdc_intrptb); // TODO check correctness
	}

	// if TDC measurement isn't ready within allocated time, everything is 0
	if (!meas_done) {
    for (int i=0; i<13; i++) {Serial.write(0);}
	} else {
  	// read from all timer outputs
    int count;
    char dout[N_TDC_DOUT];
    digitalWrite(pin_tdc_en, HIGH);
  	digitalWrite(pin_spi_csb, LOW);
    char addr_time_vec[6] = {ADDR_TIME1, ADDR_TIME2, 
                            ADDR_TIME3, ADDR_TIME4,
                            ADDR_TIME5, ADDR_TIME6};
    char msg_byte;
    for (int i=0; i<6; i++) {
      // send read command, enforce no auto-increment
      msg_byte = addr_time_vec[i];
      bitbang_byte_in(msg_byte, pin_spi_din, pin_spi_clk);
  
      // retrieve data from the TDC
      count = 0;
      while (count != N_TDC_DOUT) {
        // read and write one byte at a time over SPI and then serial
        dout[count] = bitbang_byte_out(pin_spi_dout, pin_spi_clk);
        Serial.write(dout[count]);
        count ++;
      }
    }
  
    // read from all clock count outputs
    char addr_clkcount_vec[5] = {ADDR_CLOCK_COUNT1, 
                                ADDR_CLOCK_COUNT2, 
                                ADDR_CLOCK_COUNT3, 
                                ADDR_CLOCK_COUNT4, 
                                ADDR_CLOCK_COUNT5};
    for (int i=0; i<5; i++) {
      // send read command, enforce no auto-increment
      msg_byte = addr_clkcount_vec[i];
      bitbang_byte_in(msg_byte, pin_spi_din, pin_spi_clk);
  
      // retrieve data from the TDC
      count = 0;
      while (count != N_TDC_DOUT) {
        // read and write one byte at a time over SPI and then serial
        dout[count] = bitbang_byte_out(pin_spi_dout, pin_spi_clk);
        Serial.write(dout[count]);
        count ++;
      }
    }
  
    // read from calibration count outputs
    char addr_cal_vec[2] = {ADDR_CALIBRATION1, ADDR_CALIBRATION2};
    for (int i=0; i<2; i++) {
      digitalWrite(pin_spi_csb, LOW);
      // send read command, enforce no auto-increment
      msg_byte = addr_cal_vec[i];
      bitbang_byte_in(msg_byte, pin_spi_din, pin_spi_clk);
  
      // retrieve data from the TDC
      count = 0;
      while (count != N_TDC_DOUT) {
        dout[count] = bitbang_byte_out(pin_spi_dout, pin_spi_clk);
        Serial.write(dout[count]);
        count ++;
      }
    }
  
  	// end read process from TDC
    digitalWrite(pin_spi_csb, HIGH);
  
  	// terminator
  	Serial.println("TDC read complete");
  }
} // end tdc_read_meas()

void tdc_start(int chain) {
/* 
 * Inputs:
 *  chain: CHAIN_MAIN or CHAIN_SMALL. The former indicates that
 *    we'd like to program the TDC associated with the 
 *    main signal chain; the latter indicates we'd like to 
 *    program the TDC associated with the small signal
 *    chain.
 * Returns:
 *  None.
*/
  // Figure out which pin to toggle based on the signal chain
  int pin_start;
  if (chain == CHAIN_MAIN) {
    pin_start = pin_tdc_main_start;
  } else if (chain == CHAIN_SMALL) {
    pin_start = pin_tdc_small_start;
  } else {
    pin_start = pin_tdc_main_start;
  }

  // Toggle the pin high then low
  digitalWrite(pin_start, HIGH);
  delayMicroseconds(100);
  digitalWrite(pin_start, LOW);
} // end tdc_start


/* ------------------------------------------ */
/* --- On-Chip Test Structure Interaction --- */
/* ------------------------------------------ */
void peak_reset() {
/* 
 *  Resets the test structure peak detector.
*/
	digitalWrite(pin_pk_rst, HIGH);
	delayMicroseconds(100);
	digitalWrite(pin_pk_rst, LOW);
  delayMicroseconds(500);
}

void peak_read() {
/*
 * Inputs:
 *  None.
 * Returns:
 *  None.
 * Notes:
 *  Reads the output voltage of the test peak detector and
 *  prints over serial the output _in LSB_.
*/
  Serial.println(analogRead(pin_pk_out));
}

/* ------------------------------------------ */
/* --- Temperature vs Bandgap Voltage Test --- */
/* ------------------------------------------ */
void bandgap_test() {
/*
 * Inputs:
 *  None.
 * Returns:
 *  None.
 * Notes:
 *  Prints the internal temperature (in Celsius) of the Teensy over 
 *  serial and measures (and prints over serial) the measured 
 *  bandgap voltage _in LSB_.
*/
    // Temperature reading
    InternalTemperature.begin(TEMPERATURE_NO_ADC_SETTING_CHANGES);
    Serial.println(InternalTemperature.readTemperatureC());

    // Bandgap voltage reading (in LSB!!)
    Serial.println(analogRead(pin_bandgap));
} // end bandgap_test()

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

/* --------------------------------- */
/* --- Signal Chain Measurements --- */
/* --------------------------------- */
void comp_offset(int ) {
  
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
