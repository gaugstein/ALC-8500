# -*- coding: utf-8 -*-

CH01 = 0x00
CH02 = 0x01
CH03 = 0x02
CH04 = 0x03

DEL_CH_LOG      = 0x4c  # Delete channel logging
GET_CH_FUN      = 0x61  # Reading channel function
GET_CH_LOG      = 0x62  # Getting log data at address
GET_DB_REC      = 0x64  # Read database record (40 records)
GET_DEV_CFG     = 0x6A  # Device Configuration
GET_LOG_IDX     = 0x69  # Getting channel logging indexes
GET_LOG_BLK     = 0x76  # Getting logging data block
GET_CH_MEASURE  = 0x6D  # Getting channel measurement
GET_CH_PARAM    = 0x70  # Getting channel parameters
GET_TEMP        = 0x74  # Getting temperatures
GET_FW          = 0x75  # Getting Firmware and serial
GET_CFG_ADDR0   = 0x65  # Additional parameter 0
GET_CFG_ADDR1   = 0x67  # Additional parameter 1
GET_CFG_ADDR2   = 0x68  # Additional parameter 2
GET_CFG_ADDR3   = 0x6a  # Additional parameter 3
GET_CFG_ADDR4   = 0x7a  # Additional parameter 4

SET_CH_PARAM    = 0x50  # Set channel parameter
SET_AKKU        = 0x44  # Write database record
SET_CH_FUN      = 0x41  # Set channel function
SET_CFG_ADD0    = 0x45  # Additional parameter 0
SET_CFG_ADD1    = 0x47  # Additional parameter 1
SET_CFG_ADD2    = 0x48  # Additional parameter 2
SET_CFG_ADD3    = 0x4a  # Additional parameter 3
SET_CFG_ADD4    = 0x5a  # Additional parameter 4

PROG_CHARGE     = 0x01 # Laden
PROG_DIS        = 0x02 # Entladen
PROG_DIS_CHARGE = 0x03 # Entladen–Laden
PROG_TEST       = 0x04 # Test
PROG_SERVICE    = 0x05 # Wartung
PROG_FORM       = 0x06 # Formieren
PROG_CYCLE      = 0x07 # Zyklen
PROG_REFRESH    = 0x08 # Auffrischen

CH_FUNCTION = [ 'None','Charge','Discharge','Discharge/Charge','Test',
                'Service','Forming','Cycle','Refresh']

AKKU_TYPE  = [
  'NiCd','NiMH','Li-Ion 4.1','Li-Pol 4.2','Pb','LiFePo4','LiPo+ 4.35','NiZn','AGM/CA'
]

STATUS = {
 "Idle":           [ 0x00, 0x0a ],
 "Delay_Wait":     [ 0x0b, 0x2d ],
 "Discharge":      [ 0x2e, 0x37 ],
 "Charge":         [ 0x38, 0x6e ],
 "Trickle_Charge": [ 0x6f, 0xa0 ],
 "Discharge_End":  [ 0xa1, 0xc8 ],
 "Emergency_Exit": [ 0xc9, 0xff ]
}

ALC_CFG1 = [ "Off", "On", "1min", "5min", "10min", "30min", "60min" ]
ALC_CFG2 = { 3: "ALBEEP_EN", 4: "BUBEEP_EN" }
