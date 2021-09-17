#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# ELV/Voltcraft ALC8500-2 battery charger serial communication library
#-------------------------------------------------------------------------------
import re
import sys
import json
import struct
import serial
import serial.tools.list_ports
from time import sleep
from binascii import hexlify
from constant import *

class data:
  pass

class alc8500:

  def __init__(self,debug=False):
    ''' looking for ALC8500 and initialize data structures '''
    self.dev = None
    self.debug = debug
    self.data = data()
    self.db = data()
    self.channel = data()
    self.accu = data()
    self.log = data()
    devs = serial.tools.list_ports.comports(include_links=False)
    for dev in devs:
      if re.search('ALC8500',dev.product):
        self.dev = dev.device
    try:
      self.alc = serial.Serial(
        self.dev, 38400, timeout=0,parity=serial.PARITY_EVEN, rtscts=0)
    except:
      print("ALC8500 not found!")
      sys.exit(1)
    self.sysinfo()
    self.get_config()
    self.temp()

  def dump_data(self,dump):
    ''' print object data as json '''
    print(json.dumps(vars(dump),sort_keys=True,indent=2))

  def hexdump(self, src, length=16):
    ''' print hex/ascii dump '''
    FILTER = ''.join([(len(repr(chr(x))) == 3) and chr(x) or '.' for x in range(256)])
    lines = []
    for c in range(0, len(src), length):
      chars = [ chr(i) for i in src[c:c+length]]
      hex = ' '.join(["%02x" % ord(x) for x in chars])
      printable = ''.join(["%s" % ((ord(x) <= 127 and FILTER[ord(x)]) or '.') for x in chars])
      lines.append("%04x  %-*s  %s\n" % (c, length*3, hex, printable))
    return ''.join(lines)

  def get_data(self,dump):
    ''' return object data as json '''
    return vars(dump)

  def testBit(self,int_type, offset):
    ''' checking if bit set '''
    mask = 1 << offset
    return(int_type & mask)

  def in_conv(self,data):
    ''' convert/extract response data '''
    x = data.replace(b'\x05\x12',b'\02').\
      replace(b'\x05\x13',b'\03').replace(b'\x05\x15',b'\05')
    return x[1:len(x)-1]

  def out_conv(self,data):
    ''' convert request protocol data '''
    x = data.replace(b'\05',b'\x05\x15').\
      replace(b'\02',b'\x05\x12').replace(b'\03',b'\x05\x13')
    return b'\x02' +x+ b'\x03'

  def send(self,func,*args):
    ''' send requested data and return response '''
    req = struct.pack(">B",func)
    for i in args:
      if type(i) is int:
        if i > 255:
          req += struct.pack(">H",i)
        else:
          req += struct.pack(">B",i)
      elif type(i) is bytes:
        req += i
    request = self.out_conv(req)
    self.alc.write(request)
    response = b''
    i = 0
    while not i:
      sleep(0.2)
      i = self.alc.in_waiting  # bytes in buffer
      if i > 0:
        response += self.alc.read(i)
        if response[-1] != 3:    # waiting for final 0x03
          i = 0
    conv = self.in_conv(response)
    if self.debug:
      print('# Request:')
      print(self.hexdump(request))
      #print('# RAW-Response:')
      #print(self.hexdump(response))
      print('# Response:')
      print(self.hexdump(conv))
    return conv

  def sysinfo(self):
    ''' u <0x68> <firmware version> <0xFF> <0xFF> <Serial> '''
    resp = self.send(GET_FW)
    if chr(resp[0]) == 'u': # Firmware
      self.data.hardware = {
        'fw_version': str(resp[2:10].decode("utf-8")).lstrip(),
        'serial': str(resp[12:22].decode("utf-8")),
        "usb_port": re.sub("[<>]"," ",str(self.alc))
      }

  def temp(self):
    ''' t <ext.sensor> <power-supply> <cooler> '''
    resp = self.send(GET_TEMP)
    if (chr(resp[0]) == 't' and len(resp) > 5): # Temperatur
      self.data.temperature = {
        'sensor': struct.unpack(">H", resp[1:3])[0] / 100,
        'power': struct.unpack(">H", resp[3:5])[0] / 100,
        'cooler': struct.unpack(">H", resp[5:7])[0] / 100
      }
    if resp[1] == 171:
      self.data.temperature['Sensor'] = 'n.c.'

  def read_db(self):
    ''' Getting stored battery database
    d <number> <name> <type> <cells> <capacity> <discharge current>
    <charge current> <delay C/D> <FLAGS> <fullFactor> <function> '''
    i = 0
    while i < 40:
      o = self.send(GET_DB_REC,i)
      if chr(o[0]) == 'd': # Dataset
        if o[11] != 255:
          data = {
            'name': str(o[2:11].decode("utf-8")),
            'number': o[1],
            'accu_type': AKKU_TYPE[o[11]],
            'cells': int(o[12]),
            'capacity_mAh': struct.unpack('>i', o[13:17])[0] / 10000,
            'discharge_mA': int(struct.unpack(">H", o[17:19])[0] / 10),
            'charge_mA': int(struct.unpack(">H", o[19:21])[0] / 10),
            'delay_cd_60sec': int(struct.unpack(">H", o[21:23])[0] / 60),
            'flags': o[23],
            'charge_factor_percent': o[24],
            'func_release': o[25]
          }
          setattr(self.db,"{:02d}".format(i),data)
        i += 1

  def get_config(self):
    ''' Getting internal battery and configuration data '''
    o = self.send(GET_CFG_ADDR0)
    if chr(o[0]) == 'e':
      LiPol42 = {
        'delay': o[3],
        'final_discharge_voltage': struct.unpack('>H',o[1:3])[0]/1000,
        'loading_voltage': struct.unpack('>H',o[4:6])[0]/1000,
        'trickle_voltage': struct.unpack('>H',o[6:8])[0]/1000
      }
      NiZn = {
        'delay': o[10],
        'final_discharge_voltage': struct.unpack('>H',o[8:10])[0]/1000,
        'loading_voltage': struct.unpack('>H',o[11:13])[0]/1000,
        'trickle_voltage': struct.unpack('>H',o[13:15])[0]/1000
      }
      AGM_CA = {
        'delay': o[17],
        'final_discharge_voltage': struct.unpack('>H',o[15:17])[0]/1000,
        'loading_voltage': struct.unpack('>H',o[18:20])[0]/1000,
        'trickle_voltage': struct.unpack('>H',o[20:22])[0]/1000
      }

    o = self.send(GET_CFG_ADDR1)
    if chr(o[0]) == 'g':
      NiCd = {
        'delay': o[15],
        'final_discharge_voltage': struct.unpack('>H',o[1:3])[0]/1000,
        'cycle_count': o[11],
        'cycle_forming': o[13],
        'charge_cut_off': o[20]
      }
      NiMH = {
        'delay': o[16],
        'final_discharge_voltage': struct.unpack('>H',o[3:5])[0]/1000,
        'cycle_count': o[12],
        'cycle_forming': o[14],
        'charge_cut_off': o[21]
      }
      LiIon41 = {
        'final_discharge_voltage': struct.unpack('>H',o[5:7])[0]/1000,
        'delay': o[17]
      }
      LiPol42['final_discharge_voltage'] = struct.unpack('>H',o[7:9])[0]/1000
      LiPol42['delay'] = o[17]
      Pb = {
        'final_discharge_voltage': struct.unpack('>H',o[9:11])[0]/1000,
        'delay': o[18]
      }

    o = self.send(GET_CFG_ADDR2)
    if chr(o[0]) == 'h':
      LiIon41['loading_voltage'] = struct.unpack('>H',o[9:11])[0]/1000
      LiIon41['trickle_voltage'] = struct.unpack('>H',o[11:13])[0]/1000
      LiPol42['loading_voltage'] = struct.unpack('>H',o[13:15])[0]/1000
      LiPol42['trickle_voltage'] = struct.unpack('>H',o[15:17])[0]/1000
      Pb['loading_voltage'] = struct.unpack('>H',o[17:19])[0]/1000
      Pb['trickle_voltage'] = struct.unpack('>H',o[19:21])[0]/1000
      self.data.hardware['LowBatt_Cut_Voltage'] = struct.unpack('>H',o[21:23])[0]/1000

    o = self.send(GET_CFG_ADDR3)
    if chr(o[0]) == 'j':
      LiFePo4 = {
        'charge_cut_off': struct.unpack('>H',o[1:3])[0],
        'delay': o[3],
        'loading_voltage': struct.unpack('>H',o[4:6])[0]/1000
      }
      self.data.hardware['Display_Contrast'] = int(o[10])
      self.data.hardware['Config'] = ALC_CFG1[o[10] & 7]
      for k in ALC_CFG2.keys():
        if self.testBit(o[9],k):
          self.data.hardware['config'] = self.data.hardware['Config'] +","+ ALC_CFG2[k]

    o = self.send(GET_CFG_ADDR4)
    if chr(o[0]) == 'z':
      LiIon41['storage_voltage'] = struct.unpack('>H',o[1:3])[0]/1000
      LiPol42['storage_voltage'] = struct.unpack('>H',o[3:5])[0]/1000
      LiFePo4['storage_voltage'] = struct.unpack('>H',o[5:7])[0]/1000
      NiZn['storage_voltage'] = struct.unpack('>H',o[7:9])[0]/1000

    self.accu.LiPol42 = LiPol42
    self.accu.LiIon41 = LiIon41
    self.accu.LiFePo4 = LiFePo4
    self.accu.AGM_CA = AGM_CA
    self.accu.NiZn = NiZn
    self.accu.NiMH = NiMH
    self.accu.NiCd = NiCd
    self.accu.Pb = Pb

  def _isport(self,port):
    if port in [ 1,2,3,4 ]:
      return True
    else:
      print("Channel/port number should be between 1 and 4!")
      return False

  def _get_status(self,status):
    for key in STATUS.keys():
      if (status >= STATUS[key][0] and status <= STATUS[key][1]):
        return key
    return "unknown"

  def get_ch_params(self,port):
    ''' Getting stored channel parameters
    p <ch-number> <batt-number> <batt-type> <cells> <discharge current>
    <charge current> <capacity> <prog-number> <forming current>
    <delay C/D> <FLAGS> <measure end> <full factor> '''
    if self._isport(port):
      o = self.send(GET_CH_PARAM,port-1)
      if chr(o[0]) == 'p': # Channel parameter
        data = {
          'accu_number': o[2],
          'accu_type': AKKU_TYPE[o[3]],
          'cells': int(o[4]),
          'discharge_mA': int(round(struct.unpack(">H", o[5:7])[0]/10)),
          'charge_mA': int(round(struct.unpack(">H", o[7:9])[0]/10)),
          'capacity_mAh': int(round(struct.unpack('>i', o[9:13])[0] / 10000)),  # struct.pack('>i',cap)
          'function': CH_FUNCTION[int(o[13])],
          'form_charge_mA': int(round(struct.unpack(">H", o[14:16])[0] / 60)),  # struct.pack(">H",mA)
          'delay_cd_60sec': struct.unpack(">H", o[16:18])[0] / 60,
          'flags': o[19],
          'measure_end': struct.unpack(">H", o[19:21])[0],
          'charge_factor_percent': o[21]
        }
        setattr(self.channel,str(port),data)

  def get_ch_values(self,port):
    ''' Getting last channel measurement values
    m <port number> <voltage> <current> <capacity> '''
    if self._isport(port):
      o = self.send(GET_CH_MEASURE,port-1)
      if chr(o[0]) == 'm': # Measurement
        data = {
          'port': port,
          'voltage': struct.unpack(">H", o[2:4])[0] / 1000,
          'milliampere': struct.unpack(">H", o[4:6])[0]/10,
          'capacity': struct.unpack('>i', o[6:10])[0] / 10000
        }
        return data

  def get_ch_status(self,port):
    ''' a <portnumber>  -> function (1 byte) '''
    if self._isport(port):
      o = self.send(GET_CH_FUN,port-1)
      if chr(o[0]) == 'a':
        data = {
          'port': port,
          'function': self._get_status(o[2])
        }
        return data

  def get_log(self,port,log):
    ''' Extract logging data '''
    if self._isport(port):
      values = b''
      logs = vars(self.log)
      idx = logs['port_'+str(port)][str(log)]
      print(json.dumps(idx,sort_keys=True,indent=2))
      start = divmod(idx['log_start'],100)
      end = divmod(idx['log_end'],100)
      print("Read block {}..{} index {},{}".format(start[0],end[0],start[1],end[1]))
      # reading the first data block (100 bytes) whithout 4 byte response header
      o = self.send(GET_LOG_BLK,port-1,struct.pack(">H",start[0]))
      # the first block at address 0 contains 24 byte accu information:
      o = o[4:] if start[0] else o[28:]
      # note the shift of the start value
      values = o[start[1]*8:] if start[1] else o
      for i in range(start[0]+1,end[0]):
        print("# Reading block ",i,len(values))
        o = self.send(GET_LOG_BLK,port-1,struct.pack(">H",i))[4:]
        values = values + o
      # ignore the values outside the index range
      values = values[:-(100-end[1])*8] if end[1] else values
      return values

  def print_log_values(self,log):
    ''' print logging values '''
    print("Volt;mA;mAh;")
    for i in range(0, len(log),8):
      v = log[i:i+8]
      print("{:0.02f};{:0.02f};{:0.04f};".format(
        float(struct.unpack(">H", v[0:2])[0])/1000,   # V
        float(struct.unpack(">H", v[2:4])[0])/10,     # mA
        float(struct.unpack('>i', v[4:8])[0])/10000   # mAh
      ))

  def get_ch_log(self,port,addr):
    ''' Getting battery and function data from log entry
    b <port> <word-addr> '''
    if self._isport(port):
      o = self.send(GET_CH_LOG,port-1,struct.pack(">H",addr))
      if (chr(o[0]) == 'b') and (o[5] <= len(CH_FUNCTION)):
        data = {
          'port': port,
          'address': struct.unpack(">H", o[2:4])[0],
          'accu_number': o[4],
          'func': CH_FUNCTION[o[5]],
          'accu_type': AKKU_TYPE[o[12]],
          'cells': o[13],
          'capacity': int(round(struct.unpack('>i', o[14:18])[0] / 10000)),
          'charge_mA': int(round(struct.unpack(">H", o[18:20])[0]/10)),
          'discharge_mA': int(round(struct.unpack(">H", o[22:24])[0]/10)),
          'form_charge_mA': int(round(struct.unpack(">H", o[24:26])[0] / 60)),
          'delay_cd_60sec': struct.unpack(">H", o[26:28])[0] / 60
        }
      else:
        data = {
          'port': port,
          'func': 'unknown'
        }
      return data

  def get_ch_logs(self,port):
    ''' getting log block addresses for selected port
    i <portnumber>  '''
    if self._isport(port):
      o = self.send(GET_LOG_IDX,port-1)
      if chr(o[0]) == 'i':
        port_name = 'port_'+str(port)
        addrs = [ int(i,16) for i in re.findall('....',str(hexlify(o[2:]),'ascii')) ]
        last = addrs[0]
        # remove unused index values and last start value at pos 0
        addrs[:] = (i for i in addrs[1:] if i != 65535)
        if len(addrs) > 1:
          idx = addrs.index(last)
          addrs[:] = addrs[idx:] + addrs[:idx]
          if len(addrs) > 2:
            addrs[:] = addrs[2:] + addrs[:2]
          setattr(self.log,port_name,{ 'addrs': addrs })
          ptr = getattr(self.log,port_name)
          x = 0
          for i in range(len(addrs)-1,0,-1):
            size = addrs[i] - addrs[i-1]
            data = self.get_ch_log(port,addrs[i-1])
            data['log_start'] = addrs[i-1]
            data['log_end'] = addrs[i]
            ptr[str(x)] = data
            x += 1

  def clear_logs(self,port):
    ''' clear all logs per channel
    L <port number> '''
    if self._isport(port):
      o = self.send(DEL_CH_LOG,port-1)
      return True if chr(o[0]) == 'l' else False

  def ch_stop(self,port):
    if self._isport(port):
      o = self.send(SET_CH_FUN,port-1,1)
      return self.get_ch_status(port)

  def ch_start(self,port):
    if self._isport(port):
      o = self.send(SET_CH_FUN,port-1,0)
      return self.get_ch_status(port)
