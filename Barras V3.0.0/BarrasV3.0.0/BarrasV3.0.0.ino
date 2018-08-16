/*
#####################################################################
#							BARRAS 3.0.0							                            #
#####################################################################
#	       Desarrollador:	Francisco Javier Hernandez Luna			        #
#	Hardware:		Arduino Uno / Arduino Mega						                #
#					    Sensor Sharp Analogo / Digital	  	                  #
#	IDE Arduino:	1.8.5											                          #
#####################################################################
#									Creado	:	15 de abril 2018	                      #
#						Ultima modificacion	:	15 de agosto 2018	                #
#####################################################################
*/

// Variables de estado de los sensores
boolean estado1 = false;
boolean estado2 = false;
boolean estado3 = false;
boolean estado4 = false;

// Variables de control de los estados
boolean estadoSB = false;
boolean estadoBJ = false;
boolean estadoPR = false;
boolean estadoPS = false;
boolean estadoFN = false;
boolean estadoBL = false;

// Variables de control de timers
long contador 	= 0;
long comparador = 20;
long bloqueos 	= 15;

int timer = 100;
int contadorEX = 0;
int comparadorEX = 3;

// Definicion de los pines de entrada
#define dir1 7	// Sensor Subida Superior
#define dir2 6	// Sensor Bajada Superior
#define dir3 5	// Sensor Subida Inferior
#define dir4 4	// Sensor Bajada Inferior

void setup()
{
  // Definimos los pines de entrada
  pinMode(dir1, INPUT);
  pinMode(dir2, INPUT);
  pinMode(dir3, INPUT);
  pinMode(dir4, INPUT);
  
  Serial.begin(115200);
  Serial.println("Contador Barras 3.0.0");
}

