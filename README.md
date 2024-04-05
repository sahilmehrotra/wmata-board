# WMATA (DC Metro) Train Display

Work-in-progress 64x32 LED display that is used to display train data from WMATA (DC Metro). I first started this project in 2018 out of a desire to have my own version of a PIDS (the board at a metro station that shows how many minutes away a train is) in my apartment. 

Hardware used: 
- Raspberry Pi 4
- Adafruit RGB Matrix Hat
- 64x32 LED display

This project is current split up over three files: `wmata.py`, `piScriptRunner.py`, and `incidents.py`. The incidents.py file is forked almost entirely from a similar (and better!) [project](https://github.com/kenschneider18/rpi-metro-display) which has a really cool way to display alerts/incident data that mirrors the way the WMATA project works. 

Generally speaking, the wmata.py file includes a number of options/flags that have been added over time as I adjusted my preferences/needs. As of today, the board displays train predictions, weather, alert data, as well as current date and time. 

A few notes on some old information that I cut (but for most, functionality remains to restore)
- Header row for the board before the data itself
- Number of cars for the train
- An older/basic way of displaying alerts
- DC MetroHero API integration (RIP)

One variable worth calling out in the wmata script is `minTrainDistance`:  this is a feature that filters out trains that are too close to the station for you to make it from your apartment to the station. by default it is set to 5. 

I run the code currently with a scriptRunner python file with a `--led-gpio-mapping=adafruit-hat-pwm` flag. 

One important note, as of initial upload on April 4, I made a few different changes to push stuff into an .env variable (like wmata API keys, home station, etc) and I have NOT yet gotten to make sure that I didn't make any typos, etc. 

 A few of my to-dos, both in terms of features I want to add as well as bug fixes/code cleanup: 
 
 - Configuration script at the very start, which saves a setting file. Board height, etc. but also the lines that we're tracking (which is currently hardcoded)
	 - Could pull all the train predictions (higher network load, but maybe just simpler?), or initial setup figures out what lines your "home" station tracks, etc. and saves that down. a few different ways to do this, all better than the current version. 
 - To that end, clean up hardcoding of lots of variables throughout the code
 - Figure out a better way to manage settings generally — ideally a web server / page where you can configure all the various switches and settings, but there may be a simpler way to do so
 - The three files are a complete mess right now, and need to be reorganized. Originally wmata.py was written to be shared and the piscriptrunner was meant to be a handler of sorts, but I've written a lot of functionality into the second that might warrant some cleanup 
 - General rewrite — for a lot of the code, I don't even remember how/why I wrote it the way I did, especially the way the text scrolls. There is almost certainly a better/cleaner way to do this, and should live in its own python file. 
 - Get rid of the getters/setters? Especially the ones that are truly useless. I think there are probably too many, not a very pythonic way of writing code to begin with (I originally learned to code with Java, which is probably very clear if you read my code!)
 - improve this readme: show people how to use this project themselves, how to build it, etc! 

there are certainly better projects out there on github on there doing this work, but wanted to have a place to keep my own work on this! 