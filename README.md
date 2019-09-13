# Weather display

Python source code for Raspberry PI of weather display based on Waveshare 2.13" eInk display.

<iframe width="560" height="315" src="https://www.youtube.com/embed/5isk_31pB18" frameborder="0" allow="accelerometer; autoplay; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>

TL;DR to make it work on raspberry pi

```
git clone https://github.com/rmrfus/weather-display

sudo raspi-config nonint do_spi 0
sudo apt install libopenjp2-7 libtiff5 spi-tools imgcat geopy fonts-lato
sudo pip3 install loguru click pillow spidev rpi.gpio imgcat geopy

cd weather-display
mkdir fonts

cp config-sample.py config.py
# edit config.py and enter your darksky API key and geonames username

curl -Lo fonts/LexendDeca-Regular.ttf 'https://github.com/ThomasJockin/lexend/blob/master/fonts/ttf/LexendDeca-Regular.ttf?raw=true'
curl -Lo fonts/weathericons-regular-webfont.ttf 'https://github.com/erikflowers/weather-icons/blob/master/font/weathericons-regular-webfont.ttf?raw=true'

sudo python3 weather.py --preview --draw bellevue wa
```
