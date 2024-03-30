#!/usr/bin/python3
# Creator: Thiemo Schuff
# Source: https://github.com/Starwhooper/RPi-household-energy-status

#######################################################
#
# Prepare
#
#######################################################

##### check if all required packages are aviable
import sys
try:
 from luma.core.render import canvas
 from PIL import ImageFont
# from PIL import Image, ImageDraw
 from urllib.parse import quote
 import json
 import os
 import psutil
 import requests
 import re
 import time
 from datetime import datetime, timedelta  
except:
 sys.exit("\033[91m {}\033[00m" .format('any needed package is not aviable. Please check README.md to check which components shopuld be installed via pip3".'))

##### ensure that only one instance is running at the same time
runninginstances = 0
for p in psutil.process_iter():
 if len(p.cmdline()) == 2:
  if p.cmdline()[0] == '/usr/bin/python3':
   if p.cmdline()[1] == os.path.abspath(__file__):
    runninginstances += 1
if runninginstances >= 2:
 sys.exit("\033[91m {}\033[00m" .format('exit: is already running'))
 
##### import config.json
try:
 with open(os.path.split(os.path.abspath(__file__))[0] + '/config.json','r') as file:
  cf = json.loads(file.read())
except:
 sys.exit("\033[91m {}\033[00m" .format('exit: The configuration file ' + os.path.split(os.path.abspath(__file__))[0] + '/config.json does not exist or has incorrect content. Please rename the file config.json.example to config.json and change the content as required '))

##### import module demo_opts
try:
 sys.path.append(cf['luma']['demo_opts.py']['folder'])
 from demo_opts import get_device
except:
 sys.exit("\033[91m {}\033[00m" .format('file ' + cf['luma']['demo_opts.py']['folder'] + '/demo_opts.py not found. Please check config.json or do sudo git clone https://github.com/rm-hull/luma.examples /opt/luma.examples'))

###### set defaults
if cf['font']['ttf'] == True:
 font = ImageFont.truetype(cf['font']['ttffile'], cf['font']['ttfsize'])
else:
 font = ImageFont.load_default()

inverterurl = 'http://' + cf['inverter']['user'] + ':' + quote(cf['inverter']['pw']) + '@' + cf['inverter']['address'] + '/' + cf['inverter']['site']
electricitymeterurl = 'http://' + cf['electricitymeter']['address'] + '/' + cf['electricitymeter']['site']

inverter_total =  0

##### do output
def stats(device):
 global invertertime
 try: invertertime
 except: invertertime = datetime(1977, 1, 1)
 global inverter_total
 try: inverter_total
 except: inverter_total = 0
 global inverter_now
 global sunbeam
 try: sunbeam
 except: sunbeam = 0 


 
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
  
  #####get electricitymeter
  try:
      electricitymeter = requests.get(electricitymeterurl)
      electricitymeteronline = True
  except:
      electricitymeteronline = False
      
  if electricitymeteronline == True:
      json_content = electricitymeter.json()
      electricitymeter_total_in = int(json_content['StatusSNS']['Power']['Total_in'])
      electricitymeter_total_out = int(json_content['StatusSNS']['Power']['Total_out'])
      electricitymeter_now = int(json_content['StatusSNS']['Power']['Power_curr'])
  else:
      electricitymeter_total_in = 0
      electricitymeter_total_out = 0
      electricitymeter_now = 0

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
  else: draw.text((1,11), str(round(inverter_total)), font = font, fill = 'black')
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
   rate = int(device.width / consumption * inverter_now) #welchen Anteil des Energiebedarfs ziehe ich aus der Sonne
   if rate < device.width*0.6: color = 'red'
   elif rate < device.width*0.8: color = 'orange'
   else: color = 'green'
   draw.line([(0,107),(rate,107)], fill = color, width = 4)
  
   draw.text((10,112), 'self used sunenergy', font = font, fill = 'Yellow')
   rate = int(device.width / inverter_now * consumption) #Welchen Anteil der Sonnenergie verbrauche ich selbst
   if rate < device.width*0.6: color = 'red'
   elif rate < device.width*0.8: color = 'orange'
   else: color = 'green'
   draw.line([(0,125),(rate,125)], fill = color, width = 4)

def main():
 while True:
  stats(device)
  time.sleep(cf['imagerefresh'])

if __name__ == '__main__':
 try:
  device = get_device()
  main()
 except KeyboardInterrupt:
  pass
