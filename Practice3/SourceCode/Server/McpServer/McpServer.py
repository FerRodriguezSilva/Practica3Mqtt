import paho.mqtt.client as mqtt
import time
import json
from mcp.server.fastmcp import FastMCP

# Initialize FastMCP server
mcp = FastMCP("esp32_led_controller")

# MQTT Configuration (MATCH YOUR ESP32 SETUP)
MQTT_BROKER = "broker.hivemq.com"
MQTT_PORT = 1883
MQTT_TOPIC_LED = "home/garden/UCBBOL/IotEC3Mqttactuator"
MQTT_TOPIC_DISTANCE = "home/garden/UCBBOL/IotEC3Mqttdistance"

# LED Color to Number Mapping (ESP32 configuration)
# ESP32: AZUL=1 (pin25), ROJO=2 (pin26), VERDE=3 (pin27)
LED_MAPPING = {
    "azul": 1,
    "blue": 1,
    "rojo": 2,
    "red": 2,
    "verde": 3,
    "green": 3
}

# Global variable to store the latest distance reading
latest_distance = None
last_distance_time = 0
distance_received = False

# MQTT Callback functions
def on_connect(client, userdata, flags, rc):
    print(f"Connected to MQTT broker with result code {rc}")
    # Subscribe to distance topic
    result = client.subscribe(MQTT_TOPIC_DISTANCE)
    print(f"Subscribed to {MQTT_TOPIC_DISTANCE} with result {result}")
    print("Waiting for distance data from ESP32...")

def on_message(client, userdata, msg):
    global latest_distance, last_distance_time, distance_received
    print(f"Message received on topic: {msg.topic}")
    
    if msg.topic == MQTT_TOPIC_DISTANCE:
        try:
            payload_str = msg.payload.decode()
            print(f"Raw payload: {payload_str}")
            distance_cm = int(payload_str)
            latest_distance = distance_cm
            last_distance_time = time.time()
            distance_received = True
            print(f"Distance stored: {latest_distance} cm")
        except ValueError as e:
            print(f"Error parsing distance as int: {e}")
        except Exception as e:
            print(f"Error processing distance message: {e}")
    else:
        print(f"Unhandled topic: {msg.topic} with payload: {msg.payload.decode()}")

# Setup MQTT Client with callbacks
mqtt_client = mqtt.Client()
mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message

print(f"Connecting to MQTT broker {MQTT_BROKER}:{MQTT_PORT}...")
mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
mqtt_client.loop_start()

# Wait a moment for connection and subscription to complete
time.sleep(2)

@mcp.tool()
def encender_led(color: str) -> str:
    """Turn on a specific LED by color.
    
    Args:
        color: Color of LED to turn on ("azul", "rojo", or "verde")
               Also accepts English: "blue", "red", "green"
    """
    # Normalize color input
    color_lower = color.lower().strip()
    
    # Check if color exists in mapping
    if color_lower not in LED_MAPPING:
        available = ", ".join(LED_MAPPING.keys())
        return f"Error: Color '{color}' no valido. Colores disponibles: {available}"
    
    # Get the correct LED number for ESP32
    led_number = LED_MAPPING[color_lower]
    
    # Send command to ESP32
    command = str(led_number)
    result = mqtt_client.publish(MQTT_TOPIC_LED, command)
    print(f"Published command '{command}' to {MQTT_TOPIC_LED}, result: {result}")
    
    # Map back to Spanish color name for response
    color_name = next((k for k, v in LED_MAPPING.items() if v == led_number and k in ["azul", "rojo", "verde"]), color_lower)
    
    return f"LED {color_name.upper()} encendido (comando: {command})"

@mcp.tool()
def encender_led_por_numero(led_number: int) -> str:
    """Turn on a specific LED by number.
    
    Args:
        led_number: LED number to turn on (1=azul, 2=rojo, 3=verde)
    """
    if led_number not in [1, 2, 3]:
        return f"Error: Numero de LED debe ser 1 (azul), 2 (rojo), o 3 (verde)"
    
    # Send command to ESP32
    mqtt_client.publish(MQTT_TOPIC_LED, str(led_number))
    
    # Map number to color name
    color_map = {1: "AZUL", 2: "ROJO", 3: "VERDE"}
    color = color_map[led_number]
    
    return f"LED {color} encendido (numero: {led_number})"

