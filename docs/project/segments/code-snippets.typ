#let code_snippets = [
  === Programa de la simulación de Wokwi
  #text(size: 8pt)[
    ```cpp
    #include <WiFi.h>
    #include <time.h>

    constexpr int RELAY_PIN = 26;

    constexpr bool RELAY_ACTIVE_LOW = false;

    constexpr bool TEST_MODE = false;
    constexpr int ACTIVE_MINUTES = 5;

    constexpr char WIFI_SSID[] = "Wokwi-GUEST";
    constexpr char WIFI_PASSWORD[] = "";

    constexpr long GMT_OFFSET_SECONDS = -4L * 3600L;
    constexpr int DAYLIGHT_OFFSET_SECONDS = 0;

    unsigned long simulatedHourStart = 0;
    bool previousState = false;

    void setRelay(bool enabled) {
      const int level = RELAY_ACTIVE_LOW
          ? (enabled ? LOW : HIGH)
          : (enabled ? HIGH : LOW);

      digitalWrite(RELAY_PIN, level);

      Serial.println(
          enabled
              ? "ESP32-CAM y ventilador: ENCENDIDOS"
              : "ESP32-CAM y ventilador: APAGADOS"
      );
    }

    void connectWiFi() {
      Serial.print("Conectando a Wi-Fi");

      WiFi.begin(WIFI_SSID, WIFI_PASSWORD, 6);

      while (WiFi.status() != WL_CONNECTED) {
        delay(250);
        Serial.print(".");
      }

      Serial.println();
      Serial.println("Wi-Fi conectado");
      Serial.print("Dirección IP: ");
      Serial.println(WiFi.localIP());
    }

    void configureTime() {
      configTime(
          GMT_OFFSET_SECONDS,
          DAYLIGHT_OFFSET_SECONDS,
          "pool.ntp.org",
          "time.nist.gov"
      );

      Serial.print("Sincronizando hora");

      struct tm timeInfo {};

      while (!getLocalTime(&timeInfo)) {
        delay(500);
        Serial.print(".");
      }

      Serial.println();
      Serial.println("Hora sincronizada");
    }

    void setup() {
      Serial.begin(115200);
      pinMode(RELAY_PIN, OUTPUT);

      setRelay(false);
      previousState = false;

      connectWiFi();
      configureTime();

      simulatedHourStart = millis();
    }

    void loop() {
      struct tm timeInfo {};

      if (!getLocalTime(&timeInfo)) {
        Serial.println("No se pudo obtener la hora");
        delay(1000);
        return;
      }

      const int currentMinute = TEST_MODE
          ? ((millis() - simulatedHourStart) / 1000) % 60
          : timeInfo.tm_min;

      const bool shouldBeEnabled =
          currentMinute < ACTIVE_MINUTES;

      if (shouldBeEnabled != previousState) {
        setRelay(shouldBeEnabled);
        previousState = shouldBeEnabled;
      }

      static int previousDisplayedValue = -1;

      const int displayedValue =
          TEST_MODE ? currentMinute : timeInfo.tm_sec;

      if (displayedValue != previousDisplayedValue) {
        if (TEST_MODE) {
          Serial.printf(
              "Minuto simulado: %02d | Estado: %s\n",
              currentMinute,
              shouldBeEnabled ? "ENCENDIDO" : "APAGADO"
          );
        } else {
          Serial.printf(
              "Hora Bolivia: %02d:%02d:%02d | Estado: %s\n",
              timeInfo.tm_hour,
              timeInfo.tm_min,
              timeInfo.tm_sec,
              shouldBeEnabled ? "ENCENDIDO" : "APAGADO"
          );
        }

        previousDisplayedValue = displayedValue;
      }

      delay(100);
    }

    ```
  ]

  === Función 2
  #text(size: 8pt)[
    #lorem(40)
  ]

  === Función n
  #text(size: 8pt)[
    #lorem(40)
  ]
]
