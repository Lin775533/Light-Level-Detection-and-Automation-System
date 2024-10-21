/*
Summary:
This code implements a WiFi-enabled light sensor system using an ESP8266 microcontroller.
The system follows a state machine pattern: it starts in an initialization state waiting 
for a "Start" command via UDP, then transitions to a data collection state where it reads 
from a photoresistor, buffers readings, and sends averaged data over UDP. The system also 
features LED status indication and error handling through a "Reset" command.

Key Components:
- WiFi/UDP Communication
- Photoresistor Reading
- LED Status Indication
- Data Buffering and Averaging
- Error Detection and Recovery
*/

#include <ESP8266WiFi.h>
#include <WiFiUdp.h>
#include "WiFiCredentials.h" // Contains ssid and password definitions

// Pin and Network Definitions
#define PHOTORES_PIN A0     // Analog pin for photoresistor
#define UDP_PORT 4210       // UDP port for communication

// Global Variables for UDP Communication
WiFiUDP UDP;
char incomingPacket[256];

// Timing Control Variables
int blink_interval = 1000;  // LED blink interval (ms)
int sensor_interval = 1000; // Sensor reading interval (ms)
int send_interval = 2000;   // Data transmission interval (ms)
int prev_led_time;         // Last LED state change time
int prev_sensor_time;      // Last sensor reading time
int prev_send_time;        // Last data transmission time

// State Variables
bool LED_STATUS = false;    // Current LED state
bool is_init = false;       // System initialization state

// Data Buffer
int buffer[5];             // Circular buffer for sensor readings
int buffer_idx = 0;        // Current position in buffer

void setup() {
    Serial.begin(9600);
    
    // WiFi Connection Setup
    WiFi.begin(ssid, password);
    Serial.print("Connecting");
    
    // Wait for WiFi connection
    while (WiFi.status() != WL_CONNECTED) {
        delay(500);
        Serial.print("."); 
    }

    // Initialize UDP and LED
    Serial.println("\nConnected to WiFi, IP: " + WiFi.localIP().toString());
    UDP.begin(UDP_PORT);
    pinMode(BUILTIN_LED, OUTPUT);
    digitalWrite(BUILTIN_LED, HIGH);  // LED off initially (active LOW)
}

void loop() {
    // State Machine Implementation
    if (!is_init) {
        handleInitialState();
    } else {
        unsigned long cur_time = millis();
        LED_blink(cur_time);    // Update LED state
        sensor(cur_time);       // Handle sensor readings
        error_detect();         // Check for reset command
    }
    delay(1);  // Prevent CPU hogging
}

// Handles the initial waiting state
void handleInitialState() {
    int packetSize = UDP.parsePacket();
    if (packetSize) {
        int len = UDP.read(incomingPacket, 255);
        if (len > 0) incomingPacket[len] = 0;
        
        // Transition to active state on "Start" command
        if (strcmp(incomingPacket, "Start") == 0) {
            is_init = true;
            blink_interval = 500;
            prev_led_time = prev_send_time = millis();
            digitalWrite(BUILTIN_LED, LOW);
        }
    }
}

// Monitors for error conditions and handles system reset
void error_detect() {
    int packetSize = UDP.parsePacket();
    if (packetSize) {
        int len = UDP.read(incomingPacket, 255);
        if (len > 0) incomingPacket[len] = 0;
        
        // Reset system state on "Reset" command
        if (strcmp(incomingPacket, "Reset") == 0) {
            resetSystem();
        }
    }
}

// Resets all system parameters to initial state
void resetSystem() {
    Serial.println("Error occurs, stop collecting data...");
    LED_STATUS = false;
    digitalWrite(BUILTIN_LED, HIGH);
    is_init = false;
    memset(buffer, 0, sizeof(buffer));  // Clear buffer
    buffer_idx = 0;
}

// Handles LED blinking based on current interval
void LED_blink(unsigned long cur_time) {
    if (cur_time - prev_led_time >= blink_interval / 2) {
        LED_STATUS = !LED_STATUS;
        digitalWrite(BUILTIN_LED, LED_STATUS ? LOW : HIGH);
        prev_led_time = cur_time;
    }
}

// Reads sensor data and manages buffer
void sensor(unsigned long cur_time) {
    if (cur_time - prev_sensor_time >= sensor_interval) {
        buffer[buffer_idx] = analogRead(PHOTORES_PIN);
        buffer_idx = (buffer_idx + 1) % 5;  // Circular buffer implementation
        prev_sensor_time = cur_time;
        
        calc_n_send(cur_time);
    }
}

// Calculates average and sends data via UDP
void calc_n_send(unsigned long cur_time) {
    if (cur_time - prev_send_time >= send_interval) {
        // Calculate buffer average
        int sum = 0, count = 0;
        for (int i = 0; i < 5; i++) {
            if (buffer[i] == 0) break;
            sum += buffer[i];
            count++;
        }
        if (count < 5) return;  // Wait for buffer to fill
        
        // Send data via UDP
        int avg = sum / count;
        char data[20];
        sprintf(data, "%d ", avg);
        prev_send_time = cur_time;
      
        UDP.beginPacket(UDP.remoteIP(), UDP.remotePort());
        UDP.write(data);
        UDP.endPacket();
        Serial.println("Send data to Raspberry Pi: " + String(data));
    }
}