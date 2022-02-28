#include <Wire.h> // Used to establish serial comms on I2C bus
#include <SparkFunTMP102.h> // Used to send and receive specific info from the sensor
#include <InternalTemperature.h> // Used to read the Teensy internal temperature

/* --------------------------------- */
/* --- Pin Mappings (Teensy 3.6) --- */
/* --------------------------------- */
// VDD and GND
const int pin_gnd = 17;
const int pin_vdd = 16;

/* ----------------------------- */
/* --- Runs once at power-on --- */
/* ----------------------------- */
// Initialize sensor at I2C address 0x48
TMP102 sensor0;

// Variables for command interpreter
String inputString = "";
boolean stringComplete = false;

void setup() {
  // Open USB serial port
  Serial.begin(9600);

  // Reserve 200 bytes for the inputString
  inputString.reserve(200);

  // Pin setup
  // - VDD and GND
  pinMode(pin_gnd, OUTPUT);
  pinMode(pin_vdd, OUTPUT);

  digitalWrite(pin_gnd, LOW);
  digitalWrite(pin_vdd, HIGH);

  // Join I2C bus, default address 0x48
  Wire.begin();

  // Check TMP102 connection
  if (!sensor0.begin()) {Serial.println("Cannot connect to TMP102");}
  else {Serial.println("Connected to TMP102");}
}

void loop() {
  if (stringComplete) {
    if (inputString == "temp\n") {
      read_temp();
    }
    if (inputString == "tempinternal\n") {
      read_temp_internal();  
    }
  }

  inputString = "";
  stringComplete = false;

}

void read_temp_internal() {
  /*
   * Inputs:
   *  None.
   * Returns:
   *  None.
   * Notes:
   *  Prints the internal temperature (in Celsius) of the Teensy over
   *  serial.
  */
    InternalTemperature.begin(TEMPERATURE_NO_ADC_SETTING_CHANGES);
    Serial.println(InternalTemperature.readTemperatureC());
}

void read_temp() {
  /*
   * Inputs:
   *  None
   * Returns:
   *  None
   * Notes:
   *  Queries the TMP102 and prints the temperature over serial.
  */
  float tmp = 0;
  // Turn sensor on to start temp measurement (~10uA)
  sensor0.wakeup();

  // Read temp data
  tmp = sensor0.readTempC();

  // Put sensor in sleep mode (<0.5uA)
  sensor0.sleep();

  // Print over serial
  Serial.println(tmp);
} // end read_temp()

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
