# RPi-status-via-luma #

To provide the Status of your Raspberry (tested on Zero, 2, 3 and 4) to an ST7735S OLED Display.

I use this script to get a quick and up-to-date status of the system every time I walk past my Raspberry Pis.
In this way I can see at a glance the current workload, whether problems are looming and whether the service is currently running.

My Raspberrys prepared to mounted in my 19Rack:
![Raspberry Pis im Rack](https://media.printables.com/media/prints/300085/images/2715870_a53f284c-180c-4feb-9401-bd60474f65ca/thumbs/inside/1920x1440/jpg/img20221108094538.webp)

Please also note my previous solution based on Wireshark 144: https://github.com/Starwhooper/RPi-status-on-OLED

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
