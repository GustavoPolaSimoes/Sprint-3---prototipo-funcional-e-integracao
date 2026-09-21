int ldr = A0;
int sensor_temp = A1;
int login = 2;
int energia_solar = 3;
int switchlogin = 0;
int switchsolar = 0;
int alta_demanda = 13;
int sobrecargaE = 12;
int sobrecargaT = 10;
int temperatura = 0;

unsigned long ultimaLeituraSerial = 0;
const unsigned long intervaloSerial = 1000;

void setup() {

  pinMode(login, INPUT);
  pinMode(energia_solar, INPUT);

  pinMode(alta_demanda, OUTPUT);
  pinMode(sobrecargaE, OUTPUT);
  pinMode(sobrecargaT, OUTPUT);

  digitalWrite(alta_demanda, LOW);
  digitalWrite(sobrecargaE, LOW);
  digitalWrite(sobrecargaT, LOW);

  Serial.begin(9600);
}

void loop() {

  switchlogin = digitalRead(login);

  switchsolar = digitalRead(energia_solar);

  int ldrVal = analogRead(ldr);

  int leitor_temp = analogRead(sensor_temp);

  temperatura = map(
    leitor_temp,
    20,
    358,
    -40,
    125
  );

  if (
    ldrVal > 300
    && ldrVal < 500
    && switchlogin == 1
  ) {

    digitalWrite(
      alta_demanda,
      HIGH
    );

    digitalWrite(
      sobrecargaE,
      LOW
    );
  }

  else if (
    ldrVal <= 300
    && switchlogin == 1
  ) {

    digitalWrite(
      alta_demanda,
      LOW
    );

    digitalWrite(
      sobrecargaE,
      HIGH
    );
  }

  else {

    digitalWrite(
      alta_demanda,
      LOW
    );

    digitalWrite(
      sobrecargaE,
      LOW
    );
  }


  if (
    temperatura >= 65
    || temperatura <= -35
  ) {

    digitalWrite(
      sobrecargaT,
      HIGH
    );
  }

  else {

    digitalWrite(
      sobrecargaT,
      LOW
    );
  }


  if (
    millis() - ultimaLeituraSerial
    >= intervaloSerial
  ) {

    ultimaLeituraSerial = millis();


    enviarDadosSerial(

      switchlogin,

      switchsolar,

      ldrVal,

      temperatura,

      digitalRead(
        alta_demanda
      ),

      digitalRead(
        sobrecargaE
      ),

      digitalRead(
        sobrecargaT
      )
    );
  }
}


void enviarDadosSerial(
  int loginValor,
  int solarValor,
  int ldrValor,
  int temperaturaValor,
  int altaDemandaValor,
  int sobrecargaEletricaValor,
  int sobrecargaTermicaValor
) {

  Serial.print(
    "{\"login\":"
  );

  Serial.print(
    loginValor
  );


  Serial.print(
    ",\"solar\":"
  );

  Serial.print(
    solarValor
  );


  Serial.print(
    ",\"ldr\":"
  );

  Serial.print(
    ldrValor
  );


  Serial.print(
    ",\"temperatura\":"
  );

  Serial.print(
    temperaturaValor
  );


  Serial.print(
    ",\"altaDemanda\":"
  );

  Serial.print(
    altaDemandaValor
  );


  Serial.print(
    ",\"sobrecargaEletrica\":"
  );

  Serial.print(
    sobrecargaEletricaValor
  );


  Serial.print(
    ",\"sobrecargaTermica\":"
  );

  Serial.print(
    sobrecargaTermicaValor
  );


  Serial.println(
    "}"
  );
}
