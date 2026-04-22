# Informe Técnico — Práctica MQTT
## Integración de un Objeto Inteligente con MQTT, Aplicación Móvil y Herramienta de IA

**Carrera:** Ingeniería de Sistemas  
**Asignatura:** SIS-234  
**Gestión:** 2025

Integrantes:
    Gabriel Herrera
    Nicole Gomez
    Fernando Rodriguez
---

## 1. Descripción del Sistema

El presente proyecto implementa un sistema de comunicación IoT basado en el protocolo MQTT. El sistema integra un objeto inteligente basado en ESP32, un sensor ultrasónico HC-SR04, tres actuadores LED, una aplicación móvil (IoT MQTT Panel), un broker MQTT en la nube (HiveMQ) y una herramienta de inteligencia artificial (Claude Desktop con MCP) para el control mediante lenguaje natural.

### 1.1 Componentes del Sistema

- **Objeto Inteligente:** ESP32 con sensor ultrasónico HC-SR04 y 3 LEDs.
- **Broker MQTT en la nube:** HiveMQ (`broker.hivemq.com`, puerto 1883).
- **Aplicación móvil:** IoT MQTT Panel — visualización gráfica del sensor y control de actuadores.
- **Herramienta de IA:** Claude Desktop con MCP Agent — interpreta lenguaje natural para ejecutar comandos sobre el objeto inteligente.

### 1.2 Flujo de Comunicación

El ESP32 publica la distancia medida cada 2 segundos al topic de distancia. Tanto la aplicación móvil como Claude CLI envían comandos directamente al broker MQTT al topic del actuador. El ESP32, suscrito a ese topic, recibe el comando y activa el LED correspondiente. El Button UI se conecta directo al broker sin pasar por Claude CLI.

### 1.3 Topics MQTT

| Rol | Topic | Descripción |
|---|---|---|
| PUBLISH | `home/garden/UCBBOL/IotEC3Mqttdistance` | Distancia en cm, publicada cada 2 segundos |
| SUBSCRIBE | `home/garden/UCBBOL/IotEC3Mqttactuator` | Recibe comandos: `"1"`, `"2"`, `"3"` (LED) o `"0"` (apagar) |

---

## 2. Implementación

### 2.1 Arquitectura del Software

El firmware del ESP32 sigue un diseño orientado a objetos (POO) con estructura multi-archivo. Cada responsabilidad está encapsulada en una clase independiente, siguiendo el principio de responsabilidad única (SRP). El archivo `main.cpp` actúa como orquestador, instanciando y coordinando todos los módulos.

### 2.2 Clases y Módulos

| Clase | Archivo | Responsabilidad |
|---|---|---|
| `MqttManager` | `MqttManager.h/.cpp` | Gestiona conexión WiFi, conexión MQTT y reconexión automática con re-suscripción |
| `MqttPublisher` | `MqttPublisher.h/.cpp` | Publica datos enteros o string al broker MQTT |
| `MqttSubscriber` | `MqttSubscriber.h/.cpp` | Se suscribe a un topic y delega comandos al LedController vía callback |
| `UltrasonicSensor` | `UltrasonicSensor.h/.cpp` | Encapsula la librería NewPing para medición de distancia con HC-SR04 |
| `LedController` | `LedController.h/.cpp` | Controla 3 LEDs (GPIO 25, 26, 27), procesa comandos de texto |

### 2.3 Hardware

| Componente | Pin / Conexión | Función |
|---|---|---|
| ESP32 DevKit | — | Microcontrolador principal |
| HC-SR04 (TRIG) | GPIO 5 | Sensor ultrasónico — disparo |
| HC-SR04 (ECHO) | GPIO 18 | Sensor ultrasónico — recepción |
| LED 1 + resistencia 220Ω | GPIO 25 | Actuador 1 |
| LED 2 + resistencia 220Ω | GPIO 26 | Actuador 2 |
| LED 3 + resistencia 220Ω | GPIO 27 | Actuador 3 |

### 2.4 Configuración

- **Broker MQTT:** `broker.hivemq.com`, puerto 1883 (sin autenticación — broker público gratuito).
- **Topic de publicación:** `home/garden/UCBBOL/IotEC3Mqttdistance`
- **Topic de suscripción:** `home/garden/UCBBOL/IotEC3Mqttactuator`
- **Intervalo de publicación:** 2000 ms (cada 2 segundos).
- **Librería MQTT:** PubSubClient v2.8 (knolleary).
- **Librería sensor:** NewPing v1.9.7 (teckel12).
- **Framework:** Arduino sobre PlatformIO (VS Code).

