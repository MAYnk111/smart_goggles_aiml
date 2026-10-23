#include <Arduino.h>
#include <Wire.h>
#include <WiFi.h>

#include <MAX30105.h>
#include <Adafruit_MLX90614.h>

#include <BLEDevice.h>
#include <BLEServer.h>
#include <BLEUtils.h>
#include <BLE2902.h>


// ============================================================
// WIFI
// ============================================================

const char* WIFI_SSID = "Desktop1911";
const char* WIFI_PASSWORD = "18181818";


// ============================================================
// BLE UUIDs
// MUST MATCH FLUTTER APP
// ============================================================

#define BLE_SERVICE_UUID \
  "4fafc201-1fb5-459e-8fcc-c5c9c331914b"

#define BLE_CHARACTERISTIC_UUID \
  "beb5483e-36e1-4688-b7f5-ea07361b26a8"


// ============================================================
// I2C
// ============================================================

#define SDA_PIN 21
#define SCL_PIN 22


// ============================================================
// SENSOR OBJECTS
// ============================================================

MAX30105 max30102;
Adafruit_MLX90614 mlx = Adafruit_MLX90614();

bool max30102OK = false;
bool mlxOK = false;


// ============================================================
// BLE
// ============================================================

BLECharacteristic* telemetryCharacteristic = nullptr;

bool bleConnected = false;


// ============================================================
// TIMING
// ============================================================

// Sensor processing happens continuously.
// Serial/BLE output only once per second.

unsigned long lastOutput = 0;

const unsigned long OUTPUT_INTERVAL = 1000;


// ============================================================
// HEART RATE VARIABLES
// ============================================================

const int SAMPLE_RATE = 100;

// ------------------------------------------------------------
// SIGNAL PROCESSING
// ------------------------------------------------------------

// Moving DC baseline
float dcBaseline = 0.0;

// Smoothed AC signal
float filteredAC = 0.0;

// Previous filtered signal
float previousAC = 0.0;

// Signal envelope / amplitude
float signalAmplitude = 0.0;

// ------------------------------------------------------------
// BEAT TIMING
// ------------------------------------------------------------

unsigned long lastBeatTime = 0;
unsigned long peakTime = 0;

// ------------------------------------------------------------
// RELATIVE BEAT INTERVAL BUFFER
// ------------------------------------------------------------
//
// The last 7 accepted beat-to-beat intervals are retained.
// These represent the current heartbeat rhythm.
//
const int BEAT_BUFFER_SIZE = 7;

float beatIntervals[BEAT_BUFFER_SIZE];

int beatIntervalCount = 0;
int beatIntervalIndex = 0;

// ------------------------------------------------------------
// BPM
// ------------------------------------------------------------

float bpm = 0.0;

// ------------------------------------------------------------
// FINGER DETECTION
// ------------------------------------------------------------

bool fingerDetected = false;

// ------------------------------------------------------------
// PHYSIOLOGICAL INTERVAL LIMITS
// ------------------------------------------------------------

// 400 ms = 150 BPM
const unsigned long MIN_BEAT_INTERVAL = 400;

// 1500 ms = 40 BPM
const unsigned long MAX_BEAT_INTERVAL = 1500;

// ------------------------------------------------------------
// RELATIVE AVERAGE FILTER
// ------------------------------------------------------------
//
// Once enough history exists, a new interval must remain within
// this percentage of the recent average interval.
//
// Example:
//
// Average interval = 800 ms
// Tolerance = 25%
// Accepted range = 600 to 1000 ms
//
const float RELATIVE_TOLERANCE = 0.25;

// Number of accepted intervals required before relative
// filtering becomes active.
const int MIN_RELATIVE_BEATS = 3;

// ------------------------------------------------------------
// BPM ADAPTATION
// ------------------------------------------------------------
//
// Do not allow one valid beat to make the displayed BPM jump.
//
// 0.20 means the displayed BPM moves only 20% toward the BPM
// calculated from the newest accepted interval.
//
const float BPM_ADAPTATION = 0.20;

