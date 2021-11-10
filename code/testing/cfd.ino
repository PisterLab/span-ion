#include <SPI.h> // include the SPI library
/* --------------------------------- */
/* --- Pin Mappings (Teensy 3.6) --- */
/* --------------------------------- */
// Analog scan chain
const int pin_scan_inb 			= A15;	// ASC input data
const int pin_scan_outb 		= A18;	// ASC output data
const int pin_scan_clk 			= A17;	// ASC clock
const int pin_scan_loadb 		= A16;	// ASC load

// Analog I/O signal voltages
const int pin_dac_small 		= A0; 	// Resistive DAC for small chain
const int pin_dac_main 			= A0;	// Resistive DAC for main chain
const int pin_bandgap			= A0;	// Test structure bandgap voltage source
const int pin_pk_out 			= A0; 	// Peak detector output voltage

// On-chip supply voltages
const int pin_vddaon 			= A0;	// Always-on LDO output
const int pin_vddmain			= A0;	// Main signal chain LDO output
const int pin_vddsmall 			= A0; 	// Small signal chain LDO output

// Resets, enables, and the like
const int pin_pk_rst			= A14;	// Reset for test structure peak detector
const int pin_tdc_rstb 			= A3;	// Reset for TDC input latch

// TDC SPI and other connections
// TODO Don't worry about how these are all currently A0
// What matters is the names on the left side
const int pin_spi_main_csb 		= A0;	// CSb for the main signal chain TDC
const int pin_spi_main_din		= A0; 	// Data-in pin for the main signal chain TDC
const int pin_spi_main_dout 	= A0;	// Data-out pin for the main signal chain TDC
const int pin_spi_main_clk		= A0;	// SPI clock for the main signal chain TDC
const int pin_tdc_main_intrptb	= A0;	// Interrupt pin for the TDC for the main signal chain
const int pin_tdc_main_en 		= A0;	// Active high enable for main chain TDC
const int pin_tdc_main_trig		= A0; 	// Raises when TDC for main chain is ready

const int pin_spi_small_csb 	= A0;	// CSb for the small signal chain TDC
const int pin_spi_small_din		= A0; 	// Data-in pin for the small signal chain TDC
const int pin_spi_small_dout 	= A0;	// Data-out pin for the small signal chain TDC
const int pin_spi_small_clk		= A0;	// SPI clock for the small signal chain TDC
const int pin_tdc_small_intrptb	= A0;	// Interrupt pin for the TDC for the small signal chain
const int pin_tdc_small_en 		= A0;	// Active high enable for small chain TDC
const int pin_tdc_small_trig 	= A0;	// Raises when TDC for small chainis ready

// Constants
const int N_SCAN 				= 44; 	// Number of scan bits
const int N_TDC_CONFIG 			= 2; 	// Number of TDC config bytes (not bits!)
const int N_TDC_DOUT 			= 1;	// Number of TDC data out bytes (not bits!)
const int B_ADC 				= 16;	// Number of bits for Teensy analogRead
const int CHAIN_MAIN			= 0;	// Used to indicate the main signal chain
const int CHAIN_SMALL			= 1;	// Used to indicate the small signal chain

