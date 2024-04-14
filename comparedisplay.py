#!/usr/bin/python3
# Creator: Thiemo Schuff
# Source: https://github.com/Starwhooper/RPi-household-energy-status

#######################################################
#
# prepare
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
 from PIL import Image
 from PIL import ImageDraw
 from urllib.parse import quote
 import RPi.GPIO as GPIO
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

logging.getLogger("urllib3")
logging.basicConfig(filename='/var/log/householdenergy.log', level=logging.DEBUG, encoding='utf-8', format='%(asctime)s:%(levelname)s:%(message)s')

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

KEY_PRESS_PIN  = 13
GPIO.setmode(GPIO.BCM) 
#GPIO.cleanup()
GPIO.setup(KEY_PRESS_PIN,   GPIO.IN, pull_up_down=GPIO.PUD_UP) # Input with pull-up

def inverterurl():
 return('http://' + cf['inverter']['user'] + ':' + quote(cf['inverter']['pw']) + '@' + cf['inverter']['address'] + '/' + cf['inverter']['site'])

def electricitymeterurl():
 return('http://' + cf['electricitymeter']['address'] + '/' + cf['electricitymeter']['site'])

def prepare():
 #####global vars with const value
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
 
# global device
 
def doublecheck():
 runninginstances = 0
 for p in psutil.process_iter():
  if re.search(os.path.abspath(__file__), str(p.cmdline())):
   if re.search("name='sudo'", str(p)):
    pass
   else:
    logging.warning('double start ' + str(runninginstances) + ': ' + str(p))
    runninginstances = runninginstances + 1
 if runninginstances >= 2:
  logging.warning('is already running')
  sys.exit("\033[91m {}\033[00m" .format('exit: is already running'))
 logging.debug('check no multiply starts')

#######################################################
#
# read an calculate
#
#######################################################

#####read inverter
def readinverter():
 
 try:
  inverter = requests.get(inverterurl, timeout=1)
  total = float(re.search(r'var\s+webdata_total_e\s*=\s*"([^"]+)"', inverter.text).group(1))
  now = int(re.search(r'var\s+webdata_now_p\s*=\s*"([^"]+)"', inverter.text).group(1))
 except:
  logging.warning('inverter could not read from: ' + inverterurl)
  total = -1
  now = 0
 return(total,now)
    
#####read electricitymeter
def readelectricitymeter():
 
 try:
  electricitymeter = requests.get(electricitymeterurl, timeout=1)
  json_content = electricitymeter.json()
  total_in = int(json_content['StatusSNS']['Power']['Total_in'])
  total_out = int(json_content['StatusSNS']['Power']['Total_out'])
  now = int(json_content['StatusSNS']['Power']['Power_curr'])
 except:
  total_in = -1
  total_out = -1
  now = 0
 return(total_in,total_out,now)

##### calculate values
def calculate():
#calculate inverter
 global inverter_now
 try: inverter_now
 except: inverter_now = 0
 
 global inverter_time
 try: inverter_time
 except: inverter_time = datetime(1977, 1, 1)
 
 global inverter_total
 global inverter_adj
 
 if (inverter_time <= datetime.now() - timedelta(minutes=1)) or inverter_now == 0:
  inv_t, inverter_now = readinverter()
  
  if inv_t >= 1: 
   inverter_total = inv_t
   inverter_time = datetime.now()
  else:
   try: inverter_total
   except: 
    inverter_total = 0
    logging.warning('inverter total count not found')
  
  inverter_adj = inverter_total + cf['inverter']['offset']  

 e_total_in, e_total_out, e_now = readelectricitymeter()

 global electricitymeter_total_in
 global electricitymeter_total_out
 if e_total_in >= 1:
  electricitymeter_total_in = e_total_in
  electricitymeter_total_out = e_total_out
  electricitymeteronline = True
 else:
  logging.warning('electricitymeter could not found')
  electricitymeteronline = False
  logging.warning(electricitymeterurl + ' could not read')
  try: electricitymeter_total_in = electricitymeter_total_in
  except: electricitymeter_total_in = 0
  try: electricitymeter_total_out = electricitymeter_total_out
  except: electricitymeter_total_out = 0
  logging.info('all electricitymeter information set to 0')
 
 global powersource
 if e_now <= 0: powersource = 'sun'
 else: powersource = 'net'

 global electricitymeter_now
 electricitymeter_now = e_now