// ------------------------------------------------------------
// HEARTBEAT DETECTION STATE
// ------------------------------------------------------------

bool rising = false;

float localPeak = 0.0;

bool pulseDetected = false;


// ============================================================
// TEMPERATURE
// ============================================================

float bodyTemperature = NAN;


// ============================================================
// FALL / EMERGENCY
// ============================================================

bool fallDetected = false;
bool emergency = false;


// ============================================================
// BLE CALLBACK
// ============================================================

class MyServerCallbacks : public BLEServerCallbacks
{
  void onConnect(BLEServer* server)
  {
    bleConnected = true;

    Serial.println();
    Serial.println("================================");
    Serial.println("BLE CONNECTED");
    Serial.println("================================");
  }

  void onDisconnect(BLEServer* server)
  {
    bleConnected = false;

    Serial.println();
    Serial.println("BLE DISCONNECTED");

    delay(100);

    server->getAdvertising()->start();

    Serial.println("BLE ADVERTISING RESTARTED");
  }
};


// ============================================================
// BLE SETUP
// ============================================================

void setupBLE()
{
  Serial.println("Starting BLE...");

  BLEDevice::init("JATAYU_BAND");

  BLEServer* server = BLEDevice::createServer();

  server->setCallbacks(new MyServerCallbacks());

  BLEService* service =
      server->createService(BLE_SERVICE_UUID);

  telemetryCharacteristic =
      service->createCharacteristic(
          BLE_CHARACTERISTIC_UUID,
          BLECharacteristic::PROPERTY_READ |
          BLECharacteristic::PROPERTY_NOTIFY
      );

  telemetryCharacteristic->addDescriptor(
      new BLE2902()
  );

  telemetryCharacteristic->setValue(
      "{\"status\":\"ready\"}"
  );

  service->start();

  BLEAdvertising* advertising =
      BLEDevice::getAdvertising();

  advertising->addServiceUUID(
      BLE_SERVICE_UUID
  );

  advertising->setScanResponse(true);

  advertising->start();

  Serial.println("BLE READY");
  Serial.println("Device name: JATAYU_BAND");
}


// ============================================================
// I2C SCANNER
// ============================================================

void scanI2C()
{
  Serial.println();
  Serial.println("I2C SCAN");
  Serial.println("----------------------------");

  byte count = 0;
  bool foundMLX = false;
  bool foundMAX = false;

  for (byte address = 1; address < 127; address++)
  {
    Wire.beginTransmission(address);

    byte error = Wire.endTransmission();

    if (error == 0)
    {
      Serial.print("I2C DEVICE FOUND: 0x");

      if (address < 16)
        Serial.print("0");

      Serial.print(address, HEX);

      if (address == 0x57)
      {
        Serial.print(" -> MAX30102 (Pulse Oximeter)");
        foundMAX = true;
      }
      else if (address == 0x5A)
      {
        Serial.print(" -> MLX90614 (Infrared Temperature)");
        foundMLX = true;
      }

      Serial.println();
      count++;
    }
  }

  if (count == 0)
  {
    Serial.println("NO I2C DEVICES FOUND");
  }
  else
  {
    if (!foundMLX)
    {
      Serial.println("WARNING: 0x5A (MLX90614) NOT DETECTED on I2C bus!");
      Serial.println("         Check SDA(21)/SCL(22) wiring, 3.3V power, and 4.7k pull-up resistors.");
    }
    if (!foundMAX)
    {
      Serial.println("WARNING: 0x57 (MAX30102) NOT DETECTED on I2C bus!");
    }
  }

  Serial.println("----------------------------");
}



// ============================================================
// MAX30102 SETUP
// ============================================================