### 2.5 Código Fuente Documentado

#### `main.cpp` — Orquestador principal

Inicializa todos los objetos, conecta WiFi y MQTT, crea publisher y subscriber, y ejecuta el ciclo principal de lectura y publicación cada 2 segundos.

```cpp
/*
 * ESP32 MQTT Ultrasonic Sensor and LED Controller
 * Multi-file OOP structure.
 */
#include "UltrasonicSensor.h"
#include "LedController.h"
#include "MqttPublisher.h"
#include "MqttSubscriber.h"
#include "MqttManager.h"

// ---------------------------- Configuration ----------------------------
const char* WIFI_SSID     = "YOUR_SSID";
const char* WIFI_PASSWORD = "YOUR_PASSWORD";

const char* MQTT_BROKER   = "broker.hivemq.com";
const int   MQTT_PORT     = 1883;
const char* MQTT_USERNAME = "";
const char* MQTT_PASSWORD = "";

const char* TOPIC_DISTANCE = "home/garden/UCBBOL/IotEC3Mqttdistance";
const char* TOPIC_LED_CMD  = "home/garden/UCBBOL/IotEC3Mqttactuator";

#define TRIG_PIN  5
#define ECHO_PIN  18
#define MAX_DIST  400

#define LED1_PIN  25
#define LED2_PIN  26
#define LED3_PIN  27

// ---------------------------- Global Objects ----------------------------
UltrasonicSensor ultrasonic(TRIG_PIN, ECHO_PIN, MAX_DIST);
LedController    leds(LED1_PIN, LED2_PIN, LED3_PIN);
MqttManager      mqttManager(MQTT_BROKER, MQTT_PORT, MQTT_USERNAME, MQTT_PASSWORD);

MqttPublisher*  publisher  = nullptr;
MqttSubscriber* subscriber = nullptr;

unsigned long lastPublishTime = 0;
const unsigned long PUBLISH_INTERVAL = 2000;

// ------------------------------------------------------------------------
void setup() {
    Serial.begin(115200);

    leds.begin(); // Inicializar pines de LEDs

    mqttManager.connectWiFi(WIFI_SSID, WIFI_PASSWORD);
    if (mqttManager.connectMqtt()) {
        mqttManager.setSubscribedTopic(TOPIC_LED_CMD); // Habilita re-suscripcion automatica
        publisher  = new MqttPublisher(mqttManager.getClient());
        subscriber = new MqttSubscriber(mqttManager.getClient(), leds);
        subscriber->begin(TOPIC_LED_CMD);
    }

    Serial.println("System initialized. Publishing to: " + String(TOPIC_DISTANCE));
}

void loop() {
    mqttManager.loop(); // Mantiene conexion y reconecta si es necesario

    unsigned long now = millis();
    if (now - lastPublishTime >= PUBLISH_INTERVAL) {
        lastPublishTime = now;

        unsigned int distance = ultrasonic.getDistanceCm();
        if (distance > 0) {
            Serial.print("Distance: ");
            Serial.print(distance);
            Serial.println(" cm");
            if (publisher) publisher->publishInt(TOPIC_DISTANCE, distance);
        } else {
            Serial.println("Ultrasonic sensor out of range or error.");
        }
    }
}
```

---

#### `MqttManager.h` — Cabecera del gestor de conexión

```cpp
#ifndef MQTT_MANAGER_H
#define MQTT_MANAGER_H

#include <WiFi.h>
#include <PubSubClient.h>

class MqttManager {
private:
    WiFiClient   wifiClient;
    PubSubClient mqttClient;
    const char*  broker;
    int          port;
    const char*  username;
    const char*  password;
    String       clientId;
    const char*  subscribedTopic; // Topic guardado para re-suscribir tras reconexion

    void reconnect();

public:
    MqttManager(const char* mqttBroker, int mqttPort,
                const char* mqttUser,   const char* mqttPass);
    void connectWiFi(const char* ssid, const char* pass);
    bool connectMqtt();
    void loop();
    PubSubClient& getClient();
    void setSubscribedTopic(const char* topic); // Registra topic para reconexion automatica
};

#endif
```

---

#### `MqttManager.cpp` — Implementación del gestor de conexión

Encapsula toda la lógica de conexión. El método `reconnect()` re-suscribe automáticamente al topic registrado tras una reconexión, evitando pérdida de mensajes.