#calculate others 
 global consumption
 consumption = electricitymeter_now + inverter_now
 global selfusedsunenergy
 try: selfusedsunenergy = inverter_adj - electricitymeter_total_out
 except: selfusedsunenergy = 0
 
 #########compare current consumption and current provided over inverter to know how much of current consumption cames from sun
 global rateconsumptionfromsun
 try:
  rateconsumptionfromsun = int(100 / consumption * inverter_now)
 except:
  rateconsumptionfromsun = 0
 
 #########compare current provided over inverter and current consumption to know how much of current solar power are used from my household
 global ratesolarpowerforhousehold
 try:
  ratesolarpowerforhousehold = int(100 / inverter_now * consumption)
 except:
  ratesolarpowerforhousehold = 0

 #########compare complete provided from interver exclude the adjustemt with the complete provided over electricitymeter out to net to know how much of collected sun energy i use myself
 global rateinverteradjvselectricimetertotalout
 try:
  rateinverteradjvselectricimetertotalout = int(100 / inverter_adj * (selfusedsunenergy))
 except:
  rateinverteradjvselectricimetertotalout = 0

#######################################################
#
# create output image
#
#######################################################

def colorbar(rate):
 if rate > 80: color = 'green'
 elif rate > 60: color = 'orange'
 elif rate > 40: color = 'yellow'
 else: color = 'red'
 return(color)
 
