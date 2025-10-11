import machine
import network

# Downclock the CPU frequency to 80MHz for power saving
machine.freq(80000000)

# Disable Wi-Fi completely for power saving
sta_if = network.WLAN(network.STA_IF)
sta_if.active(False)
ap_if = network.WLAN(network.AP_IF)
ap_if.active(False)