bool setupMAX30102()
{
  Serial.println();
  Serial.println("Starting MAX30102...");

  if (!max30102.begin(Wire, I2C_SPEED_FAST))
  {
    Serial.println("MAX30102 NOT FOUND");
    return false;
  }

  Serial.println("MAX30102 CONNECTED");

  /*
     Power:
     0xFF = maximum LED brightness

     Sample averaging = 4
     LED mode = Red + IR
     Sample rate = 100 Hz
     Pulse width = 411 us
     ADC range = 16384
  */

  byte ledBrightness = 0x40;
  byte sampleAverage = 4;
  byte ledMode = 2;
  int sampleRate = 100;
  int pulseWidth = 411;
  int adcRange = 16384;

  max30102.setup(
      ledBrightness,
      sampleAverage,
      ledMode,
      sampleRate,
      pulseWidth,
      adcRange
  );

  // IR LED
  max30102.setPulseAmplitudeIR(0x40);

  // Red LED
  max30102.setPulseAmplitudeRed(0x20);

  // Green OFF
  max30102.setPulseAmplitudeGreen(0);

  delay(100);

  return true;
}


// ============================================================
// MLX90614 SETUP
// ============================================================

bool setupMLX()
{
  Serial.println();
  Serial.println("Starting MLX90614...");

  if (!mlx.begin())
  {
    Serial.println("MLX90614 NOT DETECTED");
    Serial.println("  [DIAGNOSTIC] Check I2C address 0x5A, SDA pin 21, SCL pin 22,");
    Serial.println("               ensure 3.3V/5V supply, and verify 4.7k I2C pull-up resistors.");
    return false;
  }

  Serial.println("MLX90614 DETECTED");
  float testTemp = mlx.readObjectTempC();
  Serial.print("MLX90614 Test Temp: ");
  if (isnan(testTemp))
  {
    Serial.println("NAN (Sensor Reading Error)");
  }
  else
  {
    Serial.print(testTemp, 1);
    Serial.println(" C");
  }

  return true;
}


// ============================================================
// RESET BPM
// ============================================================

void resetBPM()
{
  bpm = 0.0;

  beatIntervalCount = 0;
  beatIntervalIndex = 0;

  lastBeatTime = 0;

  rising = false;
  localPeak = 0.0;
  peakTime = 0;

  filteredAC = 0.0;
  previousAC = 0.0;

  signalAmplitude = 0.0;

  pulseDetected = false;

  // Clear the interval history.
  for (int i = 0; i < BEAT_BUFFER_SIZE; i++)
  {
    beatIntervals[i] = 0.0;
  }
}


// ============================================================
// CALCULATE RELATIVE AVERAGE INTERVAL
// ============================================================
//
// This is the current heartbeat rhythm.
//
// Example:
//
// 800, 820, 790, 810 ms
//
// Average = 805 ms
//
// BPM = 60000 / 805 = 74.5 BPM
//
// ============================================================

float calculateRelativeAverage()
{
  if (beatIntervalCount == 0)
  {
    return 0.0;
  }

  float sum = 0.0;

  for (int i = 0; i < beatIntervalCount; i++)
  {
    sum += beatIntervals[i];
  }

  return sum / beatIntervalCount;
}


// ============================================================
// CHECK RELATIVE INTERVAL
// ============================================================
//
// A beat is not accepted just because it is physiologically
// possible. It must also belong to the recent heartbeat rhythm.
//
// Example:
//
// Current average = 800 ms
// New interval    = 820 ms  -> ACCEPT
// New interval    = 760 ms  -> ACCEPT
// New interval    = 320 ms  -> REJECT
// New interval    = 1200 ms -> REJECT
//
// Rejected values are NOT printed.
//
// ============================================================

bool isRelativeIntervalValid(float newInterval)
{
  // Let the first few accepted intervals establish the rhythm.
  if (beatIntervalCount < MIN_RELATIVE_BEATS)
  {
    return true;
  }

  float averageInterval =
      calculateRelativeAverage();

  if (averageInterval <= 0.0)
  {
    return true;
  }

  float difference =
      fabs(newInterval - averageInterval);

  float relativeDifference =
      difference / averageInterval;

  return relativeDifference <= RELATIVE_TOLERANCE;
}


// ============================================================
// ADD BEAT INTERVAL
// ============================================================

