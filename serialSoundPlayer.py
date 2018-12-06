#! /usr/bin/python
#

import threading
import serial
import time
import pygame
import csv
import json

from pygame import mixer

class WavePlayer:
    def __init__(self):
        #set up the mixer
        freq = 44100     # audio CD quality
        bitsize = -16    # unsigned 16 bit
        channels = 1     # 1 is mono, 2 is stereo
        buffer = 2048    # number of samples (experiment to get right sound)
        pygame.mixer.init(freq, bitsize, channels, buffer)
        pygame.mixer.init() #Initialize Mixer
        self.channelsInstances = dict()
        self.loop = False
        self.stopPlaying = True
        
        self.audio = None
        self.channel = None

        self.lock = threading.Lock()
        self.stop_event = threading.Event()
        self.t = threading.Thread(target=self.playAudio_t)
        self.t.start()

    def enableLoop(self):
        self.lock.acquire()
        try:
            if not self.loop:
                self.loop = True
            print "Loop Enabled" 
        finally:
            self.lock.release()
    
    def disableLoop(self):
        self.lock.acquire()
        try:
            if self.loop:
                self.loop = False
            print "Loop Disabled" 
        finally:
            self.lock.release()

    def stop(self):
        self.lock.acquire()
        try:
            if not self.stopPlaying:
                self.stopPlaying = True
            print "STOPPED" 
        finally:
            self.lock.release()
    
    def addAudios(self,audios):
        print "Audios are: ", len(audios)
        print(json.dumps(audios, indent = 4))
        pygame.mixer.set_num_channels(3)
        channel = pygame.mixer.Channel(2)
        for entry in audios.keys():
            #print "Try to add", entry,"file:", audios[entry][0] ,"in channels:", audios[entry][1]
            audio = pygame.mixer.Sound(audios[entry][0])
            audio.set_volume(1.0)
            self.channelsInstances.update({entry:[audio,channel]})

    def playAudio_t(self):
        print "Audio thread started"

        _stop = True
        _loop = False

        while not self.stop_event.isSet():
            
            self.lock.acquire()
            try: 
                _stop = self.stopPlaying
                _loop = self.loop
                #print "Update Params stop:",_stop,"loop:",_loop
            finally:
                #print("Release Params")
                self.lock.release()

                if _loop:
                    while True and (not _stop):
                        #print("Print")
                        self.channel.play(self.audio)
                        while self.channel.get_busy() and (not _stop):
                            pygame.time.wait(10)

                            self.lock.acquire()
                            try:
                                #print("Update Params")
                                _stop = self.stopPlaying
                                _loop = self.loop 
                            finally:
                                #print("Release Params")
                                self.lock.release()
                        self.channel.stop()
                elif self.channel is not None and not _stop:
                    print "Single Play"
                    self.channel.play(self.audio)
                    
                    while self.channel.get_busy() and (not _stop):
                        pygame.time.wait(10)
                        self.lock.acquire()
                        try:
                            #print("Update Params")
                            _stop = self.stopPlaying
                            _loop = self.loop 
                        finally:
                            #print("Release Params")
                            self.lock.release()
                    self.channel.stop()
                    _stop = True
                    self.lock.acquire()
                    try:
                        #print("Update Params")
                        self.stopPlaying = _stop
                    finally:
                        #print("Release Params")
                        self.lock.release()

    def play(self,key):
        
        self.stop()
        
        self.lock.acquire()
        try:
            print "Key is:",key
            ret = self.channelsInstances.get(key,None)
            self.channel = ret[1]
            self.audio = ret[0]
            self.stopPlaying = False
        finally:
            self.lock.release()
        print "Play_t ", key,"stop:",self.stopPlaying

    def close(self):
        print "Request thread to stop."
        self.stop_event.set()
        self.stop()
        # Wait for thread to exit.
        self.t.join()

    #def __enter__(self):
        # Nothing to do, thread already started.  Could start
        # thread here to enforce use of context manager.

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

########################################################################
# Global Variables   -  Yes I know these are bad...

ready=0                        # ready to send command to arduino
timeout = 0                    # To avoid infinite wait state, we will count 100 loops and assume failure 
line = None                     # Holds current response from Arduino Serial
line_len = 0                    # number of items in "line"
parsingData = False
prev = None

audiosInfo = None

##########################################################################
# Declare functions    

def get_arduino_response():
   global line
   global line_len
   
   if (arduino.inWaiting() > 0):
       line = arduino.readline()
       line = line[:-2]
       line_len = len(line)
       #print 'Receiving: ', line,' size: ', line_len

try:
    arduino = serial.Serial('/dev/tty.usbmodem14201',9600)#,serial.PARITY_NONE,serial.STOPBITS_ONE)#,serial.EIGHTBITS,1)
    parsingData = True

except serial.SerialException as e0:
    print "ERROR:", e0
    arduino.close()
    pass
except IOError as e1: # if port is already opened, close it and open it again and print message
    print "ERROR:", e1
    arduino.close()
    arduino.open()
    print ("port was already open, was closed and opened again!")


#time.sleep(10)    # Time for Arduino to reset and settle
#arduino.flushInput()   

##########################################################################
# Main Loop
try:

    path = "./audio"
    
    audios = {
        "freeLine": [path+"/freeLine.wav",0],
        "wrongLine": [path+"/wrongLine.wav",1],
        }
    
    numbers = dict()
    with open(path+"/numbers.csv", 'rb') as csvfile:
        audiosInfo = csv.reader(csvfile, delimiter=',', quotechar='|')
        for row in audiosInfo:
            audios.update({row[1]:[row[2],int(row[3])]})
            numbers.update({row[0]:row[1]})

    audioPlayer = WavePlayer()
    audioPlayer.addAudios(audios)

    while parsingData:                    # Continuous loop
        # os.system('clear')
        stamp = time.time()

        get_arduino_response()                   # If data available from arduino, retrieve into "line"

        if line == "000000" and line_len == 6:    # Ensure entire line came through 
            if not (prev == line):  
                audioPlayer.stop()
        elif line == "000001" and line_len == 6:    # Ensure entire line came through 
            if not (prev == line):
                audioPlayer.enableLoop()
                audioPlayer.play("freeLine")
        elif line_len == 6:
            if not (prev == line):
                ret = numbers.get(line,None)
                if ret is not None:
                    audioPlayer.disableLoop()
                    audioPlayer.play(ret)
                else:
                    audioPlayer.enableLoop()
                    audioPlayer.play("wrongLine")
        prev = line

except (KeyboardInterrupt, SystemExit): #when you press ctrl+c
    arduino.close()
    audioPlayer.close()
print "Done.\nExiting."