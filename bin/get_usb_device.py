#!/usr/bin/env python3
import sys
import usb.core

dev = usb.core.show_devices(find_all=True)
print(dev)

# loop through devices, printing vendor and product ids in decimal and hex
dev = usb.core.find(find_all=True)
for cfg in dev:
  sys.stdout.write('Decimal VendorID=' + str(cfg.idVendor) + ' & ProductID=' + str(cfg.idProduct) + '\n')
  sys.stdout.write('Hexadecimal VendorID=' + hex(cfg.idVendor) + ' & ProductID=' + hex(cfg.idProduct) + '\n\n')

# find USB devices
dev = usb.core.find(idVendor=0x403, idProduct=0xf06e)
if dev:
  print(dev.product)
  print(dev.serial_number)
  print(dev)