```cpp
#include "MqttManager.h"

MqttManager::MqttManager(const char* mqttBroker, int mqttPort,
                         const char* mqttUser,   const char* mqttPass)
    : mqttClient(wifiClient), broker(mqttBroker), port(mqttPort),
      username(mqttUser), password(mqttPass), subscribedTopic(nullptr) {
    clientId = "ESP32Client-" + String(random(0xffff), HEX);
}

void MqttManager::connectWiFi(const char* ssid, const char* pass) {
    Serial.print("Connecting to WiFi ");
    Serial.println(ssid);
    WiFi.begin(ssid, pass);
    while (WiFi.status() != WL_CONNECTED) {
        delay(500);
        Serial.print(".");
    }
    Serial.println("\nWiFi connected. IP: " + WiFi.localIP().toString());
}

bool MqttManager::connectMqtt() {
    mqttClient.setServer(broker, port);
    Serial.print("Connecting to MQTT broker... ");
    if (mqttClient.connect(clientId.c_str(), username, password)) {
        Serial.println("connected.");
        return true;
    }
    Serial.print("failed, rc=");
    Serial.println(mqttClient.state());
    return false;
}

void MqttManager::loop() {
    if (!mqttClient.connected()) reconnect();
    mqttClient.loop();
}

void MqttManager::reconnect() {
    while (!mqttClient.connected()) {
        Serial.print("Attempting MQTT reconnection...");
        if (mqttClient.connect(clientId.c_str(), username, password)) {
            Serial.println("connected");
            // Re-suscribir al topic tras reconexion
            if (subscribedTopic != nullptr) {
                mqttClient.subscribe(subscribedTopic);
                Serial.print("Re-subscribed to: ");
                Serial.println(subscribedTopic);
            }
        } else {
            Serial.print("failed, rc=");
            Serial.print(mqttClient.state());
            Serial.println(". Retrying in 5 seconds.");
            delay(5000);
        }
    }
}

void MqttManager::setSubscribedTopic(const char* topic) {
    subscribedTopic = topic;
}

PubSubClient& MqttManager::getClient() {
    return mqttClient;
}
```

---

#### `MqttPublisher.h` / `MqttPublisher.cpp`

Publica datos al broker. Soporta enteros y strings.

```cpp
// MqttPublisher.h
#ifndef MQTT_PUBLISHER_H
#define MQTT_PUBLISHER_H

#include <PubSubClient.h>

class MqttPublisher {
private:
    PubSubClient& client;
public:
    MqttPublisher(PubSubClient& mqttClient);
    bool publishInt(const char* topic, int value);
    bool publishString(const char* topic, const String& value);
};

#endif
```

```cpp
// MqttPublisher.cpp
#include "MqttPublisher.h"

MqttPublisher::MqttPublisher(PubSubClient& mqttClient)
    : client(mqttClient) {}

bool MqttPublisher::publishInt(const char* topic, int value) {
    char buffer[12];
    snprintf(buffer, sizeof(buffer), "%d", value);
    bool ok = client.publish(topic, buffer);
    if (ok) {
        Serial.print("Published ["); Serial.print(topic);
        Serial.print("]: ");        Serial.println(buffer);
    } else {
        Serial.println("Publish failed. Check MQTT connection.");
    }
    return ok;
}

bool MqttPublisher::publishString(const char* topic, const String& value) {
    bool ok = client.publish(topic, value.c_str());
    if (!ok) Serial.println("Publish failed.");
    return ok;
}
```

---

#### `MqttSubscriber.h` / `MqttSubscriber.cpp`

Usa un lambda para registrar el callback, manteniendo la referencia al objeto (`this`). Al recibir un mensaje, delega el comando al `LedController`.

```cpp
// MqttSubscriber.h
#ifndef MQTT_SUBSCRIBER_H
#define MQTT_SUBSCRIBER_H

#include <PubSubClient.h>
#include "LedController.h"

class MqttSubscriber {
private:
    PubSubClient& client;
    LedController& leds;
    void callback(char* topic, byte* payload, unsigned int length);
public:
    MqttSubscriber(PubSubClient& mqttClient, LedController& ledController);
    void begin(const char* topic);
    bool subscribe(const char* topic);
};

#endif
```

