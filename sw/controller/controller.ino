#include <SPI.h>         
#include <EEPROM.h>
#include <stdint.h>
#include <string.h>
#include <Arduino.h>
#include <avr/wdt.h>

#include <DHT22.h>

/* Configuration, in production use USE_XTAL_PINS, USE_WDT (if watchdog is working in bootloader) */

#define USE_XTAL_PINS       /*Use XTAL pins for output, crystal must not be present*/
#define BINARY_MESSAGE      /*Use THCL binary messages*/

#define LOGPRINT(a) Serial.print(a)
#define LOGPRINT_LF(a) Serial.println(a)

#define VERSION_NUM             100

#define NUM_OF_DIGITAL_CTRL     8

#define RX_PACKET_BUFFER_SIZE   128 /*Small binary messages used*/
#define TEMPERATURE_HYSTERESIS  1
#define HUMIDITY_HYSTERESIS     3
#define CONTROL_LOW             1
#define CONTROL_IN_RANGE        2
#define CONTROL_HIGH            3
#define SERIAL_BUFFER_SIZE      64

uint8_t g_serialInputData[SERIAL_BUFFER_SIZE];
boolean g_serialInputDataComplete = false;
uint8_t g_serialDataIdx           = 0;
uint8_t g_serialState             = 0;

uint8_t const g_serialSyncPattern[4] = {'s', 'y', 'n', 'c'};
uint8_t       g_serialSyncPatternFound = 0;
uint8_t       g_serialSyncPatternState = 0;

/*Control IDs*/
#define D_OUT_CTRL1         0
#define D_OUT_CTRL2         1
#define D_OUT_CTRL3         2
#define D_OUT_CTRL4         3
#define D_OUT_CTRL5         4
#define D_OUT_CTRL6         5
#define D_OUT_CTRL7         6
#define D_OUT_CTRL8         7

/*Control PINS, TBD*/
#define D_OUT_CTRL1_PIN     7
#define D_OUT_CTRL2_PIN     6
#define D_OUT_CTRL3_PIN     5
#define D_OUT_CTRL4_PIN     99 /*XTAL*/
#define D_OUT_CTRL5_PIN     98 /*XTAL*/
#define D_OUT_CTRL6_PIN     4
#define D_OUT_CTRL7_PIN     3
#define D_OUT_CTRL8_PIN     2

#define D_IN_HUMIDITY_SENSOR_PIN        8

typedef struct controller_settings_s {
    int8_t     minimum_temperature;
    int8_t     ac_start_temperature;
    int8_t     ac_max_temperature;
    int8_t     spare;
}controller_settings_s;

controller_settings_s g_settings = {4, 30, 40, 0};
static unsigned long g_last_ts = 0;

typedef struct digitalControls_s {
  uint8_t controlstatus;
  uint8_t pin;
}digitalControls_s;

static    uint8_t       g_useSwWatchDog           = 0;

static    uint32_t      g_RxMessages_Ser          = 0;
static    uint32_t      g_RxMessages_Udp          = 0;
static    uint8_t       g_validEepromRead         = 0;

digitalControls_s digitalCtrl[NUM_OF_DIGITAL_CTRL];

DHT22 internal_hum_sensor(D_IN_HUMIDITY_SENSOR_PIN);

static float internal_humidity    = 0.0;
static float internal_temperature = 0.0;
static uint8_t internal_status;

static void ReadTempAndHumMeas() { 
    DHT22_ERROR_t errorCode;
    uint8_t statusStrIdx = 0;

    errorCode = internal_hum_sensor.readData();
    internal_humidity    = -99.9; /*Set to indicate error*/
    internal_temperature = -99.9; /*Set to indicate error*/
    switch(errorCode) {
        case DHT_ERROR_NONE:
            internal_status = 0;
            internal_temperature = internal_hum_sensor.getTemperatureC();
            internal_humidity    = internal_hum_sensor.getHumidity();
            break;
        case DHT_ERROR_CHECKSUM:
            internal_status = 7;
        case DHT_BUS_HUNG:
            internal_status = 1;
        break;
        case DHT_ERROR_NOT_PRESENT:
            internal_status = 2;
        break;
        case DHT_ERROR_ACK_TOO_LONG:
            internal_status = 3;
        break;
        case DHT_ERROR_SYNC_TIMEOUT:
            internal_status = 4;
        break;
        case DHT_ERROR_DATA_TIMEOUT:
            internal_status = 5;
        break;
        case DHT_ERROR_TOOQUICK:
            internal_status = 6;
        break;
    }
}


