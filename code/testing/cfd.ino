/* --------------------------------- */
/* --- Pin Mappings (Teensy 3.6) --- */
/* --------------------------------- */
// TODO Teensy pinout
const int pin_scan_inb 		= 0;	// ASC input data
const int pin_scan_outb 	= 0;	// ASC output data
const int pin_scan_clk 		= 0;	// ASC clock
const int pin_scan_loadb 	= 0;	// ASC load

const int pin_rst_test		= 0;	// Reset for test structure peak detector

const int pin_rst_time 		= 0;	// Reset ramp for TAC
const int pin_rstb_time 	= 0;	// Inverted reset ramp for TAC
const int pin_tac_main 		= 0;	// TAC output for full signal chain
const int pin_tac_small		= 0;	// TAC output for small signal chain

const int N_SCAN 	= 44; 			// Number of scan bits; DO NOT MODIFY
const int B_ADC 	= 16;			// Number of bits for analogRead; DO NOT MOD

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

	// - Time-to-Analog Converters
	pinMode(pin_rst_time,			OUTPUT);
	pinMode(pin_rstb_time,			OUTPUT);
	pinMode(pin_tac_main, 			INPUT);
	pinMode(pin_tac_small, 			INPUT);

	digitalWrite(pin_rst_time, 		LOW);
	digitalWrite(pin_rstb_time, 	HIGH);
	analogReadResolution(16);	// 16B -> 13ENOB
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
		else if (inputString == 'tacmainread\n') {
			tac_main_read();
		}
		else if (inputString == 'tacsmallread\n') {
			tac_small_read();
		}
		else if (inputString == 'tacreset\n') {
			tac_reset();
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
	NB: The inversion is handled internally! That is, if  bits=000
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
/* -------------------------------------------- */
/* --- Time-to-Analog Converter Interaction --- */
/* -------------------------------------------- */
void tac_main_read() {
/*
	Reads from the time-to-analog converter for the full signal chain
	using the Teensy's DAC. Prints a digital code to Serial.
*/
	analogReadResolution(B_adc);
	Serial.println(analogRead(pin_tac_main));
}

void tac_reset() {
/* 
	Resets the time-to-analog converters by raising rst and dropping rstb.
*/
	digitalWrite(pin_rst_time, 	HIGH);
	digitalWrite(pin_rstb_time, LOW);

	delayMicroseconds(50);

	digitalWrite(pin_rst_time, 	LOW);
	digitalWrite(pin_rstb_time, HIGH);

	delayMicroseconds(50);
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