@mcp.tool()
def apagar_todos_los_leds() -> str:
    """Turn off all LEDs."""
    # Send any command other than "1", "2", "3" to turn all off
    mqtt_client.publish(MQTT_TOPIC_LED, "off")
    return "Todos los LEDs apagados"

@mcp.tool()
def parpadear_led(color: str, veces: int = 3, intervalo_ms: int = 500) -> str:
    """Blink a specific LED multiple times.
    
    Args:
        color: Color of LED to blink ("azul", "rojo", or "verde")
        veces: Number of times to blink (default: 3)
        intervalo_ms: Interval in milliseconds between blinks (default: 500)
    """
    # Normalize color input
    color_lower = color.lower().strip()
    
    # Check if color exists in mapping
    if color_lower not in LED_MAPPING:
        available = ", ".join(LED_MAPPING.keys())
        return f"Error: Color '{color}' no valido. Colores disponibles: {available}"
    
    # Get the correct LED number for ESP32
    led_number = LED_MAPPING[color_lower]
    
    # Get color name for response
    color_name = next((k for k, v in LED_MAPPING.items() if v == led_number and k in ["azul", "rojo", "verde"]), color_lower)
    
    result = f"Parpadeando LED {color_name.upper()} {veces} veces...\n"
    
    for i in range(veces):
        mqtt_client.publish(MQTT_TOPIC_LED, str(led_number))
        time.sleep(intervalo_ms / 1000.0)
        mqtt_client.publish(MQTT_TOPIC_LED, "off")
        if i < veces - 1:
            time.sleep(intervalo_ms / 1000.0)
    
    return f"LED {color_name.upper()} parpadeo {veces} veces"

@mcp.tool()
def secuencia_leds() -> str:
    """Run a sequence: AZUL -> ROJO -> VERDE sequentially."""
    result = "Ejecutando secuencia: AZUL -> ROJO -> VERDE\n"
    
    for num, color in [(1, "AZUL"), (2, "ROJO"), (3, "VERDE")]:
        mqtt_client.publish(MQTT_TOPIC_LED, str(num))
        result += f"  LED {color} encendido\n"
        time.sleep(0.5)
        mqtt_client.publish(MQTT_TOPIC_LED, "off")
        if num < 3:
            time.sleep(0.3)
    
    return result + "Secuencia completa"

@mcp.tool()
def obtener_distancia() -> str:
    """Get the latest distance measurement from the ultrasonic sensor in centimeters."""
    global latest_distance, distance_received, last_distance_time
    
    if not distance_received:
        return "No se ha recibido ninguna lectura de distancia. Verifica que el ESP32 este publicando datos al topic: " + MQTT_TOPIC_DISTANCE
    
    if latest_distance is None:
        return "Esperando primera lectura del sensor ultrasonico..."
    
    # Check if data is recent (less than 5 seconds old)
    time_since_last = time.time() - last_distance_time
    if time_since_last > 5:
        return f"Advertencia: La ultima lectura de distancia tiene {time_since_last:.0f} segundos. Distancia: {latest_distance} cm"
    
    if latest_distance <= 0:
        return f"Error: Lectura de distancia invalida. El sensor puede estar fuera de rango. Valor: {latest_distance} cm"
    elif latest_distance > 400:
        return f"Advertencia: La distancia medida excede el rango maximo (400cm). Valor: {latest_distance} cm"
    else:
        return f"Distancia actual: {latest_distance} centimetros"