// Access address for the TDC
char ADDR_TDC;

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
	pinMode(pin_rst_test, 			OUTPUT);

	digitalWrite(pin_rst_test, 		LOW);

	// - Chip Analog I/O
    pinMode(pin_dac_small, 			INPUT);
    pinMode(pin_dac_main, 			INPUT);
    pinMode(pin_bandgap, 			INPUT);
    pinMode(pin_pk_out, 			INPUT);

    // - On-Chip Supply Voltages
    pinMode(pin_vddaon, 			INPUT);
    pinMode(pin_vddmain, 			INPUT);
    pinMode(pin_vddsmall, 			INPUT);

    // Resets, Enables, and the Like
    pinMode(pin_pk_rst, 			OUTPUT);
    pinMode(pin_tdc_rstb, 			OUTPUT);
    pinMode(pin_tdc_main_en,		OUTPUT);
    pinMode(pin_tdc_main_trig, 		INPUT);
    pinMode(pin_tdc_small_en, 		OUTPUT);
    pinMode(pin_tdc_small_trig, 	INPUT);

    digitalWrite(pin_pk_rst, 	    LOW);
    digitalWrite(pin_tdc_rstb, 		HIGH);
    digitalWrite(pin_tdc_main_en, 	LOW);
    digitalWrite(pin_tdc_small_en, 	LOW);

    // - SPI
    pinMode(pin_spi_main_csb, 		OUTPUT);
    pinMode(pin_spi_main_din, 		OUTPUT);
    pinMode(pin_spi_main_dout, 		INPUT);
    pinMode(pin_spi_main_clk, 		OUTPUT);
    pinMode(pin_tdc_main_intrptb, 	INPUT);

    digitalWrite(pin_spi_main_csb,  HIGH);
    digitalWrite(pin_spi_main_din, 	LOW);
    digitalWrite(pin_spi_main_clk, 	LOW);

    pinMode(pin_spi_small_csb, 		OUTPUT);
    pinMode(pin_spi_small_din, 		OUTPUT);
    pinMode(pin_spi_small_dout, 	INPUT);
    pinMode(pin_spi_small_clk, 		OUTPUT);
    pinMode(pin_tdc_small_intrptb, 	INPUT);

    digitalWrite(pin_spi_small_csb, HIGH);
    digitalWrite(pin_spi_small_din, LOW);
    digitalWrite(pin_spi_small_clk, LOW);

	analogReadResolution(16);	// 16B -> 13ENOB

	// Initialize SPI speed, mode, and endianness
	SPI.begin();
	SPISettings settings_tdc_spi(16000000, MSBFIRST, SPI_MODE1);

	// TODO for Lydia: enable 16MHz clock for TDC reference
}

/* ----------------------- */
/* --- Runs repeatedly --- */
/* ----------------------- */
void loop() {
	if (stringComplete){
		if (inputString == 'ascwrite\n'){
			asc_write();
		}
		else if (inputString == 'ascread\n'){
			asc_read();
		}
		else if (inputString == 'ascload\n'){
			asc_load();
		}
		else if (inputString == 'tdcmainread\n') {
			tdc_read(CHAIN_MAIN);
		}
		else if (inputString == 'tdcsmallread\n') {
			tdc_read(CHAIN_SMALL);
		}
		else if (inputString == 'tdcconfig\n') {
			tdc_write();
		}
		else if (inputString == 'peakreset\n') {
			peak_reset();
		}

		// Reset to listen for a new '\n' terminated string over serial
		inputString = "";
		stringComplete = false;
	}
}

/* ------------------------- */
/* --- Analog Scan Chain --- */
/* ------------------------- */
void atick() {
/*
	10kHz clock, 50% duty cycle.
*/
	digitalWrite(pin_scan_clk, LOW);
	delayMicroseconds(50);

	// Read
	digitalWrite(pin_scan_clk, HIGH);
	delayMicroseconds(50);
}

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
}

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
	for (int i=1; i<N_bits; i=i+1) {
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
}

