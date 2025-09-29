#include <ESP8266WiFi.h>
#include <WiFiUdp.h>

// WiFi credentials
const char* ssid = "SSID"; //Your internet name
const char* password = "password"; //Your internet password

// UDP settings
WiFiUDP Udp;
unsigned int localUdpPort = 1234;
char incomingPacket[255];

// Pin assignments (NodeMCU)
#define BASE_IN1 D1
#define BASE_IN2 D2
#define SHOULDER_IN1 D3
#define SHOULDER_IN2 D4
#define ELBOW_IN1 D5
#define ELBOW_IN2 D6
#define GRIPPER_IN1 D7
#define GRIPPER_IN2 D8

void stopAllMotors() {
  digitalWrite(BASE_IN1, LOW);
  digitalWrite(BASE_IN2, LOW);
  digitalWrite(SHOULDER_IN1, LOW);
  digitalWrite(SHOULDER_IN2, LOW);
  digitalWrite(ELBOW_IN1, LOW);
  digitalWrite(ELBOW_IN2, LOW);
  digitalWrite(GRIPPER_IN1, LOW);
  digitalWrite(GRIPPER_IN2, LOW);
}

void setup() {
  Serial.begin(9600);
  Serial.println(WiFi.localIP());
  pinMode(BASE_IN1, OUTPUT); pinMode(BASE_IN2, OUTPUT);
  pinMode(SHOULDER_IN1, OUTPUT); pinMode(SHOULDER_IN2, OUTPUT);
  pinMode(ELBOW_IN1, OUTPUT); pinMode(ELBOW_IN2, OUTPUT);
  pinMode(GRIPPER_IN1, OUTPUT); pinMode(GRIPPER_IN2, OUTPUT);

  stopAllMotors();

  WiFi.begin(ssid, password);
  Serial.print("Connecting to WiFi ..");
  while (WiFi.status() != WL_CONNECTED) {
    delay(1000);
    Serial.print(".");
  }
  Serial.println("\nConnected to WiFi");
  Serial.print("IP Address: ");
  Serial.println(WiFi.localIP());

  Udp.begin(localUdpPort);
  Serial.printf("Listening on UDP port %d\n", localUdpPort);
}

void loop() {
  int packetSize = Udp.parsePacket();
  if (packetSize) {
    int len = Udp.read(incomingPacket, 255);
    if (len > 0) incomingPacket[len] = '\0';
    String command = String(incomingPacket);
    command.trim();
    Serial.println("Command: " + command);

    stopAllMotors(); // stop all motors before action

    if (command == "LEFT") {
      digitalWrite(BASE_IN1, HIGH);
      digitalWrite(BASE_IN2, LOW);
      delay(600);
      stopAllMotors();
    }
    else if (command == "RIGHT") {
      digitalWrite(BASE_IN1, LOW);
      digitalWrite(BASE_IN2, HIGH);
      delay(600);
      stopAllMotors();
    }
    else if (command == "UP") {
      digitalWrite(SHOULDER_IN1, HIGH);
      digitalWrite(SHOULDER_IN2, LOW);
      delay(600);
      stopAllMotors();
    }
    else if (command == "DOWN") {
      digitalWrite(SHOULDER_IN1, LOW);
      digitalWrite(SHOULDER_IN2, HIGH);
      delay(600);
      stopAllMotors();
    }
    else if (command == "FORWARD") {
      digitalWrite(ELBOW_IN1, HIGH);
      digitalWrite(ELBOW_IN2, LOW);
      delay(600);
      stopAllMotors();
    }
    else if (command == "BACKWARD") {
      digitalWrite(ELBOW_IN1, LOW);
      digitalWrite(ELBOW_IN2, HIGH);
      delay(600);
      stopAllMotors();
    }
    else if (command == "RELEASE") {
      digitalWrite(GRIPPER_IN1, HIGH);
      digitalWrite(GRIPPER_IN2, LOW);
      delay(600);
      stopAllMotors();
    }
    else if (command == "GRAB") {
      digitalWrite(GRIPPER_IN1, LOW);
      digitalWrite(GRIPPER_IN2, HIGH);
      delay(600);
      stopAllMotors();
    }
    else if (command == "STOP") {
      stopAllMotors(); 
    }
  }
}