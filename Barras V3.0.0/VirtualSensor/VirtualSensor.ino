#define sensor1 7
#define sensor2 6
#define sensor3 5
#define sensor4 4

const char S1ON = '1';
const char S1OFF = '2';
const char S2ON = '3';
const char S2OFF = '4';
const char S3ON = '5';
const char S3OFF = '6';
const char S4ON = '7';
const char S4OFF = '8';

void setup() 
{
  pinMode(sensor1, OUTPUT);
  pinMode(sensor2, OUTPUT);
  pinMode(sensor3, OUTPUT);
  pinMode(sensor4, OUTPUT);
  
  Serial.begin(115200);
}

void loop() 
{
  if (Serial.available())
  {
    char estadoactual = Serial.read();

    if (estadoactual == S1ON)
    {
      Serial.println("S1-------->ON");
      digitalWrite(sensor1, HIGH);
    }

    if (estadoactual == S1OFF)
    {
      Serial.println("S1-------->OFF");
      digitalWrite(sensor1, LOW);
    }

    if (estadoactual == S2ON)
    {
      Serial.println("S2-------->ON");
      digitalWrite(sensor2, HIGH);
    }

    if (estadoactual == S2OFF)
    {
      Serial.println("S2-------->OFF");
      digitalWrite(sensor2, LOW);
    }

    if (estadoactual == S3ON)
    {
      Serial.println("S3-------->ON");
      digitalWrite(sensor3, HIGH);
    }

    if (estadoactual == S3OFF)
    {
      Serial.println("S3-------->OFF");
      digitalWrite(sensor3, LOW);
    }

    if (estadoactual == S4ON)
    {
      Serial.println("S4-------->ON");
      digitalWrite(sensor4, HIGH);
    }

    if (estadoactual == S4OFF)
    {
      Serial.println("S4-------->OFF");
      digitalWrite(sensor4, LOW);
    }
  }
}
