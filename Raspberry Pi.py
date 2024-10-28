import socket 
import threading
import RPi.GPIO as GPIO
import time

# Define UDP settings
UDP_IP = "<broadcast>"
UDP_PORT = 4210
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST,1)

# Define thresholds
low_threshold = 400
high_threshold = 700
last_msg = time.time()
need_flash = False
collecting_data = False

lock = threading.Lock()

# GPIO pin setup
BUTTON_PIN = 15  
LED_RED = 27      
LED_YELLOW = 22   
LED_GREEN = 23   
LED_WHITE = 24   

# Dictionary to store data from each ESP8266 with timestamps
esp_data = {}
EXPECTED_ESP_COUNT = 3  # We expect exactly 3 ESPs
ESP_TIMEOUT = 10  # Time in seconds before considering an ESP disconnected

def receive():
    """
    Continuously listens for data from the UDP socket.
    Tracks data from each unique ESP8266 separately.
    """
    while True:
        data, addr = sock.recvfrom(1024)
        if collecting_data:
            received = int(data.decode())
            sender_ip = addr[0]
            
            with lock:
                # Initialize or update data for this ESP
                esp_data[sender_ip] = {
                    'value': received,
                    'last_seen': time.time()
                }
                
                print(f"Received message from {sender_ip}: {received}")
                print(f"Active ESP count: {len(esp_data)}")
                
                # Calculate average only using active ESPs
                if esp_data:
                    avg_value = sum(d['value'] for d in esp_data.values()) / len(esp_data)
                    print(f"Average from {len(esp_data)} active ESP(s): {avg_value}")
                    change_LED(int(avg_value))
            
            global last_msg
            with lock:
                last_msg = time.time()
        else:
            print("Data received but not processing as collecting_data is False")

def query_specific_esp(esp_ip):
    """
    Sends a specific query to a disconnected ESP.
    """
    query_message = f"Query_{esp_ip}"
    print(f"Querying disconnected ESP at {esp_ip}")
    sock.sendto(query_message.encode(), (UDP_IP, UDP_PORT))

def packet_lost_detect():
    """
    Detects if no data has been received for over 10 seconds.
    Also handles specific ESP disconnection detection.
    """
    message_shown = False
    while True:
        if collecting_data:
            current_time = time.time()
            
            with lock:
                # Check each ESP's last seen timestamp
                disconnected_esps = []
                for esp_ip, data in list(esp_data.items()):
                    if current_time - data['last_seen'] > ESP_TIMEOUT:
                        disconnected_esps.append(esp_ip)
                        print(f"ESP8266 at {esp_ip} disconnected")
                
                # Only handle disconnections if we previously had all 3 ESPs
                if len(esp_data) == EXPECTED_ESP_COUNT and disconnected_esps:
                    for esp_ip in disconnected_esps:
                        query_specific_esp(esp_ip)
                        del esp_data[esp_ip]
                
                # Set flash warning if any ESPs are disconnected
                global need_flash
                if len(esp_data) < EXPECTED_ESP_COUNT:
                    need_flash = True
                    if not message_shown:
                        print(f"Warning: Only {len(esp_data)} ESPs connected out of {EXPECTED_ESP_COUNT}")
                        message_shown = True
                else:
                    need_flash = False
                    message_shown = False

        time.sleep(1)  # Check every second

def flash_LED():
    while True:
        if need_flash:
            GPIO.output(LED_WHITE, GPIO.LOW)
            time.sleep(0.25)
            GPIO.output(LED_WHITE, GPIO.HIGH)
            time.sleep(0.25)

def change_LED(val):
    if val > high_threshold:
        GPIO.output(LED_RED, GPIO.HIGH)
        GPIO.output(LED_GREEN, GPIO.HIGH)
        GPIO.output(LED_YELLOW, GPIO.HIGH)
    elif val < low_threshold:
        GPIO.output(LED_RED, GPIO.LOW)
        GPIO.output(LED_GREEN, GPIO.LOW)
        GPIO.output(LED_YELLOW, GPIO.HIGH)
    else:
        GPIO.output(LED_RED, GPIO.HIGH)
        GPIO.output(LED_GREEN, GPIO.LOW)
        GPIO.output(LED_YELLOW, GPIO.HIGH)

def button_monitor():
    global collecting_data, last_msg, need_flash
    while True:
        if GPIO.input(BUTTON_PIN) == GPIO.HIGH:
            if collecting_data:
                print("Stopping data collection...")
                sock.sendto('Reset'.encode(), (UDP_IP, UDP_PORT))
                need_flash = False
                collecting_data = False
                esp_data.clear()  # Clear stored ESP data
                GPIO.output(LED_RED, GPIO.LOW)
                GPIO.output(LED_GREEN, GPIO.LOW)
                GPIO.output(LED_YELLOW, GPIO.LOW)
                GPIO.output(LED_WHITE, GPIO.LOW)
                time.sleep(0.5)
                GPIO.output(LED_WHITE, GPIO.LOW)
            else:
                print("Starting data collection...")
                sock.sendto('Start'.encode(), (UDP_IP, UDP_PORT))
                GPIO.output(LED_WHITE, GPIO.HIGH)
                collecting_data = True
                with lock:
                    last_msg = time.time()
            time.sleep(0.5)

def main():
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    GPIO.setup(LED_YELLOW, GPIO.OUT)
    GPIO.output(LED_YELLOW, GPIO.LOW)
    
    GPIO.setup(LED_RED, GPIO.OUT)
    GPIO.setup(LED_GREEN, GPIO.OUT)
    GPIO.setup(LED_WHITE, GPIO.OUT)
    GPIO.output(LED_RED, GPIO.LOW)
    GPIO.output(LED_GREEN, GPIO.LOW)
    GPIO.output(LED_WHITE, GPIO.LOW)

    button_thread = threading.Thread(target=button_monitor)
    button_thread.start()

    receiving = threading.Thread(target=receive)
    receiving.start()

    packet = threading.Thread(target=packet_lost_detect)
    packet.start()

    flashing = threading.Thread(target=flash_LED)
    flashing.start()

if __name__ == "__main__":
    main()