def createimage(imagewidth,imageheight):
 global outputimage
 global sunbeam
 try: sunbeam
 except: sunbeam = 0
 global sunkwh
 try: sunkwh
 except: sunkwh = 'tot'
 global imagestyle
 try: imagestyle
 except: imagestyle = cf['imagestyle']
 
 outputimage = Image.new(mode="RGB", size=(imagewidth,imageheight))
 draw = ImageDraw.Draw(outputimage)
 y=0

 if GPIO.input(KEY_PRESS_PIN) == 0: # button is released
  if imagestyle == 'detail':
   imagestyle = 'pretty'
   logging.info('changes imagestyle to pretty')
  elif imagestyle == 'pretty':
   imagestyle = 'detail'
   logging.info('changes imagestyle to detail')
  
 if imagestyle == 'detail':
  detailfont = ImageFont.truetype(cf['font']['ttffile'], 10)#cf['font']['ttfsize'])
  draw.text((0,y),  'consumtion:     ' + str(consumption) + 'W', font = detailfont, fill = 'white')
  y += 10
  draw.text((0,y), 'net now:        ' + str(electricitymeter_now) + 'W', font = detailfont, fill = 'white')
  y += 10
  draw.text((0,y), 'net total in:   ' + str(electricitymeter_total_in) + 'kWh', font = detailfont, fill = 'white')
  y += 10
  draw.text((0,y), 'net total out:  ' + str(electricitymeter_total_out) + 'kWh', font = detailfont, fill = 'white')
  y += 10
  draw.text((0,y), 'inverter now:   ' + str(inverter_now) + 'W', font = detailfont, fill = 'white')
  y += 10
  draw.text((0,y), 'inverter total: ' + str(round(inverter_total)) + 'kWh', font = detailfont, fill = 'white')
  y += 10
  draw.text((0,y), 'inverter adj:   ' + str(round(inverter_adj)) + 'kWh', font = detailfont, fill = 'white')
  y += 10
  #########compare current consumption and current provided over inverter to know how much of current consumption cames from sun
  draw.text((0,y), 'cur. req. prov. by sun', font = detailfont, fill = 'white')
  y += 12
  try: draw.rectangle(((0,y,int(imagewidth / 100 * rateconsumptionfromsun),y+4)), fill = colorbar(rateconsumptionfromsun), width = 1)
  except: pass
  y += 3
  #########compare current provided over inverter and current consumption to know how much of current solar power are used from my household
  draw.text((0,y), 'cur. use of PV energy', font = detailfont, fill = 'white')  
  y += 12
  try: draw.rectangle((0,y,int(imagewidth / 100 * ratesolarpowerforhousehold),y+4), fill = colorbar(ratesolarpowerforhousehold), width = 1)
  except: pass
  y += 3
  #########compare complete provided from interver exclude the adjustemt with the complete provided over electricitymeter out to net to know how much of collected sun energy i use myself
  draw.text((0,y), str(round(inverter_adj - electricitymeter_total_out)) + 'kWh in vs. ' + str(round(electricitymeter_total_out)) + 'kWh out', font = detailfont, fill = 'white')
  y += 12
  draw.rectangle((0,y,int(imagewidth / 100 * rateinverteradjvselectricimetertotalout),y+4), fill = colorbar(rateinverteradjvselectricimetertotalout), width = 1)
  
 if imagestyle == 'pretty':
  #######house
  draw.rectangle([(40,50),(imagewidth-40,imagewidth-20-15)], fill = "black", outline = "white", width = 3)
  draw.line([(40-3,50+3),(imagewidth/2,26)], fill = "red", width = 6) #left roof
  draw.line([(imagewidth-40+3,50+3),(imagewidth/2,26)], fill = "red", width = 6) #right roof
  draw.text((45,65), str(consumption) + 'W', font = font, fill = 'Yellow')
  draw.text((45,75), str(electricitymeter_total_in) + 'kWh', font = font, fill = 'Yellow')
  #######sun
  draw.ellipse([(-40,-40),(40,40)], fill = "yellow")
  if inverter_now >= 1:
   pass
   draw.ellipse([(-40-sunbeam,-40-sunbeam),(40+sunbeam,40+sunbeam)], outline = "yellow")
   sunbeam=sunbeam+4
   if sunbeam >= 4*4: sunbeam = 0
  draw.text((1,11), str(inverter_now) + 'W', font = font, fill = 'black')
  #######powerline
  draw.line([(imagewidth-15,10),(imagewidth-20,40)], fill = "gray", width = 2)
  draw.line([(imagewidth-15,10),(imagewidth-10,40)], fill = "gray", width = 2)
  draw.line([(imagewidth-25,20),(imagewidth-5,20)], fill = "gray", width = 2)
  draw.line([(imagewidth-23,25),(imagewidth-7,25)], fill = "gray", width = 2)
  draw.text((imagewidth-30,50), str(electricitymeter_now) + 'W', font = font, fill = 'white')
  #######note
  draw.text((25,95), 'powered by ' + powersource, font = font, fill = 'Yellow')
  
#######################################################
#
# output
#
#######################################################

def output(device):
 global lastimageexport
 try: lastimageexport
 except: lastimageexport = datetime(1977, 1, 1)
 if lastimageexport <= datetime.now() - timedelta(seconds=cf['imageexport']['intervall']):
  if cf['imageexport']['active'] == True:
   exportpathfile = cf['imageexport']['path']
   try:
    outputimage.save(exportpathfile)
    logging.info('saved current displaycontent to: ' + exportpathfile)
    lastimageexport = datetime.now()
   except:
    logging.info(exportpathfile + 'could not saved')
 device.display(outputimage)
 logging.debug('show an display')
 
#######################################################
#
# start
#
#######################################################
 
def main():
# doublecheck() #ensure that only one instance is running at the same time
 prepare()
 device = get_device()
 while True:
  calculate()
  createimage(device.width,device.height)
  output(device)
  time.sleep(cf['imagerefresh'])

if __name__ == '__main__':
 try:
  logging.debug('pass name')
  main()
 except KeyboardInterrupt:
  logging.info('interrupt via ctrl+c')
