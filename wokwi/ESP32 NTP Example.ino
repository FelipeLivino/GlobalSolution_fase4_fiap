// Learn about the ESP32 WiFi simulation in
// https://docs.wokwi.com/guides/esp32-wifi
#include <DHT.h>
#include <WiFi.h>
#include <WiFiClient.h>
#include <WebServer.h>
#include <uri/UriBraces.h>
#include <Wire.h>
#include <MQUnifiedsensor.h>

//módulos para webservice
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include <string>


#define NTP_SERVER     "pool.ntp.org"
#define UTC_OFFSET     0
#define UTC_OFFSET_DST 0

#define dhtPino 14 // Pino do sensor DHT22
#define DHT_TIPO DHT22

// Define o pino analógico onde o sensor MQ-2 está conectado
const int MQ2_PIN = 34;

//Parametros para a calibraão do MQ22 
#define PLACA "ESP32"
#define VOLTAGE_RESOLUTION 5.0
#define ADC_BIT_RESOLUTION 12
#define PIN_MQ2 A0 
#define TIPO_SENSOR "MQ-2"
#define RESISTENCIA_CARGA 5.0 

// Seus limiares calibrados para o Wokwi
const int LIMIAR_FUMACA_INICIAL = 2153;// 3 no sensor
const int LIMIAR_FUMACA_LEVE = 2383; // 6 no sensor de fumaça
const int LIMIAR_FUMACA_MODERADA = 2585; // 10 no sensor de fumaça
const int LIMIAR_FUMACA_DENSA = 2900; // limiar entre 23 e 24 no sensor de fumaça

const int BUZZER_PIN = 5;

//Inicia sensor DHT22
DHT dht(dhtPino, DHT22); 

MQUnifiedsensor MQ2(PLACA, VOLTAGE_RESOLUTION, ADC_BIT_RESOLUTION, PIN_MQ2, TIPO_SENSOR);

//método http para passar dados dos sensores no web-service
HTTPClient http; 

// --- Limiares de Temperatura e Umidade (Exemplos - AJUSTE!) ---
const float TEMP_ALTA_CRITICA = 50.0;       // Temperatura crítica em °C
const float TEMP_ELEVADA_ATENCAO = 38.0;    // Temperatura elevada em °C
const float AUMENTO_RAPIDO_TEMP = 5.0;      // Aumento de X °C para considerar rápido
const float UMIDADE_BAIXA_CRITICA = 20.0;   // Umidade crítica em %

// --- Variáveis para controle de tempo e leituras anteriores ---
float temperaturaAnterior = -100; // Inicializa com um valor improvável
unsigned long tempoLeituraAnterior = 0;
const unsigned long INTERVALO_VERIF_AUMENTO_TEMP = 60000; // Verificar aumento a cada 1 minuto (60000 ms)



void setup() {
  Serial.begin(115200);
  while (!Serial) delay(10);
  

  WiFi.begin("Wokwi-GUEST", "", 6);
  while (WiFi.status() != WL_CONNECTED) {
    delay(250);
  }

  dht.begin();
  float temperatura = dht.readTemperature();
  float umidade = dht.readHumidity();

  if (isnan(temperatura) || isnan(umidade)) {
    Serial.println("Erro ao ler do sensor DHT!");
  } else {
    Serial.println("Sensor DHT22 inicializado.");
    temperaturaAnterior = temperatura; // Define a primeira leitura como anterior
  }

  Serial.println("Atualizando Hora");
  configTime(UTC_OFFSET, UTC_OFFSET_DST, NTP_SERVER);

  Wire.begin(21, 22);

  Serial.println("Aguarde o aquecimento da resistencia do sensor");
  MQ2.setRL(RESISTENCIA_CARGA);
  delay(10000); //Aquecimento da resistencia

  float r0_calculado = 1693.0; //coresponde ao valor de 1ppm
   MQ2.setR0(r0_calculado);
   MQ2.setRegressionMethod(1); // método de regressão linear
   MQ2.init();
  Serial.print("R0 calibrado/definido para: ");
  Serial.println(MQ2.getR0());

  delay(250);
  pinMode(BUZZER_PIN, OUTPUT);
  digitalWrite(BUZZER_PIN, LOW);
}

void loop() {
  int valorMQ2 = analogRead(MQ2_PIN);
  float temperatura = dht.readTemperature();
  float umidade = dht.readHumidity();
  // Verifica se houve erro na leitura do DHT22
  if (isnan(temperatura) || isnan(umidade)) {
    Serial.print("Falha ao ler temperatura ");
    delay(2000);
    return;
  }
  
  checkFire(valorMQ2, temperatura, umidade);

}