int freeRam () {
    extern int __heap_start, *__brkval;
    int v;
    return (int) &v - (__brkval == 0 ? (int) &__heap_start : (int) __brkval);
}

unsigned long timeSpan(unsigned long startTime, unsigned long endTime) {
    return (unsigned long)((long)endTime - (long)startTime);
}


void InitDigitalCtrls(void) {
    uint8_t i;
    for(i=0; i<NUM_OF_DIGITAL_CTRL; i++) {
        digitalCtrl[i].controlstatus = LOW;
    }




    digitalCtrl[D_OUT_CTRL1_PIN].pin = D_OUT_CTRL1_PIN;
    digitalCtrl[D_OUT_CTRL2_PIN].pin = D_OUT_CTRL2_PIN;
    digitalCtrl[D_OUT_CTRL3_PIN].pin = D_OUT_CTRL3_PIN;
    digitalCtrl[D_OUT_CTRL4_PIN].pin = D_OUT_CTRL4_PIN;
    digitalCtrl[D_OUT_CTRL5_PIN].pin = D_OUT_CTRL5_PIN;
    digitalCtrl[D_OUT_CTRL6_PIN].pin = D_OUT_CTRL6_PIN;
    digitalCtrl[D_OUT_CTRL7_PIN].pin = D_OUT_CTRL7_PIN;
    digitalCtrl[D_OUT_CTRL8_PIN].pin = D_OUT_CTRL8_PIN;

    pinMode(D_OUT_CTRL1_PIN,     OUTPUT);
    pinMode(D_OUT_CTRL2_PIN,     OUTPUT);
    pinMode(D_OUT_CTRL3_PIN,     OUTPUT);

    /*Special case: use XTAL1 and XTAL2 pins as output*/
    DDRB |= (1 << DDB6) | (1 << DDB7);

    pinMode(D_OUT_CTRL6_PIN,     OUTPUT);
    pinMode(D_OUT_CTRL7_PIN,     OUTPUT);
    pinMode(D_OUT_CTRL8_PIN,     OUTPUT);

}


static void SetupWatchDog() {
    // immediately disable watchdog timer so set will not get interrupted
    LOGPRINT_LF("DBG: Setup watchdog...");
    wdt_disable();

    delay(100);
    wdt_enable(WDTO_8S);
    delay(100);
    LOGPRINT_LF("DBG: Setup watchdog...done");
}


void setup() {
    MCUSR=0;
    wdt_disable();

    Serial.begin(9600);
    LOGPRINT_LF("DBG: setup: started...");
    LOGPRINT("DBG: setup: version: ");
    LOGPRINT_LF(VERSION_NUM);
    
    InitDigitalCtrls();

    LOGPRINT_LF("DBG: setup: done!");
}



static void ControlTemperature() {
    /*Heating needed? */
    if ((float)internal_temperature < g_settings.minimum_temperature) {
        digitalCtrl[D_OUT_CTRL1_PIN].controlstatus = HIGH;
    } else {
        digitalCtrl[D_OUT_CTRL1_PIN].controlstatus = LOW;
    }
    /*Cooling needed?*/
    if ((float)internal_temperature > g_settings.ac_start_temperature) {
        digitalCtrl[D_OUT_CTRL2_PIN].controlstatus = HIGH;
    } else {
        digitalCtrl[D_OUT_CTRL2_PIN].controlstatus = LOW;
    }
}