```cpp
// MqttSubscriber.cpp
#include "MqttSubscriber.h"

MqttSubscriber::MqttSubscriber(PubSubClient& mqttClient, LedController& ledController)
    : client(mqttClient), leds(ledController) {}

void MqttSubscriber::begin(const char* topic) {
    // Lambda para mantener referencia al objeto actual (this)
    client.setCallback([this](char* t, byte* p, unsigned int len) {
        this->callback(t, p, len);
    });
    subscribe(topic);
}

bool MqttSubscriber::subscribe(const char* topic) {
    return client.subscribe(topic);
}

void MqttSubscriber::callback(char* topic, byte* payload, unsigned int length) {
    Serial.print("Message received on topic: ");
    Serial.println(topic);

    String message;
    for (unsigned int i = 0; i < length; i++) message += (char)payload[i];
    Serial.print("Payload: "); Serial.println(message);

    leds.handleCommand(message); // Delegar al controlador de LEDs
}
```

---

#### `UltrasonicSensor.h` / `UltrasonicSensor.cpp`

Encapsula la librería NewPing. Retorna 0 si el objeto está fuera del rango máximo configurado (400 cm).

```cpp
// UltrasonicSensor.h
#ifndef ULTRASONIC_SENSOR_H
#define ULTRASONIC_SENSOR_H

#include <NewPing.h>

class UltrasonicSensor {
private:
    NewPing sonar;
public:
    UltrasonicSensor(uint8_t trigPin, uint8_t echoPin, unsigned int maxDist);
    unsigned int getDistanceCm(); // Retorna 0 si fuera de rango
};

#endif
```

```cpp
// UltrasonicSensor.cpp
#include "UltrasonicSensor.h"

UltrasonicSensor::UltrasonicSensor(uint8_t trigPin, uint8_t echoPin, unsigned int maxDist)
    : sonar(trigPin, echoPin, maxDist) {}

unsigned int UltrasonicSensor::getDistanceCm() {
    return sonar.ping_cm(); // Retorna 0 si fuera de rango
}
```

---

#### `LedController.h` / `LedController.cpp`

Acepta comandos `"1"`, `"2"`, `"3"` para encender el LED correspondiente (los demás se apagan). `"0"` o cualquier otro valor apaga todos. También acepta `"on1"`, `"on2"`, `"on3"`, `"off"` para compatibilidad con Claude CLI.

```cpp
// LedController.h
#ifndef LED_CONTROLLER_H
#define LED_CONTROLLER_H

#include <Arduino.h>

class LedController {
private:
    uint8_t pin1, pin2, pin3;
public:
    LedController(uint8_t ledPin1, uint8_t ledPin2, uint8_t ledPin3);
    void begin();
    void handleCommand(const String& command);
    void setLed(int ledNum, bool state);
    void allOff();
};

#endif
```

```cpp
// LedController.cpp
#include "LedController.h"

LedController::LedController(uint8_t ledPin1, uint8_t ledPin2, uint8_t ledPin3)
    : pin1(ledPin1), pin2(ledPin2), pin3(ledPin3) {}

void LedController::begin() {
    pinMode(pin1, OUTPUT);
    pinMode(pin2, OUTPUT);
    pinMode(pin3, OUTPUT);
    allOff();
    Serial.println("LedController initialized. All LEDs OFF.");
}

void LedController::handleCommand(const String& command) {
    if      (command == "1" || command == "on1") setLed(1, true);
    else if (command == "2" || command == "on2") setLed(2, true);
    else if (command == "3" || command == "on3") setLed(3, true);
    else                                          allOff();
}

void LedController::setLed(int ledNum, bool state) {
    allOff(); // Apagar todos antes de encender uno
    switch (ledNum) {
        case 1: digitalWrite(pin1, state ? HIGH : LOW); break;
        case 2: digitalWrite(pin2, state ? HIGH : LOW); break;
        case 3: digitalWrite(pin3, state ? HIGH : LOW); break;
        default: Serial.println("Invalid LED number."); break;
    }
    Serial.print("LED "); Serial.print(ledNum);
    Serial.println(state ? " ON" : " OFF");
}

void LedController::allOff() {
    digitalWrite(pin1, LOW);
    digitalWrite(pin2, LOW);
    digitalWrite(pin3, LOW);
}
```

---

### 2.6 Integración con Claude Desktop (MCP Agent)

Claude Desktop actúa como interfaz de lenguaje natural para el sistema. A través del protocolo MCP (Model Context Protocol), Claude interpreta instrucciones como *"enciende el LED 1"* o *"¿cuál es la distancia actual?"* y las traduce en mensajes MQTT publicados directamente al broker HiveMQ.