void checkFire(int valorMQ2, float temperatura, float umidade){
   // --- Lógica de Detecção de Aumento Rápido de Temperatura ---
  bool houveAumentoRapidoTemp = false;
  if (millis() - tempoLeituraAnterior > INTERVALO_VERIF_AUMENTO_TEMP) {
    if (temperaturaAnterior > -99) { // Verifica se temperaturaAnterior é válida
        if ((temperatura - temperaturaAnterior) >= AUMENTO_RAPIDO_TEMP) {
            houveAumentoRapidoTemp = true;
        }
    }
    temperaturaAnterior = temperatura; // Atualiza a temperatura anterior
    tempoLeituraAnterior = millis();   // Atualiza o tempo da última verificação
  }

  // --- Impressão dos Dados (para debugging no Wokwi) ---
  Serial.print("MQ2: "); Serial.print(valorMQ2);
  Serial.print(" | Temp: "); Serial.print(temperatura); Serial.print("°C");
  Serial.print(" | Umid: "); Serial.print(umidade); Serial.print("%");
  if (houveAumentoRapidoTemp) Serial.println(" | AUMENTO RÁPIDO DE TEMP!");
  Serial.println("");

  // --- Lógica de Alerta Combinado ---
  bool alertaFumacaDensa = (valorMQ2 >= LIMIAR_FUMACA_DENSA);
  bool alertaFumacaModerada = (valorMQ2 >= LIMIAR_FUMACA_MODERADA);
  bool alertaFumacaLeve = (valorMQ2 >= LIMIAR_FUMACA_LEVE);
  bool alertaFumacaInicial = (valorMQ2 >= LIMIAR_FUMACA_INICIAL);

  bool tempCritica = (temperatura >= TEMP_ALTA_CRITICA);
  bool tempElevada = (temperatura >= TEMP_ELEVADA_ATENCAO);

  
  char* mensagem;
  char* status;
  // Nível de Alerta Máximo
  if ( (alertaFumacaModerada || alertaFumacaDensa) && (tempCritica || houveAumentoRapidoTemp) ) {
    mensagem = "ALERTA MÁXIMO: Fogo altamente provável (Fumaça + Temp Alta/Rápida)!";
    status =  "ALERTA_MAXIMO";
    bip_alarme_ativo(25, 6, 100);
  }
  // Nível de Alerta Alto
  else if ( (alertaFumacaLeve || alertaFumacaModerada) && tempElevada ) {
    mensagem = "ALERTA ALTO: Possível fogo (Fumaça + Temp Elevada)!";
    status =  "ALERTA_ALTO";
    bip_alarme_ativo(22, 6, 100);
  }
  else if ( alertaFumacaDensa ) { // Muita fumaça, mesmo sem confirmação de temp ainda
    mensagem = "ALERTA ALTO: Fumaça Densa Detectada!";
    status =  "ALERTA_ALTO";
    bip_alarme_ativo(17, 6, 100);
  }
  // Nível de Atenção
  else if ( alertaFumacaInicial && (tempElevada || houveAumentoRapidoTemp) ) {
    mensagem = "ATENÇÃO: Condições suspeitas (Fumaça inicial + Temp Elevada/Rápida).";
    status =  "ATENCAO";
    bip_alarme_ativo(14, 6, 100);
  }
  else if ( alertaFumacaLeve ) { // Apenas fumaça leve, monitorar
    mensagem = "INFO: Fumaça Leve detectada, monitorando temperatura.";
    status =  "ATENCAO";
    bip_alarme_ativo(10, 6, 100);
  }
  else if ( alertaFumacaInicial ) { // Apenas traços iniciais, monitorar
    mensagem = "INFO: Traços iniciais de fumaça detectados.";
    status =  "ATENCAO";
    bip_alarme_ativo(8, 6, 100);
  }
  // Condições apenas de temperatura (pode ser útil para outros fins, ou indicar problema no sensor de fumaça)
  else if (tempCritica || houveAumentoRapidoTemp) {
    mensagem = "AVISO: Temperatura crítica ou aumento rápido detectado SEM fumaça significativa.";
    status =  "ATENCAO";
    bip_alarme_ativo(5, 6, 100);
  }
  else {
    mensagem = "Condições normais.";
    status =  "NORMAL";
    bip_alarme_ativo(1, 6, 100);
  }
  Serial.println(mensagem);
  callWs(status, mensagem,temperatura, valorMQ2);
  delay(4000);
}


void callWs(char* status, char* mensagem, float temperatura, float valorMQ2 ){
  //link do webservice
  http.begin("https://newsfacd.herokuapp.com/journeybuilder/success"); 
  http.addHeader("Content-Type", "application/json");
  
  //formar arquivo json
  StaticJsonDocument<1024> doc;
  doc["status"] = status;
  doc["mensagem"] = mensagem;
  doc["temperatura"] = temperatura;
  doc["valorMQ2"] = valorMQ2;

  String httpRequestData;
  serializeJson(doc, httpRequestData);

  int httpResponseCode = http.POST(httpRequestData);
  if (httpResponseCode > 0) {
    String payload = http.getString();
  } else {
    Serial.printf("Falha na requisição HTTP, erro: %s\n", http.errorToString(httpResponseCode).c_str());
  }
}

void ligar_buzzer_ativo() {
  digitalWrite(BUZZER_PIN, HIGH); // Liga o buzzer
}

void desligar_buzzer_ativo() {
  digitalWrite(BUZZER_PIN, LOW); // Desliga o buzzer
}


void bip_alarme_ativo(int numero_bipes, int duracao_bipe, int intervalo_bipe) {
  for (int i = 0; i < numero_bipes; i++) {
    for (int j = 0; j < 5; j++) {
      ligar_buzzer_ativo();
      delay(duracao_bipe);
      desligar_buzzer_ativo();
    }
    delay(intervalo_bipe);
  }
}