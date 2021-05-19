# ParkPow_GateServer
Flask Server designed to run on Raspberry Pi for receiving ParkPow webhooks and opening gates.

This server is intended to interface with the Nexus 220 through the reader input terminals. It does this by setting the RTE pin to HIGH or LOW. LOW indicates that the 
relay should close and the gate should open. HIGH indicates that the relay should remain open and the gate should close.

Hardware Connection is as follows:
 
GPIO 5 ---------> READER 1 INPUTS <br />
GPIO 6 ---------> READER 2 INPUTS <br />
GPIO 13 --------> May function as an "Activity" light. Pin goes HIGH when the server is refreshing it's access lists. An LED may be connnected with a series resistor. <br />
Raspberry Pi GND -----------> READER 1 GND, READER 2 GND   

Note: It does not matter which GND pins you connect to the READER INPUTS. It only matters that the GND pins on both READER INPUTS are connect to GND pins on the Raspberry Pi.

# Client Stream Configuration 

The Raspberry Pi receives ParkPow data through port 8010. To forward data; You should modify the ParkPow Stream Configuration to forward all plate data to the Raspberry Pi's
IP Address and Port. For example, if raspberry pi is at IP Address 192.168.86.25 then the config.ini should have the following field entry:

webhook_target = http://192.168.86.25:8010/postJson

I also reccommend adding an additional field so that images are not forwarded:

webhook_image = no

# Installation

The only necessary files are the python dependencies and the service file. The service file is what allows the ParkPow gate server to run in the background. To set up
the dependencies you should use the installation script: install.sh

#Installation Instructions

## FOR INSTALLATION FROM GIT:

Execute the following commands:

cd ~/ <br />
git clone https://github.com/dmanla/ParkPow_GateServer.git <br />
cd ParkPow_GateServer <br />
sudo ./install.sh <br />
sudo reboot <br />

## FOR INSTALLATION FROM ZIP Directory:

Unzip the folder to your users home directory.

Execute the following commands:

cd ParkPow_GateServer <br />
sudo ./install.sh <br />
sudo reboot <br />





