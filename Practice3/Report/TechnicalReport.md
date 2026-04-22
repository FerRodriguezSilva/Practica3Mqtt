# Práctica 3 – Sistema IoT con MQTT, MCP y Asistente Artificial

## Integrantes
    Gabriel Herrera  
    Nicole Gomez  
    Fernando Rodriguez  

## 1. Requerimientos Funcionales

El sistema deberá poder utilizar la tecnología de comunicación Mqtt para poder recibir y mandar datos a una interfaz móvil, y por medio de un servidor MCP conectarse a un asistente Artificial, en este caso Claude.

Este se compone de 3 elementos en si un esp32 el cual denominaremos main, una interfaz en la aplicación móvil IoT Mqtt Panel, y un servidor MCP que funcionara como una skill en Claude. Todos estos tienen acceso a la lectura y escritura en dos topicos para sus respectivas funciones.

El primer tópico es “home/garden/UCBBOL/IotEC3Mqttactuator”, en este se publica la orden que el esp32 utiliza para cambiar la activación de uno solo de los leds del sistema, este variando según lo que quiera el usuario. Estos son leídos por el esp32, y son únicamente publicados cuando un usuario lo requiere.

El segundo tópico es “home/garden/UCBBOL/IotEC3Mqttdistance” en este se publica exclusivamente datos los cuales pertenezcan al sensor del esp32, y tanto la aplicación móvil, como Claude solo pueden leer el topico.

La aplicación móvil además es capas de revisar y graficar los últimos datos del topico, estos siendo guardados en la propia aplicación, no en el topico en si.

## 2. Requerimientos No Funcionales

Para el topico de “actuator” solo se deberá publicar los siguientes números, esto para simplificar y comprimir lo mas posible los datos y evitar errores:

| Color | Numero publicado |
|-------|------------------|
| Rojo  | 2                |
| Azul  | 1                |
| Verde | 3                |

Cualquier otro dato publicado dentro de este topico será interpretado como un comando para apagar todos los leds.

En cuanto a las capacidades del asistente virtual se puede generar comandos simples para encenderlo, y aunque no probado a profundidad se pueden usar para generar pequeñas secuencias del mismo trabajo.

La aplicación móvil solo tiene botones para encender cada uno de los leds y luego apagarlos todos del todo, no pueden activarse en ningún caso dos o mas leds al mismo tiempo, y además, en cuanto a velocidad se determino lo siguiente.

El mensaje mqtt enviado es casi instantáneo, desde 0.1 segundos a medio, pero en el caso de usar Claude se relantiza hasta 10 segundos debido a su propia interpretación del código interno del servidor MQT

Para el topico de “distance” se le implemento un sistema para que solo transmita datos cuando el sensor cambia entre ciertos rangos, y además tiene limites del mismo, todo ello para limitar y evitar sobrecargar la red con redundancia de datos, en Claude solo podrá ver el ultimo guardado debido a que un registro en esta interfaz no fue planeado.

Por otro lado en la aplicación móvil se puede registrar los últimos datos obtenidos del mismo y los limites para el salto entre rangos son los siguientes:

| Rango      |
|------------|
| 0 a 10     |
| 10 a 20    |
| 20 a 30    |
| Cualquier otro |

En cualquier otro rango no se manda ningún dato, y cada ves que mande un dato se mandara la ultima medida generada por el Main del ESP32 para su posteo en el Mqtt.

## 3. Arquitectura del Sistema

El sistema sigue una arquitectura basada en MQTT con un patrón publicador-suscriptor:

- **ESP32 (Main)** → Actúa como publicador de datos del sensor y suscriptor de comandos para los LEDs.
- **Aplicación Móvil (IoT MQTT Panel)** → Publica comandos de usuario y suscribe al tópico de distancia para visualización.
- **Servidor MCP** → Actúa como puente entre Claude y el broker MQTT, permitiendo control por lenguaje natural.

### Componentes del sistema:
- **Broker MQTT**: HiveMQ (broker.hivemq.com:1883)
- **Tópico de actuadores**: `home/garden/UCBBOL/IotEC3Mqttactuator`
- **Tópico de sensores**: `home/garden/UCBBOL/IotEC3Mqttdistance`

## 4. Documentación del Código

### Servidor MCP (Python)

**Clase/Archivo: McpServer.py**

Gestiona la comunicación entre Claude y el broker MQTT mediante el framework FastMCP.

#### Herramientas principales:

- `encender_led(color)`: Enciende un LED por nombre de color (azul, rojo, verde).
- `encender_led_por_numero(led_number)`: Enciende LED por número (1=azul, 2=rojo, 3=verde).
- `apagar_todos_los_leds()`: Apaga todos los LEDs.
- `parpadear_led(color, veces, intervalo_ms)`: Parpadea un LED un número específico de veces.
- `secuencia_leds()`: Ejecuta secuencia AZUL → ROJO → VERDE.
- `obtener_distancia()`: Obtiene la última lectura del sensor ultrasónico.
- `obtener_estado_completo()`: Muestra el estado completo del sistema.
- `monitorear_distancia(duracion_segundos)`: Monitorea el sensor por un tiempo determinado.

#### Formato de comandos MQTT:
- Comando "1" → Enciende LED Azul
- Comando "2" → Enciende LED Rojo
- Comando "3" → Enciende LED Verde
- Cualquier otro valor → Apaga todos los LEDs

