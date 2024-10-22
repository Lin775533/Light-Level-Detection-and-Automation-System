import socket 
import threading
import RPi.GPIO as GPIO
import time

# Define UDP settings
UDP_IP = "Your_IP"
UDP_PORT = your_port
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Define thresholds
low_threshold = 400
high_threshold = 700
last_msg = time.time()
need_flash = False
collecting_data = False  # New flag to track if data collection is active

lock = threading.Lock()

# GPIO pin setup
BUTTON_PIN = 15  
LED_RED = 27      
LED_YELLOW = 22   
LED_GREEN = 23   
LED_WHITE = 24   

def receive():
    """
    Continuously listens for data from the UDP socket.
    If data collection is active, it processes the received data and updates the LEDs.
    """
    while True:
        data, addr = sock.recvfrom(1024)
        received = data.decode()
        if collecting_data:  # Only process data if collecting_data is True
            change_LED(int(received))
            global last_msg
            with lock:
                last_msg = time.time()
            print("Received message: %s" % received)
            message_shown = False  # Data is received, reset the flag
        else:
            print("Data received but not processing as collecting_data is False")

def packet_lost_detect():
    """
    Detects if no data has been received for over 10 seconds.
    If data collection is active and no data is received, it triggers a flash on the white LED.
    """
    global message_shown  # Move this outside the loop so it persists
    message_shown = False  # Flag to track if the message has been shown

    while True:
        global last_msg
        cur_time = time.time()

        dif = cur_time - last_msg
        if dif > 10 and collecting_data:
            if not message_shown:  # Only show message if it hasn't been shown
                print("Not receiving data from ESP8266 for over 10 seconds...")
                message_shown = True  # Set flag to prevent further prints
            global need_flash
            with lock:
                need_flash = True

        time.sleep(0.1)  # Add a short sleep to avoid excessive CPU usage

def flash_LED():
    """
    Flashes the white LED if the need_flash flag is set.
    """
    while True:
        if need_flash:
            GPIO.output(LED_WHITE, GPIO.LOW)
            time.sleep(0.25)
            GPIO.output(LED_WHITE, GPIO.HIGH)
            time.sleep(0.25)

def change_LED(val):
    """
    Changes the state of the LEDs based on the received value.
    """
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
    """
    Monitors the button state and starts/stops data collection based on button presses.
    """
    global collecting_data, last_msg, need_flash, message_shown
    while True:
        if GPIO.input(BUTTON_PIN) == GPIO.HIGH:  # Button press detected
            if collecting_data:
                # Stop data collection
                print("Stopping data collection...")
                sock.sendto('Reset'.encode(), (UDP_IP, UDP_PORT))
                need_flash = False
                collecting_data = False
                GPIO.output(LED_RED, GPIO.LOW)
                GPIO.output(LED_GREEN, GPIO.LOW)
                GPIO.output(LED_YELLOW, GPIO.LOW)
                GPIO.output(LED_WHITE, GPIO.LOW)  # Turn off white LED
                time.sleep(0.5)
                GPIO.output(LED_WHITE, GPIO.LOW)  # Turn off white LED
            else:
                # Start data collection
                print("Starting data collection...")
                sock.sendto('Start'.encode(), (UDP_IP, UDP_PORT))
                GPIO.output(LED_WHITE, GPIO.HIGH)  # Turn on white LED
                collecting_data = True
                message_shown = False
                with lock:
                    last_msg = time.time()
            time.sleep(0.5)  # Debounce delay to prevent multiple presses

def main():
    """
    Main function to set up GPIO pins and start the necessary threads.
    """
    GPIO.setmode(GPIO.BCM)
    # Set up button and LEDs
    GPIO.setup(BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    GPIO.setup(LED_YELLOW, GPIO.OUT)
    GPIO.output(LED_YELLOW, GPIO.LOW)

    # Set up other LEDs
    GPIO.setup(LED_RED, GPIO.OUT)
    GPIO.setup(LED_GREEN, GPIO.OUT)
    GPIO.setup(LED_WHITE, GPIO.OUT)
    GPIO.output(LED_RED, GPIO.LOW)
    GPIO.output(LED_GREEN, GPIO.LOW)
    GPIO.output(LED_WHITE, GPIO.LOW)

    # Start monitoring button presses
    button_thread = threading.Thread(target=button_monitor)
    button_thread.start()

    # Start other threads for receiving data, packet loss detection, and flashing LEDs
    receiving = threading.Thread(target=receive)
    receiving.start()

    packet = threading.Thread(target=packet_lost_detect)
    packet.start()

    flashing = threading.Thread(target=flash_LED)
    flashing.start()

if __name__ == "__main__":
    main()
