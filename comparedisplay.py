#!/usr/bin/python3
# Creator: Thiemo Schuff
# Source: https://github.com/Starwhooper/RPi-household-energy-status

#######################################################
#
# Prepare
#
#######################################################


#Logging Levels https://rollbar.com/blog/logging-in-python/#
#    DEBUG - Detailed information, typically of interest when diagnosing problems.
#    INFO - Confirmation of things working as expected.
#    WARNING - Indication of something unexpected or a problem in the near future e.g. 'disk space low'.
#    ERROR - A more serious problem due to which the program was unable to perform a function.
#    CRITICAL - A serious error, indicating that the program itself may not be able to continue executing.


##### check if all required packages are aviable
import sys
try:
 from luma.core.render import canvas
 from PIL import ImageFont
 from urllib.parse import quote
 import json
 import logging
 import os
 import psutil
 import requests
 import re
 import time
 from datetime import datetime, timedelta  
except:
 sys.exit("\033[91m {}\033[00m" .format('any needed package is not aviable. Please check README.md to check which components should be installed via pip3".'))

logging.getLogger("urllib3").setLevel(logging.WARNING)

##### import config.json
try:
 with open(os.path.split(os.path.abspath(__file__))[0] + '/config.json','r') as file:
  cf = json.loads(file.read())
except:
 logging.critical('The configuration file ' + os.path.split(os.path.abspath(__file__))[0] + '/config.json does not exist or has incorrect content. Please rename the file config.json.example to config.json and change the content as required ')
 sys.exit("\033[91m {}\033[00m" .format('exit: The configuration file ' + os.path.split(os.path.abspath(__file__))[0] + '/config.json does not exist or has incorrect content. Please rename the file config.json.example to config.json and change the content as required '))
 
##### import module demo_opts
try:
 sys.path.append(cf['luma']['demo_opts.py']['folder'])
 from demo_opts import get_device
except:
 logging.critical('file ' + cf['luma']['demo_opts.py']['folder'] + '/demo_opts.py not found. Please check config.json or do sudo git clone https://github.com/rm-hull/luma.examples /opt/luma.examples')
 sys.exit("\033[91m {}\033[00m" .format('file ' + cf['luma']['demo_opts.py']['folder'] + '/demo_opts.py not found. Please check config.json or do sudo git clone https://github.com/rm-hull/luma.examples /opt/luma.examples'))