### Dispositivo ESP32 (C++)


#### Clases principales:

**LedController**: Controla los 3 LEDs independientes.
- `allOff()`: Apaga todos los LEDs.
- `handleCommand(command)`: Procesa comandos (1,2,3 u otro).

**UltrasonicSensor**: Maneja el sensor HC-SR04.
- `getDistanceCm()`: Retorna distancia en centímetros.

**MqttManager**: Gestiona conexión WiFi y MQTT.
- `connectWiFi()`: Conecta a red WiFi.
- `connectMqtt()`: Conecta al broker MQTT.
- `reconnect()`: Reconección automática ante fallos.

**MqttPublisher**: Publica mensajes al broker.
- `publishInt(topic, value)`: Publica valores enteros.

**MqttSubscriber**: Suscribe y recibe comandos.
- Callback que ejecuta `handleCommand()` al recibir mensajes.

#### Flujo de operación del ESP32:
1. Conectar a WiFi y MQTT.
2. Suscribirse al tópico de actuadores.
3. Cada 2 segundos, medir distancia y publicar en tópico de sensores.
4. Al recibir comando, ejecutar acción en LEDs.

## 5. Componentes Utilizados

- 1x ESP32 (Wemos D1 R32 / ESP32 Dev Module)
- 1x Sensor ultrasónico HC-SR04
- 3x LEDs (Azul, Rojo, Verde)
- 3x Resistencias de 220Ω
- Cables para conexiones
- 1x Protoboard
- Broker MQTT público (HiveMQ)

## 6. Esquema de Conexiones

### Sensor HC-SR04:
| Pin Sensor | Pin ESP32 |
|------------|-----------|
| VCC        | 5V        |
| GND        | GND       |
| TRIG       | GPIO5     |
| ECHO       | GPIO18    |

### LEDs (cátodo común):
| LED   | Pin ESP32 | Resistencia |
|-------|-----------|-------------|
| Azul  | GPIO25    | 220Ω        |
| Rojo  | GPIO26    | 220Ω        |
| Verde | GPIO27    | 220Ω        |

## 7. Resultados

El sistema funcionó correctamente, logrando:
- Comunicación MQTT estable entre ESP32, aplicación móvil y servidor MCP.
- Control de LEDs por lenguaje natural a través de Claude.
- Monitoreo de distancia desde la app y desde el asistente.

## 8. Pruebas del Sistema

Para la recolección de datos y distintas pruebas del sistema se eligieron dos categorías, velocidad y entendimiento de una orden, este ultimo siendo exclusivo para el uso de Claude.

Por lo cual en su uso de la aplicación móvil se vieron estos resultados regulares, junto con los de Claude para una comparación.

| Comando               | Velocidad App [seg] | Velocidad Claude [seg] |
|-----------------------|---------------------|------------------------|
| "Encender Led Rojo"   | 0,5                 | 5                      |
| "Encender Led Azul"   | 0,5                 | 7                      |
| "Encender Led Verde"  | 0,5                 | 6                      |
| "Leer distancia"      | 0,5                 | 10                     |

Estos datos demuestran una anomalia que puede ser resuelta por una simple explicación, Claude tarda en generar el entendimiento de la orden dada y dependiendo de su conexión a internet esta acelerara o bajara su velocidad de trabajo.

Por lo cual se generó también la siguiente prueba:
# ver en la carpeta de anexos anexos la tabla de prueba |

Dándole ordenes que no son simples se vio que aunque llego a entender el contexto, esto fue después de varios intentos, y además confirmar cual fue la orden dada. Esto no siendo explorado debido a que aunque fascinante, no es el enfoque del trabajo.

### Pruebas adicionales realizadas:

| Prueba | Comando enviado | Resultado esperado | Resultado obtenido |
|--------|----------------|--------------------|--------------------|
| 1      | "1" (MQTT)      | LED Azul ON        | Correcto           |
| 2      | "2" (MQTT)      | LED Rojo ON        | Correcto           |
| 3      | "3" (MQTT)      | LED Verde ON       | Correcto           |
| 4      | "off" (MQTT)    | Todos apagados     | Correcto           |
| 5      | Distancia 5 cm  | Publica 5 cm       | Correcto           |
| 6      | Distancia 15 cm | Publica 15 cm      | Correcto           |

## 9. Conclusiones

El sistema cumple correctamente su objetivo:
- Comunicación estable mediante MQTT.
- Control efectivo de LEDs desde aplicación móvil y Claude.
- Monitoreo de distancia en tiempo real en la aplicacion movil, con un envio de datos mas retrasado al servidor mcp.

### Conclusiones cuantitativas:
- Baja latencia en comunicación directa (app → ESP32).
- Mayor latencia en interacción con Claude (hasta 10 segundos).
- Alta confiabilidad en red local.

## 10. Recomendaciones

- Implementar reconexión automática en el ESP32 para el broker MQTT (ya implementado parcialmente).
- Promediar múltiples lecturas del sensor ultrasónico para reducir ruido.
- Optimizar el servidor MCP para reducir latencia con Claude.
- Agregar registro histórico de distancias en el servidor MCP.
- Implementar estado de LEDs publicable para conocer el estado actual desde Claude.


