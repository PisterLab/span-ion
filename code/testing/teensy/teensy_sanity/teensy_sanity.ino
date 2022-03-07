#include <InternalTemperature.h> // include the InternalTemperature library
/* --------------------------------- */
/* --- Pin Mappings (Teensy 3.6) --- */
/* --------------------------------- */
// Analog scan chain
const int pin_scan_inb      = A15;  // ASC input data
const int pin_scan_outb     = A18;  // ASC output data
const int pin_scan_clk      = A17;  // ASC clock
const int pin_scan_loadb    = A16;  // ASC load

// Miscellaneous analogRead/Write-enabled pin
const int pin_dac1 = A22;
const int pin_dac0 = A21;

// TDC SPI and other connections
const int pin_spi_main_csb       = 10; // CSb for the main signal chain TDC
const int pin_spi_main_din      = 11; // Data-in pin for the main signal chain TDC
const int pin_spi_main_dout     = 12; // Data-out pin for the main signal chain TDC
const int pin_spi_main_clk      = 13; // SPI clock for the main signal chain TDC
const int pin_tdc_main_intrptb  = 9;  // Interrupt pin for the TDC for the main signal chain
const int pin_tdc_main_en       = 8;  // Active high enable for main chain TDC
const int pin_tdc_main_trig     = 7;  // Raises when TDC for main chain is ready
const int pin_tdc_main_start    = 6;  // For triggering the TDC's start pulse

const int pin_spi_small_csb     = A12;  // CSb for the small signal chain TDC
const int pin_spi_small_din     = 0;    // Data-in pin for the small signal chain TDC
const int pin_spi_small_dout    = 1;    // Data-out pin for the small signal chain TDC
const int pin_spi_small_clk     = A13;  // SPI clock for the small signal chain TDC
const int pin_tdc_small_intrptb = 27;   // Interrupt pin for the TDC for the small signal chain
const int pin_tdc_small_en      = 28;   // Active high enable for small chain TDC
const int pin_tdc_small_trig    = 29;   // Raises when TDC for small chain is ready
const int pin_tdc_small_start   = 30;   // For triggering the TDC's start pulse

// For getting a reference clock
const int pin_clk_ref = 14;

// Constants
const int B_ADC             = 16;   // Resolution for ADC read/write
const int CHAIN_MAIN        = 0;    // Used to indicate the main signal chain
const int CHAIN_SMALL       = 1;    // Used to indicate the small signal chain

void setup() {
  analogReadResolution(B_ADC);  // 16B -> 13ENOB
  analogWriteResolution(B_ADC); // 16B -> 13ENOB?
  
  pinMode(pin_scan_inb,       OUTPUT);
  pinMode(pin_scan_outb,      INPUT);
  pinMode(pin_scan_clk,       OUTPUT);
  pinMode(pin_scan_loadb,     OUTPUT);

  digitalWrite(pin_scan_inb,    LOW);
  digitalWrite(pin_scan_clk,    LOW);
  digitalWrite(pin_scan_loadb,  HIGH);

  pinMode(pin_dac1,         OUTPUT);
  pinMode(pin_dac0,         OUTPUT);
  
  analogWrite(pin_dac1,     1<<B_ADC);
  analogWrite(pin_dac0,     1<<(B_ADC-1));

  pinMode(pin_spi_main_csb,     OUTPUT);
  pinMode(pin_spi_main_din,     OUTPUT);
  pinMode(pin_spi_main_dout,    INPUT);
  pinMode(pin_spi_main_clk,     OUTPUT);
  pinMode(pin_tdc_main_intrptb, INPUT);
  pinMode(pin_tdc_main_en,      OUTPUT);
  pinMode(pin_tdc_main_trig,    INPUT);
  pinMode(pin_tdc_main_start,   OUTPUT);

  analogWrite(pin_spi_main_csb,   HIGH);
  analogWrite(pin_spi_main_din,   LOW);
  analogWrite(pin_spi_main_clk,   LOW);
  analogWrite(pin_tdc_main_en,    LOW);
  analogWrite(pin_tdc_main_start, LOW);

  pinMode(pin_spi_small_csb,     OUTPUT);
  pinMode(pin_spi_small_din,     OUTPUT);
  pinMode(pin_spi_small_dout,    INPUT);
  pinMode(pin_spi_small_clk,     OUTPUT);
  pinMode(pin_tdc_small_intrptb, INPUT);
  pinMode(pin_tdc_small_en,      OUTPUT);
  pinMode(pin_tdc_small_trig,    INPUT);
  pinMode(pin_tdc_small_start,   OUTPUT);

  analogWrite(pin_spi_small_csb,   HIGH);
  analogWrite(pin_spi_small_din,   LOW);
  analogWrite(pin_spi_small_clk,   LOW);
  analogWrite(pin_tdc_small_en,    LOW);
  analogWrite(pin_tdc_small_start, LOW);

//  Gets the 16MHz clock out from pin 9
//  SIM_SOPT2 = (SIM_SOPT2 & ~0xE0) | 0xC0;
//  OSC0_CR |= 0x80;
//  CORE_PIN9_CONFIG = PORT_PCR_MUX(0); // PTC3

  analogWriteFrequency(pin_clk_ref, 8000000);
  pinMode(pin_clk_ref, OUTPUT);
  analogWrite(pin_clk_ref, 1<<(B_ADC-1));

}

