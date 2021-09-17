#!/usr/bin/env python3
import serial, re, json, sys, serial.tools.list_ports, struct
from time import sleep
from binascii import hexlify

devs = serial.tools.list_ports.comports(include_links=False)
for obj in devs:
  print(obj.device, obj.product)
  if re.search('ALC8500',obj.product):
    DEV = obj.device

# Looking for ALC8500
try:
  c = serial.Serial(DEV, 38400, timeout=0,parity=serial.PARITY_EVEN, rtscts=0)
except:
  print("ALC8500 device not found")
  sys.exit()

def send(data):
  c.write(data.encode('utf-8'))
  sleep(0.2)
  i = 0
  while i < c.in_waiting:
    i = c.in_waiting
    sleep(0.2)
  n = c.read(i)
  return n

# Getting firmware and serial
request = '\x02\x75\x03'
o = send(request)
p = str(hexlify(o),'ascii')
print("Version: {}, Serial: {}".format(str(o[4:11],'ascii'),str(o[13:-1],'ascii')))

# Getting temperatures
request = '\x02\x74\x03'
o = send(request)
p = str(hexlify(o),'ascii')
print("Temperature sensor: {:0.2f}, Powersupply: {:0.2f}, Cooler: {:0.2f}".format(
  struct.unpack(">H",o[2:4])[0] / 100,
  struct.unpack(">H",o[4:6])[0] / 100,
  struct.unpack(">H",o[6:8])[0] / 100
))