##### do output
def stats(device):
 global invertertime
 try: invertertime
 except: invertertime = datetime(1977, 1, 1)
 global inverter_total
 try: inverter_total
 except: inverter_total = 0
 global inverter_adj
 try: inverter_adj
 except: inverter_adj = 0
 global inverter_now
 global sunbeam
 try: sunbeam
 except: sunbeam = 0 
 global sunkwh
 try: sunkwh
 except: sunkwh = 'adj'
 
 #print(invertertime)
 with canvas(device, dither=True) as draw:

  #####get inverter    
  if (invertertime <= datetime.now() - timedelta(minutes=1)):
   try:
    inverter = requests.get(inverterurl, timeout=1)
    html_content = inverter.text
    inverter_total = float(re.search(r'var\s+webdata_total_e\s*=\s*"([^"]+)"', inverter.text).group(1))
    inverter_now = int(re.search(r'var\s+webdata_now_p\s*=\s*"([^"]+)"', inverter.text).group(1))
    invertertime = datetime.now()
   except:
    inverter_now = 0
    invertertime = datetime.now() - timedelta(minutes=1) - timedelta(seconds=10)
    logging.warning(inverterurl + ' could not read')

   if inverter_total >= 1:
    inverter_adj = inverter_total + cf['inverter']['offset']
   else:
    inverter_adj = inverter_total
    logging.warning('inverter total count not found')
    
  
  #####get electricitymeter
  try:
      electricitymeter = requests.get(electricitymeterurl, timeout=1)
      electricitymeteronline = True
  except:
      electricitymeteronline = False
      logging.warning(electricitymeterurl + ' could not read')
      
  if electricitymeteronline == True:
      json_content = electricitymeter.json()
      electricitymeter_total_in = int(json_content['StatusSNS']['Power']['Total_in'])
      electricitymeter_total_out = int(json_content['StatusSNS']['Power']['Total_out'])
      electricitymeter_now = int(json_content['StatusSNS']['Power']['Power_curr'])
  else:
      electricitymeter_total_in = 0
      electricitymeter_total_out = 0
      electricitymeter_now = 0
      logging.info('all electricitymeter information set to 0')

  #####calculated values:
  consumption = electricitymeter_now + inverter_now

  
  #######house
  draw.rectangle([(40,50),(device.width-40,device.width-20-15)], fill = "black", outline = "white", width = 3)
  draw.line([(40-3,50+3),(device.width/2,26)], fill = "red", width = 6) #left roof
  draw.line([(device.width-40+3,50+3),(device.width/2,26)], fill = "red", width = 6) #right roof
  draw.text((45,65), str(consumption) + 'W', font = font, fill = 'Yellow')
  draw.text((45,75), str(electricitymeter_total_in) + 'kWh', font = font, fill = 'Yellow')

  #######sun
  draw.ellipse([(-40,-40),(40,40)], fill = "yellow")
  if inverter_now >= 1:
   draw.ellipse([(-40-sunbeam,-40-sunbeam),(40+sunbeam,40+sunbeam)], outline = "yellow")
   sunbeam=sunbeam+4
   if sunbeam >= 4*4: sunbeam = 0
  draw.text((1,1), 'total:', font = font, fill = 'black')
  if inverter_total == 0: draw.text((1,11), '????', font = font, fill = 'black')
  else: 
   if sunkwh == 'tot':
    draw.text((1,11), str(round(inverter_adj)), font = font, fill = 'black')
    sunkwh = 'adj'
   else: 
    draw.text((1,11), '(' + str(round(inverter_total)) + ')', font = font, fill = 'black')
    sunkwh = 'tot'
   
  draw.text((1,21), 'kWh', font = font, fill = 'black')
  left, top, right, bottom = draw.textbbox((10,50), str(inverter_now) + 'W', font=font)
  draw.rectangle((left-1, top-1, right+1, bottom+1), fill="black")
  draw.text((10,50), str(inverter_now) + 'W', font = font, fill = 'white')

  #######powerline
  draw.line([(device.width-15,10),(device.width-20,40)], fill = "gray", width = 2)
  draw.line([(device.width-15,10),(device.width-10,40)], fill = "gray", width = 2)
  draw.line([(device.width-25,20),(device.width-5,20)], fill = "gray", width = 2)
  draw.line([(device.width-23,25),(device.width-7,25)], fill = "gray", width = 2)
  draw.text((device.width-30,50), str(electricitymeter_now) + 'W', font = font, fill = 'white')
  draw.text((device.width-60,5), str(electricitymeter_total_out) + 'kWh', font = font, fill = 'white')
  
  #######note
  if (electricitymeter_now > 0): draw.text((25,95), 'powered by net', font = font, fill = 'Yellow')
  if (electricitymeter_now < 0): draw.text((25,95), 'powered by sun', font = font, fill = 'Yellow')

  
  if (int(inverter_now) > 0):
  #########compare current consumption and current provided over inverter to know how much of current consumption cames from sun
   try:
    rate = int(device.width / consumption * inverter_now)
   except:
    rate = 0
    logging.warning('division zero: consumption = ' + str(consumption))

   if rate < device.width*0.6: color = 'red'
   elif rate < device.width*0.8: color = 'orange'
   else: color = 'green'
   draw.line([(0,107),(rate,107)], fill = color, width = 4)
   draw.text((0,112), 'cur. PV energy cons.', font = font, fill = 'Yellow')

  #########compare current provided over inverter and current consumption to know how much of current solar power are used from my household
   try:
    rate = int(device.width / inverter_now * consumption)
   except:
    rate = 0
    logging.warning('division zero: inverter_now = ' + str(inverter_now))
   if rate < device.width*0.6: color = 'red'
   elif rate < device.width*0.8: color = 'orange'
   else: color = 'green'
   
   draw.rectangle((0,121,rate,124), fill = color)

  #########compare complete provided from interver exclude the adjustemt with the complete provided over electricitymeter out to net to know how much of collected sun energy i use myself
   try:
    rate = int(device.width - (device.width / inverter_adj * electricitymeter_total_out))
   except:
    rate = 0
    logging.warning('division zero: inverter_adj = ' + str(inverter_adj))
   if rate < device.width*0.3: color = 'red'
   elif rate < device.width*0.6: color = 'orange'
   else: color = 'green'
   draw.rectangle((0,125,rate,127), fill = color)
   draw.text((0,device.height-10), str(round(inverter_adj)), font = font, fill = 'white')
   draw.text((device.width-10,device.height-10), str(round(electricitymeter_total_out)), font = font, fill = 'white')

def inverterurl():
 return('http://' + cf['inverter']['user'] + ':' + quote(cf['inverter']['pw']) + '@' + cf['inverter']['address'] + '/' + cf['inverter']['site'])

def electricitymeterurl():
 return('http://' + cf['electricitymeter']['address'] + '/' + cf['electricitymeter']['site'])

def prepare():
 ## font
 if cf['font']['ttf'] == True:
  try:
   font = ImageFont.truetype(cf['font']['ttffile'], cf['font']['ttfsize'])
  except:
   font = ImageFont.load_default()
   logging.error('font ' + cf['font']['ttffile'] + ' could not used. Use instead default font')
 else:
  font = ImageFont.load_default()
 globals()['font'] = font

 ##device urls 
 globals()['electricitymeterurl'] = str(electricitymeterurl())
 globals()['inverterurl'] = str(inverterurl())
 

def doublecheck():
 runninginstances = 0
 for p in psutil.process_iter():
  if re.search(os.path.abspath(__file__), str(p.cmdline())):
   runninginstances = runninginstances + 1
 if runninginstances >= 2:
  logging.warning('is already running')
  sys.exit("\033[91m {}\033[00m" .format('exit: is already running'))
 logging.debug('check no multiply starts')

def main():
 doublecheck() #ensure that only one instance is running at the same time
 prepare()
 device = get_device()
 while True:
  stats(device)
  time.sleep(cf['imagerefresh'])

if __name__ == '__main__':
 try:
  logging.debug('pass name')
  main()
 except KeyboardInterrupt:
  logging.info('interrupt via ctrl+c')
