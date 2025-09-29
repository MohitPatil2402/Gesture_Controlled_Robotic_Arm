import socket

# ==============================
# ESP8266 details
# ==============================
ESP_IP = "127.0.0.1"  # change to ESP8266's IP from Serial Monitor
ESP_PORT = 1234           # must match your Arduino code

# Create UDP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

print("🚀 UDP Controller started")
print("Type a command (forward, backward, left, right, up, down, grab, release, stop)")
print("Ctrl+C to quit")

while True:
    cmd = input("Command: ").strip().lower()

    # if cmd in ["forward", "backward", "left", "right", "up", "down", "grab", "release", "stop"]:
    sock.sendto(cmd.upper().encode(), (ESP_IP, ESP_PORT))
    print(f"✅ Sent: {cmd}")
    # else:
    #     print("❌ Invalid command, try again")