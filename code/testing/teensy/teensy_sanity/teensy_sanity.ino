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

// Constants
const int B_ADC = 16; // Resolution for ADC read/write

void setup() {
  analogReadResolution(B_ADC);  // 16B -> 13ENOB
  analogWriteResolution(B_ADC); // 16B -> 13ENOB?
  // analogWriteFrequency(dac1, 915.527);
  
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
  for (int i=0; i<100; i++) {
    Serial.println(InternalTemperature.readTemperatureC());
  }
}
