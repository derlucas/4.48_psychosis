char zaehler;

void setup() {
  Serial.begin(115200);
  pinMode(7, OUTPUT);
  zaehler = 0;
}

float getTemperature(void)
{
    //Local variables
    float Temperature; //Corporal Temperature
    float Resistance;  //Resistance of sensor.
    float ganancia=5.0;
    float Vcc=3.3;
    float RefTension=3.0; // Voltage Reference of Wheatstone bridge.
    float Ra=4700.0; //Wheatstone bridge resistance.
    float Rc=4700.0; //Wheatstone bridge resistance.
    float Rb=821.0; //Wheatstone bridge resistance.
    int sensorValue = analogRead(A3);

    float voltage2=((float)sensorValue*Vcc)/1023; // binary to voltage conversion

    // Wheatstone bridge output voltage.
    voltage2=voltage2/ganancia;
    // Resistance sensor calculate
    float aux=(voltage2/RefTension)+Rb/(Rb+Ra);
    Resistance=Rc*aux/(1-aux);
    if (Resistance >=1822.8) {
        // if temperature between 25ºC and 29.9ºC. R(tª)=6638.20457*(0.95768)^t
        Temperature=log(Resistance/6638.20457)/log(0.95768);
    } else {
        if (Resistance >=1477.1){
                        // if temperature between 30ºC and 34.9ºC. R(tª)=6403.49306*(0.95883)^t
                        Temperature=log(Resistance/6403.49306)/log(0.95883);
        } else {
                if (Resistance >=1204.8){
                        // if temperature between 35ºC and 39.9ºC. R(tª)=6118.01620*(0.96008)^t
                        Temperature=log(Resistance/6118.01620)/log(0.96008);
                }
                else{
                        if (Resistance >=988.1){
                                // if temperature between 40ºC and 44.9ºC. R(tª)=5859.06368*(0.96112)^t
                                Temperature=log(Resistance/5859.06368)/log(0.96112);
                        }
                        else {
                                if (Resistance >=811.7){
                                        // if temperature between 45ºC and 50ºC. R(tª)=5575.94572*(0.96218)^t
                                        Temperature=log(Resistance/5575.94572)/log(0.96218);
                                }
                        }
                }
        }
    }

    return Temperature;
}


void loop() {
  zaehler++;
//  int airFlow = analogRead(A1);
//  int emg = analogRead(0);
//  int temp = getTemperature();
  Serial.print(analogRead(A1));
  Serial.print(";");
  Serial.print(analogRead(0));
  Serial.print(";");
  Serial.println(getTemperature());
  delay(100);
  
  if(zaehler >= 10) {
    zaehler = 0;
    if(digitalRead(7) == HIGH) {
      digitalWrite(7, LOW);
    } else {
      digitalWrite(7, HIGH);
    }
  }
  

}