void loop()
{
  // Si se generaron muchas excepciones se toma como bloqueo de barras
  if (contadorEX == comparadorEX)
  {
    Serial.println("QUITATE DE LAS BARRAS -------> CHUFA SUPER EMPUTADO");    
  }
  
  // Leemos las 4 entradas para determinar el primer estado
  estado1 = digitalRead(dir1);
  estado2 = digitalRead(dir2);
  estado3 = digitalRead(dir3);
  estado4 = digitalRead(dir4);

  // Evaluamos el estado de subida superior
  if (estado1 and !estado3 and !estado2 and !estado4)
  {
    estadoSB = true;
	  contador = comparador;
    Serial.print("Estado Subida UP ");
  }

  // Evaluamos el estado de subida inferior
  if (estado3 and !estado1 and !estado2 and !estado4)
  {
    estadoSB = true;
    contador = comparador;
    Serial.print("Estado Subida DW ");
  }
	/*
	#############################################
	# 		Evaluamos el estado de subida		      #
	#			          1	0		X	0				            #
	#			          X	0		1	0				            #
	#############################################
	*/

  // Evaluamos el estado de bajada superior
  if (!estado1 and !estado3 and estado2 and !estado4)
  {
    estadoBJ = true;
	  contador = comparador;
    Serial.print("Estado Bajada UP ");
  }

  // Evaluamos el estado de bajada inferior
  if (!estado1 and !estado3 and estado4 and !estado2)
  {
    estadoBJ = true;
    contador = comparador;
    Serial.print("Estado Bajada DW ");
  }
	/*
	#############################################
	#		    Evaluamos el estado de bajada		    #
	#			            0	1		0	X				          #
	#			            0	X		0	1				          #
	#############################################
	*/

  // Comenzar a detectar un bloque de S1 S2 S3 y S4
  if (estado1 and estado2 and estado3 and estado4)
  {
    estadoBL = true;
    contador = bloqueos;
    Serial.print("Algo va mal S1,S2,S3,S4 BL ");
  }

  // Comenzar a detectar un bloqueo de S1, S2
  if (estado1 and estado2 and !estado3 and !estado4)
  {
    estadoBL = true;
    contador = bloqueos;
    Serial.print("Algo va mal S1,S2 BL ");
  }

  // Comenzar a detectar un bloqueo de S1, S3
  if (estado1 and !estado2 and estado3 and !estado4)
  {
    estadoBL = true;
    contador = bloqueos;
    Serial.print("Algo va mal S1,S3 BL ");
  }

  // Comenzar a detectar un bloqueo de S2, S4
  if (!estado1 and estado2 and !estado3 and estado4)
  {
    estadoBL = true;
    contador = bloqueos;
    Serial.print("Algo va mal S2,S4 BL ");
  }

  // Comenzar a detectar un bloqueo de S3, S4
  if (estado3 and estado4 and !estado1 and !estado2)
  {
    estadoBL = true;
    contador = bloqueos;
    Serial.print("Algo va mal S3, S4 BL ");
  }

  // Comenzar a detectar un bloqueo de S1, S2 y S3
  if (estado1 and estado2 and estado3 and !estado4)
  {
    estadoBL = true;
    contador = bloqueos;
    Serial.print("Algo va mal S1, S2, S3 BL");
  }

  // Comenzar a detectar un bloqueo de S1, S2 y S4
  if (estado1 and estado2 and !estado3 and estado4)
  {
    estadoBL = true;
    contador = bloqueos;
    Serial.print("Algo va mal S1, S2, S4 BL");
  }

  // Comenzar a detectar un bloqueo de S1, S3 y S4
  if (estado1 and !estado2 and estado3 and estado4)
  {
    estadoBL = true;
    contador = bloqueos;
    Serial.print("Algo va mal S1, S3, S4 BL");
  }

  // Comenzar a detectar un bloqueo de S2, S3 y S2
  if (!estado1 and estado2 and estado3 and estado4)
  {
    estadoBL = true;
    contador = bloqueos;
    Serial.print("Algo va mal S2, S3, S4 BL");
  }
    
  // Comenzamos a evaluar los estados de subida
  while (estadoSB and contador > 0)
  {
    contador = contador - 1;
	  Serial.print("SB");
	  delay(timer);
	  estado1 = digitalRead(dir1);
	  estado2 = digitalRead(dir2);
	  estado3 = digitalRead(dir3);
	  estado4 = digitalRead(dir4);
	  if (contador == 0)
    {
      estadoSB = false;
	    Serial.println(" EX-01");
      contadorEX = contadorEX + 1; 
	  }       // Generamos la Excepcion 01 para Subidas
  }         // Final del While del Estado de Subida
  
  // Comenzamos a evaluar los estados de bajada
  while (estadoBJ and contador > 0)
  {
    contador = contador - 1;
	  Serial.print("BJ");
	  delay(timer);
	  estado1 = digitalRead(dir1);
	  estado2 = digitalRead(dir2);
	  estado3 = digitalRead(dir3);
	  estado4 = digitalRead(dir4);
	  
	  if (contador == 0)
	  {
	    estadoBJ = false;
	    Serial.println(" EX-10");
      contadorEX = contadorEX + 1;
	  }       // Generamos la Excepcion 10 para Bajadas
  }         // Final del While de Estado de Bajada

  // Comenzamos a evaluar el estado de bloqueo
  while (estadoBL and contador > 0)
  {
    contador = contador - 1;
    Serial.print("BL");
    delay(timer);
    estado1 = digitalRead(dir1);
    estado2 = digitalRead(dir2);
    estado3 = digitalRead(dir3);
    estado4 = digitalRead(dir4);

    if (!estado1 and estado2 and estado3 and estado4)
    {
      while (contador > 0)
      {
        contador = contador - 1;
        Serial.print("BL");
        delay(timer);    
      }
    }         // Se desbloqueo el Sensor 01

    if (estado1 and !estado2 and estado3 and estado4)
    {
      while (contador > 0)
      {
        contador = contador - 1;
        Serial.print("BL");
        delay(timer);    
      }
    }         // Se desbloqueo el Sensor 02

    if (estado1 and estado2 and !estado3 and estado4)
    {
      while (contador > 0)
      {
        contador = contador - 1;
        Serial.print("BL");
        delay(timer);    
      }
    }         // Se desbloqueo el Sensor 03

    if (estado1 and estado2 and estado3 and !estado4)
    {
      while (contador > 0)
      {
        contador = contador - 1;
        Serial.print("BL");
        delay(timer);    
      }
    }         // Se desbloqueo el Sensor 04

    if (!estado1 and !estado2 and estado3 and estado4)
    {
      while (contador > 0)
      {
        contador = contador - 1;
        Serial.print("BL");
        delay(timer);    
      }
    }         // Se desbloqueo el Sensor 01 y 02

    if (estado1 and estado2 and !estado3 and !estado4)
    {
      while (contador > 0)
      {
        contador = contador - 1;
        Serial.print("BL");
        delay(timer);    
      }
    }         // Se desbloqueo el Sensor 03 y 04
    
    if (contador == 0)
    {
      Serial.println(" CHUFA SUPER ENOJADO");
    }         // Las barras se han bloqueado
  }         // Final del while del bloqueo
}           // Final del Void Loop
