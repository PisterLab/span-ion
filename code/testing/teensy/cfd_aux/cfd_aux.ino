/*
 * This is for a secondary Teensy intended to provide a variety of 
 * slow analog signals for the SPAN-Ion chip. These were not
 * connected to the original Teensy because of the additional capacitance
 * they would introduce for fast testing.
*/

/* --------------------------------- */
/* --- Pin Mappings (Teensy 3.6) --- */
/* --------------------------------- */
// Useful pins to use elsewhere
const int pin_dac0 = A21;
const int pin_dac1 = A22;

// Small signal chain
const int pin_zcd_vinn_small  = A21; // ZCD comparator inverting input
const int pin_zcd_vinp_small  = A22; // ZCD comparator noninverting input
const int pin_led_vinp_small  = A0; // LED comparator noninverting input

// Main signal chain
const int pin_vin_main        = A0; // Voltage input to the board amp for the signal input

// Test structures
const int pin_pk_vin          = A21; // Test peak detector input voltage

// Constants
const int B_ADC = 16; // Number of bits (precision) for analogRead

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

  // Setting the ADC precision
  analogReadResolution(B_ADC);  // 16B -> 13ENOB
  analogWriteResolution(B_ADC); // 16B -> 13ENOB?

  // Set up pins
  // - Small Signal Chain
  pinMode(pin_zcd_vinn_small, OUTPUT);
  pinMode(pin_zcd_vinp_small, OUTPUT);
  pinMode(pin_led_vinp_small, OUTPUT);

  analogWrite(pin_zcd_vinn_small, 1<<B_ADC);
  analogWrite(pin_zcd_vinp_small, 0);
  analogWrite(pin_led_vinp_small, 0);
  
  // - Main Signal Chain
  pinMode(pin_vin_main, OUTPUT);

  analogWrite(pin_vin_main, 0);
  
  // - Test Structures
  pinMode(pin_pk_vin, OUTPUT);

  analogWrite(pin_pk_vin, 0);
} // end setup

void loop() {
if (stringComplete){
    if (inputString == "peakslow\n"){
      slow_ramp(pin_pk_vin);
    } 
    else if (inputString == "zcdcompnsmall\n") {
      slow_ramp(pin_zcd_vinn_small);
    }
    else if (inputString == "zcdcomppsmall\n") {
      slow_ramp(pin_zcd_vinp_small);  
    }
    else if (inputString == "ledcomppsmall\n") {
      slow_ramp(pin_led_vinp_small);  
    }
    else if (inputString == "vinmain\n") {
      slow_ramp(pin_vin_main);  
    }

    // Reset to listen for a new '\n' terminated string over serial
    inputString = "";
    stringComplete = false;
  }

} // end loop

void slow_ramp(int pin) {
/*
 * Inputs:
 *  pin: Integer. The pin to ramp.
 * Returns:
 *  None.
 * Notes:
 *  Reads in the desired set voltage _in LSB_ over serial and sets
 *  the pin voltage to that DC value with a ramp of roughly 3.3V/ms.
*/
  // Read in the desired set voltage (in LSB, MSB first)
  int vin_target = 0;
  for (int i=0; i<2; i++) {
    while(!Serial.available());
    vin_target = (vin_target << 8) + Serial.read();
  }
  Serial.println(vin_target);

  // Set the desired voltage
  analogWrite(pin, vin_target);
  
} // end slow_ramp

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