void WriteControlOutputs(void) {
    
    digitalWrite(D_OUT_CTRL1_PIN, digitalCtrl[D_OUT_CTRL1].controlstatus);
    digitalWrite(D_OUT_CTRL2_PIN, digitalCtrl[D_OUT_CTRL2].controlstatus);
    digitalWrite(D_OUT_CTRL3_PIN, digitalCtrl[D_OUT_CTRL3].controlstatus);
    digitalWrite(D_OUT_CTRL6_PIN, digitalCtrl[D_OUT_CTRL6].controlstatus);
    digitalWrite(D_OUT_CTRL7_PIN, digitalCtrl[D_OUT_CTRL7].controlstatus);
    digitalWrite(D_OUT_CTRL8_PIN, digitalCtrl[D_OUT_CTRL8].controlstatus);

    if(digitalCtrl[D_OUT_CTRL4_PIN].controlstatus) {
        PORTB |= (1 << PORTB7);
    } else {
        PORTB &= ~(1 << PORTB7);
    }
    if(digitalCtrl[D_OUT_CTRL5_PIN].controlstatus) {
        PORTB |= (1 << PORTB6);
    } else {
        PORTB &= ~(1 << PORTB6);
    }
}

static void ParseControllerMsg(void * msg) {
    controller_settings_s const * const message = (controller_settings_s*)msg;
    LOGPRINT("mintemp: ");
    LOGPRINT(message->minimum_temperature);
    LOGPRINT(" acstart: ");
    LOGPRINT(message->ac_start_temperature);
    LOGPRINT(" acmax: ");
    LOGPRINT(message->ac_max_temperature);
    LOGPRINT_LF("");
    g_settings.minimum_temperature  = message->minimum_temperature;
    g_settings.ac_start_temperature = message->ac_start_temperature;
    g_settings.ac_max_temperature   = message->ac_max_temperature;
}

static void ParseSerialData() {
    if (g_serialInputDataComplete) {
        uint8_t i;
        
        /*Do something...*/
        LOGPRINT_LF("DBG: Parsing serial data...");
        
        g_serialSyncPatternState = 0;
        for(i=0; i<sizeof(g_serialSyncPattern); i++) {
            if (g_serialInputData[i] == g_serialSyncPattern[i]) {
                g_serialSyncPatternState++;
            }
        }
        if (g_serialSyncPatternState == sizeof(g_serialSyncPattern)) {
     //       ParseControllerMsg(&g_serialInputData[sizeof(g_serialSyncPattern)]);
            LOGPRINT_LF("DBG: Serial sync found");
            g_RxMessages_Ser++;
        }
        
        memset(g_serialInputData, 0, sizeof(g_serialInputData));
        g_serialDataIdx = 0;
        g_serialInputDataComplete  = false;
    }
}

/*
  SerialEvent occurs whenever a new data comes in the
 hardware serial RX.  This routine is run between each
 time loop() runs, so using delay inside loop can delay
 response.  Multiple bytes of data may be available.
 */
void serialEvent() {
    while (Serial.available()) {
        // get the new byte:
        uint8_t inChar = (uint8_t)Serial.read(); 
        // add it to the inputString:
        
        g_serialInputData[g_serialDataIdx] = inChar;
    
        g_serialDataIdx++;
        if (g_serialDataIdx >= (SERIAL_BUFFER_SIZE-1)) {
            g_serialDataIdx = 0;
        }

        if (inChar == 'z') {
            LOGPRINT_LF("ACK: Serial message completed");
            g_serialInputDataComplete = true;
        } 
    }
}



void loop() {
    // at every loop: reset the watchdog timer
    if (g_useSwWatchDog) {
        wdt_reset();
    }
    unsigned long now = millis();
    unsigned long timespan = timeSpan(g_last_ts, now);
    if(timespan > 4000) {
        //ParseSerialData();
        ReadTempAndHumMeas();
        LOGPRINT("Temp: ");
        LOGPRINT(internal_temperature);
        LOGPRINT(" Hum: ");
        LOGPRINT(internal_humidity);
        LOGPRINT(" H: ");
        LOGPRINT(digitalCtrl[D_OUT_CTRL1_PIN].controlstatus);
        LOGPRINT(" C: ");
        LOGPRINT(digitalCtrl[D_OUT_CTRL2_PIN].controlstatus);
        LOGPRINT(" TS: ");
        LOGPRINT_LF(now);
        ControlTemperature();
        g_last_ts = now;
    } else {
        
    }
    WriteControlOutputs();
}
