
int analogPin=A4;
int digitalOutPin =6;
int val=0;
const int numReadings=50;
int readings[numReadings];
int index=0;
int total=0;
int avg=0;
int x=0;

void setup() {
   // Initialize serial communication for debugging
  Serial.begin(9600);

   for (int i = 0; i < numReadings; i++) {
    readings[i] = 0;   // Initialize all readings to 0
  }
  // Set the digital output pin as an output
  pinMode(digitalOutPin, OUTPUT);
  pinMode(analogPin, INPUT);
}

void loop() {
val=analogRead(analogPin);
total -= readings[index];
readings[index] = val;
total += val;
index = (index + 1) % numReadings;
avg = total / numReadings;
if (x-avg>1 && val<avg) {digitalWrite(digitalOutPin,HIGH);}
if (x-avg<1 ) {digitalWrite(digitalOutPin,LOW);}
x=avg;
}