void addBeatInterval(unsigned long interval)
{
  beatIntervals[beatIntervalIndex] =
      (float)interval;

  beatIntervalIndex++;

  if (beatIntervalIndex >= BEAT_BUFFER_SIZE)
  {
    beatIntervalIndex = 0;
  }

  if (beatIntervalCount < BEAT_BUFFER_SIZE)
  {
    beatIntervalCount++;
  }
}


// ============================================================
// UPDATE BPM RELATIVELY
// ============================================================
//
// The newest interval gives a target BPM, but the displayed BPM
// moves toward that target gradually.
//
// Example:
//
// Previous BPM = 75
// New interval BPM = 80
// Adaptation = 0.20
//
// New BPM = 75 + (80 - 75) * 0.20
//         = 76
//
// Therefore a single valid interval cannot cause a large jump.
//
// ============================================================

void updateRelativeBPM(float interval)
{
  if (interval <= 0.0)
  {
    return;
  }

  float newBPM =
      60000.0 / interval;

  // First valid interval establishes the initial BPM.
  if (bpm <= 0.0)
  {
    bpm = newBPM;
    return;
  }

  // Gradually follow the new valid measurement.
  bpm =
      bpm +
      (newBPM - bpm) * BPM_ADAPTATION;

  // Safety limits.
  if (bpm < 40.0)
  {
    bpm = 40.0;
  }

  if (bpm > 150.0)
  {
    bpm = 150.0;
  }
}


// ============================================================
// PROCESS HEARTBEAT
// ============================================================

void processHeartRate(long irValue)
{
  // ----------------------------------------------------------
  // FINGER DETECTION
  // ----------------------------------------------------------

  if (irValue < 10000)
  {
    if (fingerDetected)
    {
      fingerDetected = false;
      resetBPM();
    }

    return;
  }

  fingerDetected = true;


  // ----------------------------------------------------------
  // ADAPTIVE DC BASELINE
  // ----------------------------------------------------------

  if (dcBaseline == 0.0)
  {
    dcBaseline = irValue;
  }

  dcBaseline =
      dcBaseline * 0.995 +
      irValue * 0.005;


  // ----------------------------------------------------------
  // REMOVE DC COMPONENT
  // ----------------------------------------------------------

  float ac =
      (float)irValue - dcBaseline;


  // ----------------------------------------------------------
  // LOW-PASS FILTER
  // ----------------------------------------------------------

  filteredAC =
      filteredAC * 0.80 +
      ac * 0.20;


  // ----------------------------------------------------------
  // TRACK SIGNAL AMPLITUDE
  // ----------------------------------------------------------

  float absoluteAC =
      fabs(filteredAC);

  signalAmplitude =
      signalAmplitude * 0.98 +
      absoluteAC * 0.02;


  // ----------------------------------------------------------
  // IGNORE VERY WEAK SIGNAL
  // ----------------------------------------------------------

  if (signalAmplitude < 20.0)
  {
    previousAC = filteredAC;
    return;
  }


  // ----------------------------------------------------------
  // ADAPTIVE PEAK THRESHOLD
  // ----------------------------------------------------------

  float threshold =
      max(15.0f, signalAmplitude * 0.55f);


  // ----------------------------------------------------------
  // PEAK DETECTION
  // ----------------------------------------------------------

  if (filteredAC > previousAC)
  {
    rising = true;

    if (filteredAC > localPeak)
    {
      localPeak = filteredAC;
      peakTime = millis();
    }
  }
  else
  {
    // --------------------------------------------------------
    // SIGNAL STARTED FALLING
    // A local peak has occurred.
    // --------------------------------------------------------

    if (rising &&
        localPeak > threshold)
    {
      unsigned long now = peakTime;


      // ======================================================
      // FIRST BEAT
      // ======================================================

      if (lastBeatTime == 0)
      {
        lastBeatTime = now;
        pulseDetected = true;

        localPeak = 0.0;
        rising = false;
        previousAC = filteredAC;

        return;
      }


      // ======================================================
      // CALCULATE BEAT-TO-BEAT INTERVAL
      // ======================================================

      unsigned long interval =
          now - lastBeatTime;


      // ======================================================
      // BASIC PHYSIOLOGICAL FILTER
      // ======================================================

      if (interval >= MIN_BEAT_INTERVAL &&
          interval <= MAX_BEAT_INTERVAL)
      {
        // ====================================================
        // RELATIVE AVERAGE FILTER
        // ====================================================

        bool accepted =
            isRelativeIntervalValid(
                (float)interval
            );


        // ====================================================
        // ACCEPTED BEAT
        // ====================================================

        if (accepted)
        {
          // Store only accepted intervals.
          addBeatInterval(interval);

          // This beat becomes the new timing reference.
          lastBeatTime = now;

          pulseDetected = true;

          // Smoothly update the displayed BPM.
          updateRelativeBPM(
              (float)interval
          );
        }


        // ====================================================
        // REJECTED BEAT
        // ====================================================
        //
        // Intentionally nothing is printed here.
        //
        // The previous BPM remains unchanged.
        // The rejected interval is not added to history.
        // lastBeatTime is not changed.
        //
        // This is what prevents a false peak from changing BPM.
        // ====================================================
      }


      localPeak = 0.0;
    }

    rising = false;
  }


  previousAC = filteredAC;


  // ----------------------------------------------------------
  // TIMEOUT
  // ----------------------------------------------------------

  if (lastBeatTime != 0 &&
      millis() - lastBeatTime > 5000)
  {
    resetBPM();
  }
}


