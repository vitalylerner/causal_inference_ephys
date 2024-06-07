int clk_cnt;
int period;
int duration;

int StimTrig;
bool StimGate;

char receivedChar;
#define regular_period   1000
#define regular_duration 250
#define regular_M        55

#define sweep_step     100
#define sweep_M        5


#define clk_pin 2
#define stim_pin 8
#define gate_pin 7

void setup() {
  pinMode(clk_pin, OUTPUT);    
  pinMode(stim_pin, INPUT);
  pinMode(gate_pin,INPUT);
  
  Serial.begin(9600);
  Serial.println("<Arduino is ready>");

  StimGate=false;
  StimTrig=0;
  clk_reset();

}

void clk_reset(){
  period=regular_period;
  duration=regular_duration;
  clk_cnt=0;
}

void gate_tick(){
  /*if (clk_cnt>10){
    clk_cnt==0
  }*/
  //delay(1000);
  if (digitalRead(stim_pin)>0){
    digitalWrite(clk_pin,HIGH);
    delay(2000);
    digitalWrite(clk_pin,LOW);
  }
  //clk_cnt++;
}

void clk_tick(){
  digitalWrite(clk_pin, HIGH); 
  delay(duration);            
  digitalWrite(clk_pin, LOW); 
  delay(period-duration);            
  clk_cnt++;
}

void clk_sweep(int k){
  period=regular_period-k*sweep_step;
  duration=regular_duration;
}

void loop() {
  //StimGate=digitalRead(gate_pin)>0;
  if (Serial.available() > 0) {
    receivedChar = Serial.read();
    
    StimGate=!StimGate;
    Serial.print("Swithed to ");
    if (StimGate)
      Serial.println("visual stimulus trigger");
    else
      Serial.println("1Hz+sweep trigger");
  }

  //StimGate=true;
  if (StimGate){
    gate_tick();
  }
  else{
    clk_tick();
    if (clk_cnt>=regular_M){
      clk_sweep(clk_cnt-regular_M);
    }
    if (clk_cnt==regular_M+sweep_M){
      clk_reset();
    }
  }

}