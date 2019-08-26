/*
1. Use temp pin to generate voltage, Celsius & Fahrenheit
2. Print as measurement,pin=A0 voltage=x,Celsius=y,Fahrenheit=z
3. Send printed data to InfluxDB over http/UDP via Ethernet

*/

const int temperaturePin = 0;


void setup()
{
  Serial.begin(9600);
}


void loop()
{
  float voltage, degreesC, degreesF;

  voltage = getVoltage(temperaturePin);

  degreesC = (voltage - 0.5) * 100.0;
  
  degreesF = degreesC * (9.0/5.0) + 32.0;

  Serial.print("Temp_Sensor,");
  Serial.print("pin=A0 ");
  Serial.print("voltage=");
  Serial.print(voltage);
  Serial.print(",");
  Serial.print("Celsius=");
  Serial.print(degreesC);
  Serial.print(",");
  Serial.print("Fahrenheit=");
  Serial.println(degreesF);
   
  delay(1000); // repeat once per second
}


float getVoltage(int pin)
{ 
  return (analogRead(pin) * 0.004882814);

  Serial.end();
}
