/*
 * Code for interacting with the various test structures on the chip.
 * - peak detector
 * - bandgap
 * - DACs
 * - intermediate comparator outputs
*/
#include <Arduino.h>

/* ------------------------------------------ */
/* --- On-Chip Test Structure Interaction --- */
/* ------------------------------------------ */
void peak_reset(int pin_pk_rst) {
/* 
 *  Resets the test structure peak detector.
*/
  digitalWrite(pin_pk_rst, HIGH);
  delayMicroseconds(100);
  digitalWrite(pin_pk_rst, LOW);
  delayMicroseconds(500);
}

void peak_read(int pin_pk_out) {
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
void bandgap_test(int pin_bandgap) {
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

/* --------------------------------------------- */
/* --- Intermediate Comparator Sanity Checks --- */
/* --------------------------------------------- */
void latch_reset(int pin_reset, bool active_low) {
/*
 * Inputs:
 *  pin_reset: Integer. Designation of the pin to control.
 *  active_low: Boolean. True if the reset is active low.
 * Returns:
 *  None.
*/
  if (active_low) {
    digitalWrite(pin_pk_rst, HIGH);
    delayMicroseconds(100);
    digitalWrite(pin_pk_rst, LOW);
    delayMicroseconds(500);
  }
  else {
    digitalWrite(pin_pk_rst, LOW);
    delayMicroseconds(100);
    digitalWrite(pin_pk_rst, HIGH);
    delayMicroseconds(500);
  }
}