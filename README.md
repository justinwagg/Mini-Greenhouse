# Mini Greenhouse
## RPi Controlled Greenhouse
This project monitors the temperature and humidity inside a greenhouse, as well as controlling the grow lighting. 

`green.py` Controls the lighting, as well as monitoring temperature & humidity. Data is stored locally with MySQL.
'launcher.sh' is called with cron and waits 5 seconds for MySQL to boot before running `green.py`.

## Pinout
	                            J8
	                           .___.              
	                  +3V3---1-|O O|--2--+5V
	    			 GPIO2---3-|O O|--4--+5V
	    			 GPIO3---5-|O O|--6--_
Inner DHT Sensor	 GPIO4---7-|O O|--8-----GPIO14 
	                      _--9-|O.O|-10-----GPIO15 
	    			GPIO17--11-|O O|-12-----GPIO18
	    			GPIO27--13-|O O|-14--_
	    			GPIO22--15-|O O|-16-----GPIO23	LED MOSFET
	                  +3V3--17-|O O|-18-----GPIO24 
Outer DHT Sensor	GPIO10--19-|O.O|-20--_
	    			GPIO9 --21-|O O|-22-----GPIO25 
	    			GPIO11--23-|O O|-24-----GPIO8  
	                      _-25-|O O|-26-----GPIO7  
	       			ID_SD---27-|O O|-28-----ID_SC 
	 				GPIO5---29-|O.O|-30--_
	 				GPIO6---31-|O O|-32-----GPIO12
	                GPIO13--33-|O O|-34--_
Fan MOSFET			GPIO19--35-|O O|-36-----GPIO16
Fan Power			GPIO26--37-|O O|-38-----GPIO20
	                      _-39-|O O|-40-----GPIO21
	                           '---'