// ============================================================
// READ TEMPERATURE
// ============================================================

void readTemperature()
{
  if (!mlxOK)
  {
    bodyTemperature = NAN;
    return;
  }

  float temp =
      mlx.readObjectTempC();

  if (isnan(temp) ||
      temp < 0 ||
      temp > 100)
  {
    bodyTemperature = NAN;
  }
  else
  {
    bodyTemperature = temp;
  }
}


// ============================================================
// EMERGENCY LOGIC
// ============================================================

void updateEmergency()
{
  /*
     Since there is currently no accelerometer,
     fall detection is disabled.

     Do NOT generate an emergency merely because
     BPM is temporarily unavailable.
  */

  fallDetected = false;

  emergency = false;

  if (fingerDetected &&
      bpm > 0)
  {
    /*
       Simple prototype threshold.

       This is NOT a medical diagnosis.
    */

    if (bpm >= 150 ||
        bpm <= 40)
    {
      emergency = true;
    }
  }
}


// ============================================================
// SEND BLE DATA
// ============================================================

void sendBLEData()
{
  String json = "{";

  json += "\"bpm\":";
  json += String((int)round(bpm));

  json += ",";

  if (isnan(bodyTemperature))
  {
    json += "\"temperature\":null";
  }
  else
  {
    json += "\"temperature\":";
    json += String(bodyTemperature, 1);
  }

  json += ",";

  json += "\"fall\":";
  json += fallDetected ? "true" : "false";

  json += ",";

  json += "\"finger\":";
  json += fingerDetected ? "true" : "false";

  json += ",";

  json += "\"emergency\":";
  json += emergency ? "true" : "false";

  json += "}";


  // ----------------------------------------------------------
  // SERIAL
  // ----------------------------------------------------------

  Serial.println();
  Serial.println("----------------------------");

  Serial.print("IR          : ");

  if (max30102OK)
    Serial.println(max30102.getIR());
  else
    Serial.println("SENSOR ERROR");


  Serial.print("Finger      : ");

  if (fingerDetected)
    Serial.println("DETECTED");
  else
    Serial.println("NOT DETECTED");


  Serial.print("BPM         : ");

  if (!fingerDetected)
  {
    Serial.println("NO FINGER");
  }
  else if (bpm <= 0)
  {
    Serial.println("WAITING FOR BEATS...");
  }
  else
  {
    Serial.println((int)round(bpm));
  }


  Serial.print("Temperature : ");

  if (isnan(bodyTemperature))
  {
    Serial.println("SENSOR ERROR");
  }
  else
  {
    Serial.print(bodyTemperature, 1);
    Serial.println(" C");
  }


  Serial.print("Fall        : ");

  if (fallDetected)
    Serial.println("DETECTED");
  else
    Serial.println("NORMAL");


  Serial.print("Emergency   : ");

  if (emergency)
    Serial.println("ALERT");
  else
    Serial.println("NORMAL");


  Serial.print("BLE JSON    : ");
  Serial.println(json);


  // ----------------------------------------------------------
  // BLE
  // ----------------------------------------------------------

  if (bleConnected &&
      telemetryCharacteristic != nullptr)
  {
    telemetryCharacteristic->setValue(
        json.c_str()
    );

    telemetryCharacteristic->notify();

    Serial.println("BLE STATUS  : DATA SENT");
  }
  else
  {
    Serial.println("BLE STATUS  : NOT CONNECTED");
  }
}