void loop() {
  // --- Level Shifter Function Check ---
  if (false) {
    int pin_arr[] = {pin_scan_inb, pin_scan_clk, pin_scan_loadb};
    check_levelshift(pin_arr, sizeof(pin_arr)/sizeof(int));
  }

  // --- Teensy Internal Temp Sensor ---
  if (false) {
    check_internalTemp();
  }

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
}

void check_levelshift(int pin_arr[], int num_pins) {
/*
 * Inputs:
 *  pin_arr: Array of ints. The ints are the pins to toggle.
 *  num_pins: Number of elements in pin_arr.
 * Notes:
 *  - Toggles the pins connected to the level shifter for testing
 *    the on-board level shifter.
 *  - Period is 100us, duty cycle nominally 50%.
 *  - Requires manually probing the outputs (and inputs) 
 *    of the level shifter.
*/
  int pin_idx;
  for (int i=0; i<num_pins; i++) {
    pin_idx = pin_arr[i];
    if (digitalRead(pin_idx)) {digitalWrite(pin_idx, LOW);}
    else {digitalWrite(pin_idx, HIGH);}
  }
  delayMicroseconds(50);
}

void check_internalTemp() {
/*  
 * Inputs:
 *  None.
 * Returns:
 *  None.
 * Notes:
 *  - Reads the internal temperature temperature from the Teensy and 
 *    prints it over serial. Recommend .decode() on the receiving side
*/
  for (int i=0; i<100; i++) {
    Serial.println(InternalTemperature.readTemperatureC());
  }
}

void tdc_write_reg(int chain, char addr) {
/*
 * Inputs:
 *  chain: The signal chain (CHAIN_MAIN vs. CHAIN_SMALL)
 *    to test.
 *  addr: Byte. The address of the register to write to.
 * Returns:
 *  None.
 * Notes:
 *  Unfinished. Do not use.
*/
  // select signal chain-specific SPI pins
  int pin_spi_csb;
  int pin_tdc_en;
  int pin_spi_din;
  int pin_spi_dout;
  int pin_spi_clk;

  if (chain == CHAIN_MAIN){
    pin_spi_csb     = pin_spi_main_csb;
    pin_tdc_en      = pin_tdc_main_en;
    pin_spi_din     = pin_spi_main_din;
    pin_spi_dout    = pin_spi_main_dout;
    pin_spi_clk     = pin_spi_main_clk;
  } else {
    pin_spi_csb     = pin_spi_small_csb;
    pin_tdc_en      = pin_tdc_small_en;
    pin_spi_din     = pin_spi_small_din;
    pin_spi_dout    = pin_spi_small_dout;
    pin_spi_clk     = pin_spi_small_clk;
  }

  // Sending the write command
  digitalWrite(pin_tdc_en, HIGH);
  digitalWrite(pin_spi_csb, LOW);
  char msg_in = 0x40 | addr;
  int val;
  char msg_out = 0;

  for (int j=0; j<8; j++) {
    // Bitbang the write command
    if (bitRead(msg_in, 7-j)) {digitalWrite(pin_spi_din, HIGH);}
    else {digitalWrite(pin_spi_din, LOW);}

    digitalWrite(pin_spi_clk, HIGH);
    delayMicroseconds(100);

    // dout should lag din for write commands by half a clock cycle
    val = digitalRead(pin_spi_dout);
    if (val) {bitSet(msg_out, 7-j);}
    else {bitClear(msg_out, 7-j);

    digitalWrite(pin_spi_clk, LOW);
    delayMicroseconds(100);
    }
  }
  Serial.println(addr, HEX);
  Serial.println(msg_in, BIN);
  Serial.println(msg_out, HEX);
  Serial.println("----");
} // end tdc_write_reg

