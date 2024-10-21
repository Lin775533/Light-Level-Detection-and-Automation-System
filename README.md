**Components**

-   Raspberry Pi

-   ESP8266

-   Photoresistor (Light Sensor)

-   LEDs (Red, Yellow, Green, and White)

-   Buttons (Start/Reset, UDP Packet Loss Simulation)

**Schematic Description**

**ESP8266**

1.  Photoresistor (Analog Light Sensor):

-   One side: Connected to 3.3V.

-   Other side: Connected to A0 (analog input) on the ESP8266.

-   Use a pull-down resistor (typically 10kΩ) between the photoresistor
    and ground.

2.  Onboard LED of ESP8266:

-   Onboard LED of the ESP8266, no extra connections needed as it's
    controlled via code.

> ![A diagram of a circuit board Description automatically
> generated](media/image1.png){width="3.476672134733158in"
> height="3.356467629046369in"}

**Raspberry Pi**

1.  LEDs

> All LEDs have a 330Ω resistor between the GPIO pin and LED anode to
> limit current.

-   Red LED: Anode (long leg): GPIO 27, Cathode (short leg): Connect to
    GND.

-   Yellow LED: Anode (long leg): GPIO 22, Cathode (short leg): Connect
    to GND.

-   Green LED: Anode (long leg): GPIO 23, Cathode (short leg): Connect
    to GND.

-   White LED: Anode (long leg): GPIO 24, Cathode (short leg): Connect
    to GND.

2.  Button

-   Pin: GPIO 15

-   Ground: Connect the other leg to a GND pin (pin 6)

-   Resistor: 10kΩ pull-down resistor between the button and GND

> ![A diagram of a circuit board Description automatically
> generated](media/image1.png){width="3.3767158792650918in"
> height="3.789139326334208in"}

**Protocol**

The Raspberry Pi and ESP8266 are connected over a UDP communication
protocol.

Raspberry Pi (IP: 192.168.1.xxx) sends and receives UDP messages on a
specific port.

ESP8266 (IP: 192.168.1.xxx) listens for instructions from the Pi to
start or stop collecting data.

**UDP Message Flow & Data Transmission**

-   Start Communication:

> Raspberry Pi → ESP8266: \"START\"
>
> ESP8266 → Raspberry Pi: \"DATA: \<average_value\>\" (every 2 seconds)

-   Error Handling:

> Raspberry Pi detects no response from the ESP8266 for 10 seconds.
>
> Raspberry Pi → User: White LED flashes every 0.5 seconds to indicate
> an error.
>
> Button press required to reset the system and re-establish
> communication.

-   Stop Communication:

> Raspberry Pi → ESP8266: \"STOP\"
>
> ESP8266 halts data collection and turns off its onboard LED.

**Flow-chart**

![A diagram of a flowchart Description automatically
generated](media/image2.png){width="2.095260279965004in"
height="5.545590551181102in"}

**Flow-chart of Raspberry Pi**

The flowchart illustrates the operation of the Raspberry Pi system,
beginning with the initial state where it awaits user interaction. When
the button is pressed, the system activates the white LED and enters a
waiting state for UDP data from the ESP8266. If data is received within
10 seconds, the process continues; otherwise, the system enters an error
state until the button is pressed again to reinitialize communication.

![A diagram of a flowchart Description automatically
generated](media/image2.png){width="2.2344816272965877in"
height="4.713043525809274in"}

**Flow-chart of ESP8266**

The flowchart depicts the operation of the ESP8266 system, starting from
its initial state where it waits for commands from the Raspberry Pi.
Upon receiving a \"Start\" message, the ESP8266 begins reading sensor
values every second and sends the collected data back to the Raspberry
Pi. If a \"Stop\" message is received, the ESP8266 ceases its data
collection and returns to the initial state, ready for the next command.

**Main Functionality**

1.  Initialization: Pressing the button on the Raspberry Pi activates
    the white LED and sends a UDP message to the ESP8266 to establish
    communication.

2.  ESP8266 Response: Upon receiving the UDP message, the ESP8266 begins
    flashing its onboard LED every 0.5 seconds, collects light sensor
    values every second, and sends UDP responses with the average light
    sensor value every 2 seconds after a 5-second data collection
    period.

3.  Raspberry Pi Reaction: When the Raspberry Pi receives light sensor
    data, it controls its RGB LEDs according to the received value: one
    LED for LOW, two for MEDIUM, and all three for HIGH, with
    configurable threshold values.

4.  Error Handling: If the Raspberry Pi does not receive a message from
    the ESP8266 within 10 seconds, it flashes the white LED to indicate
    an error, refraining from reestablishing the connection until the
    button is pressed again.

5.  Reset: Pressing the button again sends a different UDP message to
    the ESP8266, turns off all RGBW LEDs, stops data collection, turns
    off the onboard LED, and resets both devices to their initial
    states.

**DEMO link:**

<https://drive.google.com/file/d/1eb1Ryeq-JZTNZIdM9p7p94Wu8D1bjBXA/view?usp=drive_link>
