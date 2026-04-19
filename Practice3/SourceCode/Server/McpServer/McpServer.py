import paho.mqtt.client as mqtt
import time
from mcp.server.fastmcp import FastMCP

# Initialize FastMCP server
mcp = FastMCP("esp32_led_controller")

# MQTT Configuration (MATCH YOUR ESP32 SETUP)
MQTT_BROKER = "broker.hivemq.com"
MQTT_PORT = 1883
MQTT_TOPIC_LED = "home/garden/UCBBOL/IotEC3Mqttactuator"

# LED Color to Number Mapping (ESP32 configuration)
# ESP32: AZUL=1, ROJO=2, VERDE=3
LED_MAPPING = {
    "azul": 1,
    "blue": 1,
    "rojo": 2,
    "red": 2,
    "verde": 3,
    "green": 3
}

# MQTT Client
mqtt_client = mqtt.Client()
mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
mqtt_client.loop_start()

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
    mqtt_client.publish(MQTT_TOPIC_LED, command)
    
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
    return f"Todos los LEDs apagados"

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
def estado_leds() -> str:
    """Get the current status information of the LED controller."""
    return """
    Estado del Controlador de LEDs:
    - Broker MQTT: broker.hivemq.com
    - Topic de control: home/garden/UCBBOL/IotEC3Mqttactuator
    - Topic de distancia: home/garden/UCBBOL/IotEC3Mqttdistance
    
    Mapeo de LEDs:
    - AZUL  -> comando "1" (pin 25)
    - ROJO  -> comando "2" (pin 26)  
    - VERDE -> comando "3" (pin 27)
    
    Comandos: Enviar "1", "2", "3" para encender LED especifico
    Cualquier otro comando apaga todos los LEDs
    """

def main():
    print("Servidor MCP para Control de LEDs ESP32 Iniciado...")
    print(f"Broker MQTT: {MQTT_BROKER}:{MQTT_PORT}")
    print(f"Topic de control: {MQTT_TOPIC_LED}")
    print("\nMapeo de LEDs:")
    print("   AZUL  -> comando '1'")
    print("   ROJO  -> comando '2'")
    print("   VERDE -> comando '3'")
    mcp.run(transport="stdio")

if __name__ == "__main__":
    main()