# RPi-household-energy-status #

I was looking for a way to measure the current energy consumption of my household and compare it with the photovoltaic system.
Basically, I'm not interested in long-term storage of the data, but rather in order to be able to spontaneously determine whether I'm currently purchasing energy from the grid or am already giving energy away to the grid operator

![status](IMG20240326144308.jpg)

## Installation
install all needed packages to prepare the software environtent of your Raspberry Pi:

### enable SPI
```bash
sudo raspi-config
```

### install required components
choose luma.lcd (SPI)
```bash
sudo apt install python3-luma.lcd python3-psutil git -y
sudo git clone https://github.com/rm-hull/luma.examples /opt/luma.examples
```

### install this tool itself:
```bash
sudo git clone https://github.com/Starwhooper/RPi-household-energy-status /opt/RPi-household-energy-status
sudo chmod +x /opt/RPi-household-energy-status/comparedisplay.py
```

### config this tool:
```
sudo cp /opt/RPi-household-energy-status/config.json.example /opt/RPi-household-energy-status/config.json
sudo nano /opt/RPi-household-energy-status/config.json
```
* add credentials from solar inverter
* add ip adress from solar inverter an tasmota smartmeter

### add to autostart ###
add it to rc.local to autostart as boot
```bash
sudo sed -i -e '$i \/opt/RPi-household-energy-status/comparedisplay.py --rotate 2 --display=st7735 --interface=spi --spi-bus-speed=16000000 --gpio-reset=27 --gpio-data-command=25 --gpio-backlight=24 --width=128 --height=128 --bgr --h-offset=1 --v-offset=2 --backlight-active=high &\n' /etc/rc.local
```

## Update
If you already use it, feel free to update with
```bash
cd /opt/RPi-household-energy-status
sudo git pull origin main
```

## Hardware
### Display
1.44" Waveshare
https://www.waveshare.com/wiki/1.44inch_LCD_HAT
### Case
STL Files: https://www.printables.com/de/model/258922-raspberry-pi-zero-with-waveschare-144-display-case
