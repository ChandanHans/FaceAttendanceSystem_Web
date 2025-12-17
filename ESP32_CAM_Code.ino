// ===============================
// ESP32-CAM (AI Thinker) – CONFIGURABLE VIA SERIAL
// Streams camera over WiFi
// WiFi credentials stored in EEPROM, configurable via Python script
// ===============================

#include "esp_camera.h"
#include <WiFi.h>
#include <EEPROM.h>

// ===============================
// Camera model
// ===============================
#define CAMERA_MODEL_AI_THINKER

// ===============================
// EEPROM Configuration
// ===============================
#define EEPROM_SIZE 512
#define SSID_ADDR 0
#define SSID_LENGTH 32
#define PASSWORD_ADDR 64
#define PASSWORD_LENGTH 64
#define CONFIG_FLAG_ADDR 128
#define CONFIG_MAGIC 0xAB  // Magic byte to check if configured

// ===============================
// AI Thinker pin configuration
// ===============================
#define PWDN_GPIO_NUM     32
#define RESET_GPIO_NUM    -1
#define XCLK_GPIO_NUM      0
#define SIOD_GPIO_NUM     26
#define SIOC_GPIO_NUM     27

#define Y9_GPIO_NUM       35
#define Y8_GPIO_NUM       34
#define Y7_GPIO_NUM       39
#define Y6_GPIO_NUM       36
#define Y5_GPIO_NUM       21
#define Y4_GPIO_NUM       19
#define Y3_GPIO_NUM       18
#define Y2_GPIO_NUM        5

#define VSYNC_GPIO_NUM    25
#define HREF_GPIO_NUM     23
#define PCLK_GPIO_NUM     22

// ===============================
// WiFi credentials (will be loaded from EEPROM or received via serial)
// ===============================
char ssid[SSID_LENGTH] = "";
char password[PASSWORD_LENGTH] = "";

// Default fallback credentials (if EEPROM empty)
const char* default_ssid = "FaceAttendance-Pi";
const char* default_password = "attendance2025";

void startCameraServer();

// ===============================
// EEPROM Functions
// ===============================
void saveWiFiConfig(String newSSID, String newPassword) {
  Serial.println("💾 Saving WiFi config to EEPROM...");
  
  // Clear EEPROM areas
  for (int i = 0; i < SSID_LENGTH; i++) {
    EEPROM.write(SSID_ADDR + i, 0);
  }
  for (int i = 0; i < PASSWORD_LENGTH; i++) {
    EEPROM.write(PASSWORD_ADDR + i, 0);
  }
  
  // Write SSID
  for (int i = 0; i < newSSID.length() && i < SSID_LENGTH - 1; i++) {
    EEPROM.write(SSID_ADDR + i, newSSID[i]);
  }
  
  // Write Password
  for (int i = 0; i < newPassword.length() && i < PASSWORD_LENGTH - 1; i++) {
    EEPROM.write(PASSWORD_ADDR + i, newPassword[i]);
  }
  
  // Set configuration flag
  EEPROM.write(CONFIG_FLAG_ADDR, CONFIG_MAGIC);
  
  EEPROM.commit();
  Serial.println("✅ CONFIGURED");
}

bool loadWiFiConfig() {
  // Check if EEPROM has been configured
  if (EEPROM.read(CONFIG_FLAG_ADDR) != CONFIG_MAGIC) {
    Serial.println("⚠️  No saved WiFi config, using defaults");
    strcpy(ssid, default_ssid);
    strcpy(password, default_password);
    return false;
  }
  
  // Load SSID
  for (int i = 0; i < SSID_LENGTH; i++) {
    ssid[i] = EEPROM.read(SSID_ADDR + i);
    if (ssid[i] == 0) break;
  }
  ssid[SSID_LENGTH - 1] = '\0';
  
  // Load Password
  for (int i = 0; i < PASSWORD_LENGTH; i++) {
    password[i] = EEPROM.read(PASSWORD_ADDR + i);
    if (password[i] == 0) break;
  }
  password[PASSWORD_LENGTH - 1] = '\0';
  
  Serial.println("✅ Loaded WiFi config from EEPROM");
  return true;
}