/* ----------------------------------- */
/* --- TDC Control & Communication --- */
/* ----------------------------------- */
void tdc_write(int chain) {
/*
	Uses the Teensy' SPI library to program the TDC using
	the TDC's SPI interface.
	SPI library documentation:
		https://www.pjrc.com/teensy/td_libs_SPI.html
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

	// get bytes (sent as bytes!) over serial
	char configbytes[N_TDC_CONFIG];
	int count = 0;
	
	// loop until all bytes are received over serial from the computer
	while (count != N_TDC_CONFIG*sizeof(char)) {
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
	if (chain == CHAIN_MAIN){
		pin_spi_csb 	= pin_spi_main_csb;
		pin_tdc_en 		= pin_tdc_main_en;
		pin_tdc_trig 	= pin_tdc_main_trig;
	    SPI.setMOSI	(pin_spi_main_din); 		// TODO check
	    SPI.setSCK	(pin_spi_main_clk);
	} else {
		pin_spi_csb 	= pin_spi_small_csb;
		pin_tdc_en 		= pin_tdc_small_en;
		pin_tdc_trig 	= pin_tdc_small_trig;
	    SPI.setMOSI	(pin_spi_small_din); 		// TODO check
	    SPI.setSCK	(pin_spi_small_clk);
	}
	
	// bring TDC enable high if it isn't already
	digitalWrite(pin_tdc_en, HIGH);

	// enforce no auto-increment and that it's a write
	configbytes[0] |= 0xC00;

	// store the address being written to for later
	ADDR_TDC = configbytes[0] & ~0xC00;

	// forward bytes to the TDC 
	digitalWrite(pin_spi_csb, LOW);
	SPI.beginTransaction(settings_tdc_spi);
	count = 0;
    while (count != N_TDC_CONFIG) {
		// transfer one byte at a time over SPI
		SPI.transfer(configbytes[count]);
		count ++;
	}

	// end write process to TDC
	digitalWrite(pin_spi_csb, HIGH);
    SPI.endTransaction();

	Serial.println("TDC config complete");

	// wait for indication that TDC is armed
	elapsedMillis waiting;
	while (waiting < 1000) {
		if (digitalRead(pin_tdc_trig)) {
			// tell the computer that the TDC is armed
			Serial.println("TDC armed");
			return;
		}
	}

	// if timeout, warn the computer
	Serial.println("TDC trigger not armed");
}


void tdc_read(int chain) {
/*
	Uses the Teensy's SPI library to read from the TDC
	using the TDC's SPI interface.

	Inputs:
		chain: CHAIN_MAIN or CHAIN_SMALL to indicate which
			TDC to communicate with. CHAIN_MAIN (the variable name)
			indicates that we'd like to read from the TDC
			that's connected to the main signal chain. CHAIN_SMALL
			indicates that we'd like to read from the TDC that's 
			connected to the small signal chain.
*/
	// select signal chain-specific SPI pins
	int pin_spi_csb;
	int pin_tdc_intrptb;

    if (chain = CHAIN_MAIN){
    	pin_spi_csb 	= pin_spi_main_csb;
    	pin_tdc_intrptb = pin_tdc_main_intrptb;
    	SPI.setMISO (pin_spi_main_dout);		// TODO check
    	SPI.setSCK	(pin_spi_main_clk);
	} else {
		pin_spi_csb 	= pin_spi_small_csb;
		pin_tdc_intrptb	= pin_tdc_small_intrptb;
		SPI.setmISO (pin_spi_small_dout);		// TODO check
		SPI.setSCK (pin_spi_small_clk);
	}

	// wait until interrupt indicates measurement data is available
	elapsedMillis waiting;
	bool meas_done = false;
	while (waiting < 100 && !meas_done) {
		meas_done = !digitalRead(pin_tdc_intrptb); // TODO check correctness
	}

	// warn if TDC measurement isn't ready within allocated time
	if not meas_done {
		Serial.println("TDC interrupt wait timed out.");
		return;
	}

	// send read command (no auto-increment, read)
	digitalWrite(pin_spi_csb, LOW);
	SPI.transfer(0x80 |= ADDR_TDC);

	// retrieve the bits from the TDC
	int count = 0;
    char val[N_TDC_DOUT];
    while (count != N_TDC_DOUT) {

		// read one byte at a time over SPI
		val[count] = SPI.transfer(0);
		count ++;
	}

	// end read process from TDC
	digitalWrite(pin_spi_csb, HIGH);
    SPI.endTransaction();

	// forward the data byte(s) to the computer over serial
	count = 0;
    while (count != N_TDC_DOUT) {
		Serial.write(val[count]);
		count ++;
	}

	// terminator
	Serial.println("TDC read complete")
}


/* ------------------------------------------ */
/* --- On-Chip Test Structure Interaction --- */
/* ------------------------------------------ */
void peak_reset() {
/* 
	Resets the test structure peak detector
*/
	digitalWrite(pin_rst_test, HIGH);
	delayMicroseconds(50);
	digitalWrite(pin_rst_time, LOW);
}


/* ------------- */
/* --- Other --- */
/* ------------- */
void serialEvent() {
/* 
	SerialEvent occurs whenever new data comes in the hardware serial RX. This
	routine is run between each time loop() runs, so using delay inside loop
	can delay response. Multiple bytes of data may be available.
*/
	if (Serial.available()) {
		char inChar = (char)Serial.read();
		inputString += inChar;

		// String terminates with \n
		if (inChar == '\n') {
			stringComplete = true;
		}
	}
}
