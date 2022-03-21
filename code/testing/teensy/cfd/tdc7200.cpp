/*
 * This is code meant for interfacing with the Texas Instruments TDC7200.
 * https://www.ti.com/lit/ds/symlink/tdc7200.pdf
*/
#include <Arduino.h>

// Register addresses
const char ADDR_CONFIG1 = 0x00;
const char ADDR_CONFIG2 = 0x01;
const char ADDR_INT_STATUS = 0x02;
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

/* ----------------------- */
/* --- SPI Bit-Banging --- */
/* ----------------------- */
void spitick(int pin_clk) {
/*
 * Inputs:
 *  pin_clk: Integer. Number of the pin 
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
} // end bitbang_byte_in()

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
} // end bitbang_byte_out()

/* ---------------------------------------- */
/* --- Status Checking in Register Data --- */
/* ---------------------------------------- */
bool trigg_fall(char config1) {
/*
 * Inputs:
 *  config1: 1 byte of the CONFIG1 register data.
 * Returns:
 *  True if the TRIG is output as a falling edge signal,
 *    False if it's output as a rising edge signal.
*/
  return bitRead(config1, 5);
} // end trigg_fall()

bool stop_fall(char config1) {
/*
 * Inputs:
 *  config1: 1 byte of the CONFIG1 register data.
 * Returns:
 *  True if the measurement is stopped on the falling edge
 *    of the STOP signal, False if it stops on the rising edge.
*/
  return bitRead(config1, 4);
} // end stop_fall()

bool start_fall(char config1) {
/*
 * Inputs:
 *  config1: 1 byte of the CONFIG1 register data.
 * Returns:
 *  True if the START pulse is meant to be read as a falling
 *    edge, False if it's meant to be read as a rising edge.
*/
  return bitRead(config1, 3);
} // end start_fall()

bool is_done(char int_status) {
/*
 * Inputs:
 *  int_status: 1 byte of the INT_STATUS register data.
 * Returns:
 *  True if the measurement is done, False otherwise.
*/
  return bitRead(int_status, 0);
} // end is_done()

bool is_overflow_clk(char int_status) {
/*
 * Inputs:
 *  int_status: 1 byte of the INT_STATUS register data.
 * Returns:
 *  True if clock overflow is detected, False otherwise.
*/
  return bitRead(int_status, 2);
} // end is_overflow_clk ()

bool is_overflow_coarse(char int_status) {
/*
 * Inputs:
 *  int_status: 1 byte of the INT_STATUS register data.
 * Returns:
 *  True if coarse overflow is detected, False otherwise.
*/
  return bitRead(int_status, 1);
} // end is_overflow_coarse()

char get_addr(char cmd) {
/*
 * Inputs:
 *  cmd: 1 byte intended as the first byte when communicating with the 
 *    TDC over SPI. See Figure 21 in TDC7200 documentation.
 * Returns:
 *  The address (in a byte) of the register to access within the command.
*/
  return cmd & 0x3F;
} // end get_addr()

/* ------------------------------- */
/* --- TDC Reading and Writing --- */
/* ------------------------------- */
void tdc_write(char cmd, char din, int pin_spi_csb, int pin_tdc_en, int pin_spi_din, int pin_spi_clk) {
  /*
   * Inputs:
   *  cmd: 1 byte intended as the first byte when communicating with the 
   *    TDC over SPI. See Figure 21 in TDC7200 documentation.
   *  din: 1 byte to write to the TDC's register. See TDC7200 documentaion
   *    for specifics of data formatting.
   *  pin_spi_csb: Integer. The Teensy pin associated with CSb for the TDC
   *    on the board.
   *  pin_tdc_en: Integer. The Teensy pin associated with the TDC enable.
   *  pin_spi_din: Integer. The Teensy pin associated with the TDC's SPI
   *    data-in.
   *  pin_spi_clk: Integer. The Teensy pin associated with the TDC's SPI clock
   *    (sometimes referred to as sclk). Note that this is _NOT_ the same thing
   *    as the TDC's reference clock used for calibration.
   * Returns:
   *  Character. The address of the register that's being written to.
   * Notes:
   *  Reads the write command (to forward to the TDC) over serial from the
   *    computer, enforcing that is's a write operation with no auto-incrementing.
   *  Bitbangs the command to the TDC, MSB first.
  */
  Serial.println("Executing TDC write " + String(cmd, BIN));

  // Warn the user if it isn't a write
  if (!bitRead(cmd, 6)) {Serial.println("WARNING: Command is not a write");}
  else {Serial.println("OK: TDC write setting correct");}

  // Warn the user if there's auto-increment
  if (bitRead(cmd, 7)) {Serial.println("WARNING: Auto-increment is enabled");}
  else {Serial.println("OK: TDC not auto-incrementing");}

  // Bit-bang over SPI to the TDC, MSB-first
  digitalWrite(pin_spi_csb, LOW);
  bitbang_byte_in(cmd, pin_spi_din, pin_spi_clk);
  bitbang_byte_in(din, pin_spi_din, pin_spi_clk);
  digitalWrite(pin_spi_csb, HIGH);

  Serial.println("Wrote data " 
    + String(din, BIN) + 
    " to TDC address 0x" 
    + String(get_addr(cmd), HEX));
} // end tdc_write()

int tdc_read(char cmd, int pin_spi_csb, int pin_tdc_en, int pin_spi_din, 
              int pin_spi_dout, int pin_spi_clk, int num_bytes) {
/*
 * Inputs:
 *  cmd: 1 byte intended as the first byte when communicating with the 
 *    TDC over SPI. See Figure 21 in TDC7200 documentation.
 *  pin_sip_csb: Integer. The Teensy pin associated with CSb for the TDC
 *    on the board.
 *  pin_tdc_en: Integer. The Teensy pin associated with the TDC enable.
 *  pin_spi_din: Integer. The Teensy pin associated with the TDC's SPI
 *    data-in (MOSI).
 *  pin_spi_dout: Integer. The Teensy pin associated with the TDC's SPI data-out (MISO)
 *  pin_spi_clk: Integer. The Teensy pin associated with the TDC's SPI clock
 *    (sometimes referred to as sclk). Note that this is _NOT_ the same thing
 *    as the TDC's reference clock used for calibration.
 *  num_bytes: Integer. Number of bytes expected of data to be read.
 * Returns:
 *  Integer. Output data in integer form.
 * Notes:
 *  Receives the command (to forward to the TDC) via serial from the computer,
 *    enforcing that it's a read with no auto-incrementing.
 *  Bitbangs the command to the TDC.
 *  Reads out the output data from the TDC (the return value).
 *  dout is a pointer and will be used to retrieve the data.
*/
  int dout = 0;
  Serial.println("Executing TDC read " + String(cmd, BIN));

  // Warn the user if it isn't a read
  if (bitRead(cmd, 6)) {Serial.println("WARNING: Command is not a read");
  } else {Serial.println("OK: TDC read setting correct");}

  // Warn the user if auto-increment is on
  if (bitRead(cmd, 7)) {Serial.println("WARNING: Auto-increment enabled");
  } else {Serial.println("OK: TDC no auto-increment");}

  // Bit-bang over SPI to the TDC, MSB-first
  digitalWrite(pin_spi_csb, HIGH);
  delayMicroseconds(30);
  digitalWrite(pin_spi_csb, LOW);
  bitbang_byte_in(cmd, pin_spi_din, pin_spi_clk);

  // Bit-bang over SPI from the TDC, MSB-first
  for (int j=0; j<num_bytes; j++) {
    dout = (dout << 8) + bitbang_byte_out(pin_spi_dout, pin_spi_clk);
  }
  digitalWrite(pin_spi_csb, HIGH);
  
  Serial.println("Accessed register at address 0x" + String(cmd & 0x3F, HEX) + " with " + String(num_bytes, DEC) + " bytes");

  return dout;
} // end tdc_read()

/* ---------------------------- */
/* --- Actual TDC Operation --- */
/* ---------------------------- */
void tdc_reset(int pin_tdc_en) {
/*
 * Inputs:
 *  pin_tdc_en: Integer. Teensy pin associated with the enable on the
 *    TDC.
 * Returns:
 *  None.
 * Notes:
 *  Toggles the enable on the TDC low, then high again to
 *    reset the TDC's register values.
*/
  digitalWrite(pin_tdc_en, LOW);
  delayMicroseconds(100);
  digitalWrite(pin_tdc_en, HIGH);
  
  // Allow TDC to initialize
  delayMicroseconds(100);
  
  Serial.println("TDC disabled and enabled");
} // end tdc_reset()

void tdc_start(int pin_start, int pin_latch_rstb) {
/*
 * Inputs:
 *  pin_start: Integer. Teensy pin associated with the 
 *    TDC's start pulse input.
 *  pin_latch_rstb: Integer. Teensy pin associated with the
 *    reset on the latch attached to the output of the CFD.
 * Returns:
 *  None.
 * Notes:
 *  Resets the latch on the output of the CFD.
 *  Feeds a start pulse to the TDC.
*/
  // Reset the latched input to the TDC
  digitalWrite(pin_latch_rstb, LOW);
  delayMicroseconds(10);
  digitalWrite(pin_latch_rstb, HIGH);
  
  // Toggle the start pin high then low
  digitalWrite(pin_start, HIGH);
  delayMicroseconds(100);
  digitalWrite(pin_start, LOW);
  delayMicroseconds(100);

  Serial.println("Start sent to TDC");
} // end tdc_start()

/* ------------------------------- */
/* --- Specific TDC Operations --- */
/* ------------------------------- */
void tdc_config(int pin_spi_csb, int pin_tdc_en, int pin_spi_din, int pin_spi_clk, int pin_tdc_trig) {
/*
 * Inputs:
 *  
 *  pin_tdc_trig: Integer. The Teensy pin associated with the TRIGGER
 *    signal on the TDC. This will go high when the TDC is armed
 *    for a START pulse.
 * Returns:
 *  None.
 * Notes:
 *  Intended for writing to the CONFIG registers of the TDC. 
 *  This assumes any write to CONFIG1 will necessarily want the trigger
 *    pin to to high right after and will print over serial accordingly.
 *  Reads two bytes over serial to write to the config register.
*/
  char msg_in_bytes[2];
  char addr;
  bool trig_ok = false;
  // Read two bytes over serial to write to the config register
  for (int i=0; i<2; i++) {
    while (!Serial.available());
    msg_in_bytes[i] = Serial.read();
  }

  addr = get_addr(msg_in_bytes[0]);
  
  // Write to the register in question
  tdc_write(msg_in_bytes[0], msg_in_bytes[1],
            pin_spi_csb, pin_tdc_en, 
            pin_spi_din, pin_spi_clk);

  // Check if TRIGGER needs to be high
  if (addr == ADDR_CONFIG1) {
    elapsedMillis waiting;
    while (waiting < 1000 && !trig_ok) {
        trig_ok = (digitalRead(pin_tdc_trig) == HIGH);
    }
    if (trig_ok) {
      Serial.println("OK: Trigger good");
    } else {
      Serial.println("WARNING: Trigger low, TDC not armed");
    }
  } else {
    Serial.println("OK: Trigger irrelevant");
  }
} // end tdc_config()

void tdc_read_print(int pin_spi_csb, int pin_tdc_en, 
                    int pin_spi_din, int pin_spi_dout,
                    int pin_spi_clk) {
/*
 * Inputs:
 *  
 * Returns:
 *  None.
 * Notes:
 *  Prints the read-out data over serial, one byte at a time, with
 *    the MSB first.
*/
  char cmd;
  char addr;
  int num_bytes;
  // Read byte over serial to send to the TDC
  while (!Serial.available());
  cmd = Serial.read();

  bitbang_byte_in(cmd, pin_spi_din, pin_spi_clk);
  addr = get_addr(cmd);

  // Figure out number of bytes required to read
  if (addr < 0x10) {
    num_bytes = 1;
  } else {
    num_bytes = 3;
  }

  // Read out data
  int dout = tdc_read(cmd, pin_spi_csb, pin_tdc_en, pin_spi_din, 
          pin_spi_dout, pin_spi_clk, num_bytes);

  // Print out the read-out data over serial
  Serial.println(dout);
//  for (int i=0; i<num_bytes; i++) {
//    Serial.println(dout[i]);
//  }
} // end tdc_read_print()
