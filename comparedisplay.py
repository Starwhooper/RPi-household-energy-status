#!/usr/bin/python3
# Creator: Thiemo Schuff, thiemo@schuff.eu
# Source: https://github.com/Starwhooper/RPi-status-via-luna

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
 from PIL import Image, ImageDraw
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
 global inverter_total
 global inverter_now
 try:
  invertertime
 except:
  invertertime = datetime(1977, 1, 1)
 
 with canvas(device, dither=True) as draw:
  if (invertertime <= datetime.now() - timedelta(minutes=1)):
   print(invertertime)   
   print(datetime.now())
   print(timedelta(minutes=1))
   inverter = requests.get(inverterurl)
   if inverter.status_code == 200:
    html_content = inverter.text
    try:
     inverter_total = re.search(r'var\s+webdata_total_e\s*=\s*"([^"]+)"', inverter.text).group(1)
     inverter_total = float(inverter_total)
     inverter_total = round(inverter_total)
     inverter_now = re.search(r'var\s+webdata_now_p\s*=\s*"([^"]+)"', inverter.text).group(1)
     invertertime = datetime.now()
    except:
     inverter_now = 0 
   else:
    inverter_now = 0 
  
  #####get electricitymeter
  try:
      electricitymeter = requests.get(electricitymeterurl)
      electricitymeteronline = True
  except:
      electricitymeteronline = False
      
  if electricitymeteronline == True:
      json_content = electricitymeter.json()
      electricitymeter_total = json_content['StatusSNS']['Power']['Total_in']
      electricitymeter_now = json_content['StatusSNS']['Power']['Power_curr']
  else:
      electricitymeter_total = 0
      electricitymeter_now = 0
  
  #####image

  #######house
  draw.rectangle([(40,60),(128-40,128-20)], fill = "black", outline = "white", width = 2)
  draw.line([(40,60),(128/2,20)], fill = "red", width = 2)
  draw.line([(128-40,60),(128/2,20)], fill = "red", width = 2)
  draw.text((55,80), str(int(electricitymeter_now) + int(inverter_now)) + 'W', font = font, fill = 'Yellow')

  #######sun
  draw.ellipse([(-40,-40),(40,40)], fill = "yellow")
  draw.text((1,1), 'total:', font = font, fill = 'black')
  draw.text((1,11), str(inverter_total), font = font, fill = 'black')
  draw.text((1,21), 'kWh', font = font, fill = 'black')
  draw.text((10,50), str(inverter_now) + 'W', font = font, fill = 'white')

  #######powerline
  draw.line([(128-15,10),(128-20,40)], fill = "gray", width = 2)
  draw.line([(128-15,10),(128-10,40)], fill = "gray", width = 2)
  draw.line([(128-25,20),(128-5,20)], fill = "gray", width = 2)
  draw.line([(128-23,25),(128-7,25)], fill = "gray", width = 2)
  draw.text((128-30,50), str(electricitymeter_now) + 'W', font = font, fill = 'white')
  
  #######note
  if (electricitymeter_now > 0): draw.text((25,110), 'powered by net', font = font, fill = 'Yellow')
  if (electricitymeter_now < 0): draw.text((25,110), 'powered by sun', font = font, fill = 'Yellow')
  if (int(inverter_now) > 0):
   rate =  int(128 / (int(inverter_now)) * (int(electricitymeter_now) + int(inverter_now)))

   color = 'green'
   if rate < 80: color = 'orange'
   if rate > 128: color = 'red'
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