void checkSerialConfig() {
  if (Serial.available() > 0) {
    String input = Serial.readStringUntil('\n');
    input.trim();
    
    // Format: WIFI_CONFIG:SSID:PASSWORD
    if (input.startsWith("WIFI_CONFIG:")) {
      int firstColon = input.indexOf(':', 12);
      int secondColon = input.indexOf(':', firstColon + 1);
      
      if (firstColon > 0 && secondColon > 0) {
        String newSSID = input.substring(12, firstColon);
        String newPassword = input.substring(firstColon + 1, secondColon);
        
        Serial.println("\n📡 Received WiFi configuration:");
        Serial.print("   SSID: ");
        Serial.println(newSSID);
        Serial.print("   Password: ");
        Serial.println("********");
        
        saveWiFiConfig(newSSID, newPassword);
        
        Serial.println("\n🔄 Please RESET ESP32 to connect with new credentials");
      }
    }
  }
}

void setup() {
  Serial.begin(115200);
  Serial.println();
  Serial.println("========================================");
  Serial.println("ESP32-CAM Configurable WiFi");
  Serial.println("========================================");

  // Initialize EEPROM
  EEPROM.begin(EEPROM_SIZE);
  
  // Wait for serial configuration (5 seconds)
  Serial.println("\n⏳ Waiting for WiFi configuration...");
  Serial.println("   (Send via Python script or press RESET to use saved/default)");
  
  unsigned long startTime = millis();
  while (millis() - startTime < 5000) {
    checkSerialConfig();
    delay(100);
  }
  
  // Load WiFi credentials
  loadWiFiConfig();
  
  Serial.println("\n📡 WiFi Credentials:");
  Serial.print("   SSID: ");
  Serial.println(ssid);
  Serial.print("   Password: ");
  for (int i = 0; i < strlen(password); i++) Serial.print("*");
  Serial.println();

  camera_config_t config;
  config.ledc_channel = LEDC_CHANNEL_0;
  config.ledc_timer = LEDC_TIMER_0;
  config.pin_d0 = Y2_GPIO_NUM;
  config.pin_d1 = Y3_GPIO_NUM;
  config.pin_d2 = Y4_GPIO_NUM;
  config.pin_d3 = Y5_GPIO_NUM;
  config.pin_d4 = Y6_GPIO_NUM;
  config.pin_d5 = Y7_GPIO_NUM;
  config.pin_d6 = Y8_GPIO_NUM;
  config.pin_d7 = Y9_GPIO_NUM;
  config.pin_xclk = XCLK_GPIO_NUM;
  config.pin_pclk = PCLK_GPIO_NUM;
  config.pin_vsync = VSYNC_GPIO_NUM;
  config.pin_href = HREF_GPIO_NUM;
  config.pin_sccb_sda = SIOD_GPIO_NUM;
  config.pin_sccb_scl = SIOC_GPIO_NUM;
  config.pin_pwdn = PWDN_GPIO_NUM;
  config.pin_reset = RESET_GPIO_NUM;
  config.xclk_freq_hz = 16000000;   // SAFE clock
  config.pixel_format = PIXFORMAT_JPEG;

  // ===============================
  // Frame settings (SAFE)
  // ===============================
  if (psramFound()) {
    config.frame_size = FRAMESIZE_VGA;
    config.jpeg_quality = 10;
    config.fb_count = 2;
  } else {
    config.frame_size = FRAMESIZE_QVGA;
    config.jpeg_quality = 12;
    config.fb_count = 1;
  }

  // ===============================
  // Init camera
  // ===============================
  esp_err_t err = esp_camera_init(&config);
  if (err != ESP_OK) {
    Serial.printf("Camera init failed: 0x%x\n", err);
    return;
  }

  // ===============================
  // Connect WiFi
  // ===============================
  Serial.println("\n🔌 Connecting to WiFi...");
  WiFi.begin(ssid, password);
  
  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 20) {
    delay(500);
    Serial.print(".");
    attempts++;
  }

  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\n✅ WiFi Connected!");
    Serial.print("   ESP32-CAM IP: ");
    Serial.println(WiFi.localIP());
  } else {
    Serial.println("\n❌ WiFi connection failed!");
    Serial.println("   Check SSID/Password in config.json");
    Serial.println("   Run: python configure_esp32_wifi.py");
    return;
  }

  // ===============================
  // Start web server
  // ===============================
  startCameraServer();

  Serial.println("\n========================================");
  Serial.println("✅ Camera Ready!");
  Serial.println("========================================");
  Serial.print("📹 Stream URL: http://");
  Serial.print(WiFi.localIP());
  Serial.println(":81/stream");
  Serial.println("\n💡 To change WiFi:");
  Serial.println("   1. Edit config/config.json on Pi");
  Serial.println("   2. Run: python configure_esp32_wifi.py");
  Serial.println("   3. Press RESET on ESP32");
  Serial.println("========================================\n");
}

void loop() {
  // Check for configuration updates
  checkSerialConfig();
  delay(1000);
}