/* Goal:
 * - Reads randomly generated numbers every 2 ms
 * - Writes average of randomly generated numbers to serial every 100 ms
 * - Prints in InfluxDB line protocol
 * 
 * Helpful Sources:
 * - https://learn.adafruit.com/multi-tasking-the-arduino-part-1/using-millis-for-timing
 * 
 */

//variables
long previousMillis_read = 0;
long previousMillis_write = 0;
long readInterval = 5;
long writeInterval = 100;
long currentNumber;
long currentSum = 0;
long currentAvg;
int i = 0;

void setup() {
  // put your setup code here, to run once:
  Serial.begin(9600);
  randomSeed(analogRead(0));
}

void loop() {
  // read every 2 ms, write every 100 ms
  unsigned long currentMillis = millis();
  currentNumber = random(3000);
  if(currentMillis - previousMillis_read >= readInterval) {
    previousMillis_read = currentMillis;
    i = i+1;
    currentSum = currentSum + currentNumber;
    currentAvg = currentSum / i;
  }
  if(currentMillis - previousMillis_write >= writeInterval) {
    previousMillis_write = currentMillis;
    
    // print to serial port
    Serial.print("random,");
    Serial.print("pin=None ");
    Serial.print("currentNumber=");
    Serial.print(currentNumber);
    Serial.print(",");
    Serial.print("i=");
    Serial.print(i);
    Serial.print(",");
    Serial.print("currentAvg=");
    Serial.print(currentAvg);
    Serial.print(",");
    Serial.print("millisecs=");
    Serial.println(previousMillis_write);
    
    // resets average calculations
    i = 0;
    currentSum = 0;
  }
}