void tdc_read_reg(int chain, char addr) {
/*
 * Inputs:
 *  chain: The signal chain (CHAIN_MAIN vs. CHAIN_SMALL)
 *    to test.
 *  addr: Byte. The address of the register to write to.
 * Returns:
 *  None.
 * Notes:
 *  - Sets all TDC registers to default values by toggling
 *    the TDC reset pin (tdc_en), then reads from the registers
 *    which have a single byte of data.
 *  - Prints the following over serial in this order:
 *    (1) Address
 *    (2) The bits banged over SPI to to the TDC
 *    (3) The byte of data read out from the TDC
 *    (4) A separating line to make things easier to read
 *  - See Table 1 (https://www.ti.com/lit/ds/symlink/tdc7200.pdf) 
 *    "Register Summary" for the expected values from each of the registers.
*/
  // select signal chain-specific SPI pins
  int pin_spi_csb;
  int pin_tdc_en;
  int pin_spi_din;
  int pin_spi_dout;
  int pin_spi_clk;

  if (chain == CHAIN_MAIN){
    pin_spi_csb     = pin_spi_main_csb;
    pin_tdc_en      = pin_tdc_main_en;
    pin_spi_din     = pin_spi_main_din;
    pin_spi_dout    = pin_spi_main_dout;
    pin_spi_clk     = pin_spi_main_clk;
  } else {
    pin_spi_csb     = pin_spi_small_csb;
    pin_tdc_en      = pin_tdc_small_en;
    pin_spi_din     = pin_spi_small_din;
    pin_spi_dout    = pin_spi_small_dout;
    pin_spi_clk     = pin_spi_small_clk;
  }

  // Reset the register values to defaults
  digitalWrite(pin_tdc_en, LOW);
  digitalWrite(pin_tdc_en,  HIGH);
  
  // Send read command, enforce no auto-increment
  digitalWrite(pin_spi_csb, LOW);
  char msg_byte = addr;
  bitbang_byte_in(msg_byte, pin_spi_din, pin_spi_clk);
  
  // Retrieve one byte of data from the TDC
  char dout;
  dout = bitbang_byte_out(pin_spi_dout, pin_spi_clk);
  digitalWrite(pin_spi_csb, HIGH);

  Serial.println(addr, HEX);
  Serial.println(msg_byte, HEX);
  Serial.println(dout, HEX);
  Serial.println("---");
} // end tdc_read_reg

void tdc_rw_reg(int chain) {
/*
 * Inputs:
 *  chain: The signal chain (CHAIN_MAIN vs. CHAIN_SMALL)
 *    to test.
 * Returns:
 *  None.
 * Notes:
 *  - Writes data 0x00 -> 0xFF to each single-byte register in the TDC,
 *    then reads the data from the same register right after.
 *  - Prints the following over serial in this order:
 *    (1) The write command byte
 *    (2) The read command byte--it should only differ from the write
 *        command byte by 0x40
 *    (3) The data written to the register
 *    (4) The data read out from the register; it should match the data
 *        written to the register.
 *    (5) A separating line to make things easier to read
*/
  // select signal chain-specific SPI pins
  int pin_spi_csb;
  int pin_tdc_en;
  int pin_spi_din;
  int pin_spi_dout;
  int pin_spi_clk;

  if (chain == CHAIN_MAIN){
    pin_spi_csb     = pin_spi_main_csb;
    pin_tdc_en      = pin_tdc_main_en;
    pin_spi_din     = pin_spi_main_din;
    pin_spi_dout    = pin_spi_main_dout;
    pin_spi_clk     = pin_spi_main_clk;
  } else {
    pin_spi_csb     = pin_spi_small_csb;
    pin_tdc_en      = pin_tdc_small_en;
    pin_spi_din     = pin_spi_small_din;
    pin_spi_dout    = pin_spi_small_dout;
    pin_spi_clk     = pin_spi_small_clk;
  }
  char msg_read;
  char msg_write;
  char dout;

  // Reset the register values to defaults
  digitalWrite(pin_tdc_en, LOW);
  digitalWrite(pin_tdc_en,  HIGH);
  
  for (char addr=0; addr<0x0A; addr++) {
    for (char din=0x00; din<0xFF; din++) {
      digitalWrite(pin_spi_csb, LOW);
  
      // Send write command, enforce no auto-increment
      msg_write = 0x40 | addr;
      bitbang_byte_in(msg_write, pin_spi_din, pin_spi_clk);

      // Send write data
      bitbang_byte_in(din, pin_spi_din, pin_spi_clk);

      digitalWrite(pin_spi_csb, HIGH);
      delayMicroseconds(100);
      digitalWrite(pin_spi_csb, LOW);
  
      // Send read command for same register, enforce no auto-increment
      msg_read = addr;
      bitbang_byte_in(msg_read, pin_spi_din, pin_spi_clk);
      
      // Retrieve read data
      dout = bitbang_byte_out(pin_spi_dout, pin_spi_clk);
      digitalWrite(pin_spi_csb, HIGH);
  
      Serial.println(msg_write, HEX);
      Serial.println(msg_read, HEX);
      Serial.println(din, HEX);
      Serial.println(dout, HEX);
      Serial.println("-------");
    }
  }
  digitalWrite(pin_tdc_en, LOW);
  
}

void spitick(int pin_clk) {
/*
*/
  delayMicroseconds(100);
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