@mcp.tool()
def obtener_estado_completo() -> str:
    """Get complete system status including LED state and latest distance reading."""
    global latest_distance, last_distance_time, distance_received
    
    status = "=== ESTADO COMPLETO DEL SISTEMA ===\n\n"
    
    # MQTT Connection Status
    status += "[CONEXION MQTT]\n"
    if mqtt_client.is_connected():
        status += f"  Broker: {MQTT_BROKER}:{MQTT_PORT} - CONECTADO\n"
        status += f"  Topic LED: {MQTT_TOPIC_LED}\n"
        status += f"  Topic Distancia: {MQTT_TOPIC_DISTANCE}\n"
        status += f"  Suscrito a distancia: SI\n"
    else:
        status += "  Broker MQTT: DESCONECTADO\n"
    
    # Distance Sensor Status
    status += "\n[SENSOR ULTRASONICO]\n"
    if not distance_received:
        status += "  Estado: Esperando datos del sensor...\n"
        status += f"  Verifica que el ESP32 este publicando a: {MQTT_TOPIC_DISTANCE}\n"
    else:
        status += f"  Ultima distancia: {latest_distance} cm\n"
        time_since_last = time.time() - last_distance_time
        status += f"  Ultima actualizacion: Hace {time_since_last:.1f} segundos\n"
        
        if latest_distance < 10:
            status += "  Advertencia: Objeto muy cerca (menos de 10cm)\n"
        elif latest_distance > 300:
            status += "  Nota: Objeto muy lejos o sin obstaculo\n"
        else:
            status += "  Estado: Operacion normal\n"
    
    # LED Configuration Status
    status += "\n[CONFIGURACION DE LEDS]\n"
    status += "  AZUL  -> comando '1' (pin 25)\n"
    status += "  ROJO  -> comando '2' (pin 26)\n"
    status += "  VERDE -> comando '3' (pin 27)\n"
    status += "  Nota: El ESP32 no publica el estado actual de los LEDs\n"
    
    return status

@mcp.tool()
def monitorear_distancia(duracion_segundos: int = 10) -> str:
    """Monitor distance sensor for a specified duration.
    
    Args:
        duracion_segundos: Duration in seconds to monitor (default: 10)
    """
    global latest_distance, last_distance_time
    
    result = f"Monitoreando distancia por {duracion_segundos} segundos...\n"
    result += "=" * 50 + "\n"
    
    start_time = time.time()
    readings = []
    last_recorded_distance = latest_distance
    
    while time.time() - start_time < duracion_segundos:
        if latest_distance != last_recorded_distance and latest_distance is not None:
            last_recorded_distance = latest_distance
            readings.append(latest_distance)
            result += f"Tiempo: {time.time() - start_time:.1f}s -> Distancia: {latest_distance} cm\n"
        time.sleep(0.5)  # Check every half second
    
    # Calculate statistics
    if readings:
        avg_distance = sum(readings) / len(readings)
        min_distance = min(readings)
        max_distance = max(readings)
        
        result += "\n" + "=" * 50 + "\n"
        result += "RESUMEN DEL MONITOREO:\n"
        result += f"  Lecturas tomadas: {len(readings)}\n"
        result += f"  Distancia promedio: {avg_distance:.1f} cm\n"
        result += f"  Distancia minima: {min_distance} cm\n"
        result += f"  Distancia maxima: {max_distance} cm\n"
    else:
        result += "\nNo se recibieron lecturas de distancia durante el monitoreo.\n"
        result += "Verifica que el ESP32 este publicando datos correctamente.\n"
    
    return result

@mcp.tool()
def test_mqtt_connection() -> str:
    """Test MQTT connection and subscription status."""
    status = f"Testing MQTT connection to {MQTT_BROKER}:{MQTT_PORT}\n"
    status += f"Connected: {mqtt_client.is_connected()}\n"
    status += f"Distance topic: {MQTT_TOPIC_DISTANCE}\n"
    status += f"Distance received: {distance_received}\n"
    if distance_received:
        status += f"Last distance: {latest_distance} cm at {time.ctime(last_distance_time)}\n"
    else:
        status += "No distance data received yet. Check ESP32 is running and publishing.\n"
    return status

def main():
    print("Servidor MCP para Control de LEDs y Sensor Ultrasonico ESP32 Iniciado...")
    print(f"Broker MQTT: {MQTT_BROKER}:{MQTT_PORT}")
    print(f"Topic de control LED: {MQTT_TOPIC_LED}")
    print(f"Topic de distancia: {MQTT_TOPIC_DISTANCE}")
    print("\nMapeo de LEDs:")
    print("   AZUL  -> comando '1' (pin 25)")
    print("   ROJO  -> comando '2' (pin 26)")
    print("   VERDE -> comando '3' (pin 27)")
    print("\nHerramientas disponibles:")
    print("   - Control de LEDs (encender, apagar, parpadear, secuencia)")
    print("   - obtener_distancia() - Lectura actual del sensor")
    print("   - obtener_estado_completo() - Estado completo del sistema")
    print("   - monitorear_distancia() - Monitoreo por tiempo definido")
    print("   - test_mqtt_connection() - Verificar conexion MQTT")
    mcp.run(transport="stdio")

if __name__ == "__main__":
    main()