// ============================================================
// WIFI
// ============================================================

void connectWiFi()
{
  Serial.println();
  Serial.print("Connecting WiFi");

  WiFi.mode(WIFI_STA);

  WiFi.begin(
      WIFI_SSID,
      WIFI_PASSWORD
  );

  unsigned long start =
      millis();

  while (
      WiFi.status() != WL_CONNECTED &&
      millis() - start < 10000
  )
  {
    delay(500);
    Serial.print(".");
  }

  Serial.println();

  if (WiFi.status() == WL_CONNECTED)
  {
    Serial.println("WiFi CONNECTED");

    Serial.print("IP: ");
    Serial.println(
        WiFi.localIP()
    );
  }
  else
  {
    Serial.println(
        "WiFi unavailable - BLE still works"
    );
  }
}


// ============================================================
// SETUP
// ============================================================

void setup()
{
  Serial.begin(115200);

  delay(1000);

  Serial.println();
  Serial.println("================================");
  Serial.println("       JATAYU HEALTH BAND");
  Serial.println("================================");


  // ----------------------------------------------------------
  // I2C
  // ----------------------------------------------------------

  Wire.begin(
      SDA_PIN,
      SCL_PIN
  );

  Wire.setClock(100000);

  delay(100);


  // ----------------------------------------------------------
  // I2C SCAN
  // ----------------------------------------------------------

  scanI2C();


  // ----------------------------------------------------------
  // MAX30102
  // ----------------------------------------------------------

  max30102OK =
      setupMAX30102();


  // ----------------------------------------------------------
  // MLX90614
  // ----------------------------------------------------------

  mlxOK =
      setupMLX();


  // ----------------------------------------------------------
  // BLE
  // ----------------------------------------------------------

  setupBLE();


  // ----------------------------------------------------------
  // WIFI
  // ----------------------------------------------------------

  connectWiFi();


  Serial.println();
  Serial.println("================================");
  Serial.println("SYSTEM READY");
  Serial.println("================================");

  Serial.println(
      "Place finger firmly on MAX30102."
  );

  Serial.println(
      "Keep finger still for 10-15 seconds."
  );

  Serial.println(
      "BPM will appear after real beats are detected."
  );

  Serial.println();
}


// ============================================================
// LOOP
// ============================================================

void loop()
{
  // ----------------------------------------------------------
  // MAX30102
  // ----------------------------------------------------------

  if (max30102OK)
  {
    /*
       Read continuously.

       This is VERY important.

       Heartbeat detection cannot work correctly if
       getIR() is only called once every second.
    */

    long irValue =
        max30102.getIR();

    processHeartRate(
        irValue
    );
  }


  // ----------------------------------------------------------
  // OUTPUT EVERY 1 SECOND
  // ----------------------------------------------------------

  if (
      millis() - lastOutput >=
      OUTPUT_INTERVAL
  )
  {
    lastOutput =
        millis();


    // Temperature
    readTemperature();


    // Emergency
    updateEmergency();


    // BLE + Serial
    sendBLEData();
  }


  /*
     Small delay.

     This is NOT the sensor sampling interval.
     The MAX30102 is configured for 100 Hz.

     10 ms = approximately 100 processing cycles/sec.
  */

  delay(10);
}