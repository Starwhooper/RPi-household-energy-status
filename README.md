# RPi-status-via-luma #

I was looking for a way to measure the current energy consumption of my household and compare it with the photovoltaic system.
Basically, I'm not interested in long-term storage of the data, but rather in order to be able to spontaneously determine whether I'm currently purchasing energy from the grid or am already giving energy away to the grid operator

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
```

### config this tool:
```
sudo cp /opt/RPi-household-energy-status/config.json.example /opt/RPi-household-energy-status/config.json
sudo nano /opt/RPi-household-energy-status/config.json
```
add credentials from solar inverter

### add to autostart ###

add it to rc.local to autostart as boot
in case of 1.44" Waveshare:
```bash
sudo sed -i -e '$i \python3 /opt/RRPi-household-energy-status/comparedisplay.py --rotate 3 --config /opt/luma.examples/conf/st7735_128x128.conf &\n' /etc/rc.local
```

## Update
If you already use it, feel free to update with
```bash
cd /opt/RPi-status-via-luma
sudo git pull origin main
```

## Hardware
### Displays
i recommend using https://pinout.xyz/# as reverence

#### 1.44" Waveshare
https://www.waveshare.com/wiki/1.44inch_LCD_HAT

connections:
| Display Pin | Raspberry Pin |
|---|---|
| Display Pin 1 | Raspberry 3.3V |
| Display Pin 6 | Raspberry Ground Pin |
| Display **Pin 13** | Raspberry **Pin 18** |
| Display Pin 19 | Raspberry Pin 19 |
| Display **Pin 22** | Raspberry **Pin 16** |
| Display Pin 23 | Raspberry Pin 23 |
| Display Pin 24 | Raspberry Pin 24 |