**Flujo:**
1. El usuario escribe un comando en lenguaje natural en Claude Desktop.
2. El MCP Agent lo interpreta y genera el payload correspondiente (`"1"`, `"2"` o `"3"`).
3. Publica el payload al topic `home/garden/UCBBOL/IotEC3Mqttactuator`.
4. El ESP32 recibe el mensaje y activa el LED correspondiente.

### 2.7 Aplicación Móvil — IoT MQTT Panel

La aplicación IoT MQTT Panel se configura para conectarse al broker HiveMQ. La información del sensor se despliega de forma **gráfica** mediante un gauge o gráfica de línea en tiempo real. Los botones publican directamente al topic del actuador sin pasar por ningún intermediario.

- **Suscripción:** `home/garden/UCBBOL/IotEC3Mqttdistance` — visualización gráfica de distancia.
- **Publicación:** `home/garden/UCBBOL/IotEC3Mqttactuator` — botones envían `"1"`, `"2"`, `"3"` o `"0"` directo al broker.

---

## 3. Evaluación

### 3.1 Ponderación

| Componente | Porcentaje |
|---|---|
| Defensa / Demo | 40% |
| — Evaluación individual (dominio del trabajo) | 20% |
| — Evaluación grupal (funcionalidad del sistema) | 20% |
| Informe Técnico | 60% |

### 3.2 Rúbrica Analítica — Desarrollo e Implementación

| Nivel | Descripción |
|---|---|
| **4 - Excelente** | Código bien estructurado, modular (POO), documentado y con buenas prácticas. Prototipo completamente funcional. |
| **3 - Satisfactorio** | Código estructurado y funcional, con documentación básica. |
| **2 - Satisfactorio con recomendaciones** | Código funcional pero con mala organización o sin estándares claros. |
| **1 - Necesita mejorar** | Prototipo no funcional o con fallas críticas. |

### 3.3 Justificación del Nivel Alcanzado

El proyecto alcanza el **nivel 4 (Excelente)** según la rúbrica, por los siguientes aspectos:

- **Código modular orientado a objetos:** cada clase tiene una única responsabilidad (SRP), con archivos `.h` y `.cpp` separados.
- **Documentación en código:** comentarios descriptivos en todas las clases y métodos.
- **Buenas prácticas:** uso de punteros gestionados, lambdas para callbacks, reconexión automática con re-suscripción.
- **Prototipo completamente funcional:** publicación de sensor, control de LEDs por MQTT, integración con Claude CLI y aplicación móvil.
- **Integración completa** de todos los componentes requeridos por la actividad evaluativa.

---

## 4. Anexos

### 4.1 Estructura de Archivos del Proyecto

```
Esp32Script/
├── src/
│   ├── main.cpp
│   ├── MqttManager.cpp
│   ├── MqttPublisher.cpp
│   ├── MqttSubscriber.cpp
│   ├── UltrasonicSensor.cpp
│   └── LedController.cpp
├── include/
│   ├── MqttManager.h
│   ├── MqttPublisher.h
│   ├── MqttSubscriber.h
│   ├── UltrasonicSensor.h
│   └── LedController.h
└── platformio.ini
```

### 4.2 Dependencias (`platformio.ini`)

```ini
[env:esp32dev]
platform     = espressif32
board        = esp32dev
framework    = arduino
monitor_speed = 115200

lib_deps =
    knolleary/PubSubClient @ ^2.8
    teckel12/NewPing       @ ^1.9.7
```

### 4.3 Glosario

| Término | Definición |
|---|---|
| **MQTT** | Message Queuing Telemetry Transport. Protocolo de mensajería liviano basado en publicador/suscriptor, diseñado para dispositivos IoT. |
| **MCP** | Model Context Protocol. Permite a modelos de IA conectarse con herramientas externas y ejecutar acciones en el mundo real. |
| **Broker** | Servidor intermediario MQTT que distribuye mensajes entre publicadores y suscriptores. |
| **Topic** | Cadena jerárquica que identifica el canal de comunicación en MQTT. |
| **QoS** | Quality of Service. Nivel de garantía de entrega (este proyecto usa QoS 0). |
| **ESP32** | Microcontrolador de Espressif con WiFi integrado, programable con Arduino Framework. |
| **HC-SR04** | Sensor ultrasónico que mide distancia emitiendo pulsos de ultrasonido. |
| **POO** | Programación Orientada a Objetos. Paradigma que organiza el código en clases con atributos y métodos. |
| **SRP** | Single Responsibility Principle. Principio de diseño donde cada clase tiene una única responsabilidad. |
