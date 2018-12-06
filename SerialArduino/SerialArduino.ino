#include <Keyboard.h>

int needToPrint = 0;
int count;
int dialIn = 2;
int buttonIn = 3;

int lastState = LOW;
int trueState = LOW;
long lastStateChangeTime = 0;
int cleared = 0;

// constants

int dialHasFinishedRotatingAfterMs = 100;
int debounceDelay = 16;
//int debounceDelay = 10;

int numberLength = 6;
//int numberLength = 10;

long lastDebounceTime = 0;
long buttonDebounceDelay = 50;

String targetProject;

void setup()
{
    Serial.begin(9600);
    pinMode(dialIn, INPUT);
    pinMode(buttonIn, INPUT);
    targetProject = "";
}
void printNoSound()
{
  Serial.println(numberLength == 6 ? "000000" : "0000000000");
}

void printFreeLine()
{
  Serial.println(numberLength == 6 ? "000001" : "0000000001");
}

int reading;
int previous = LOW;
int buttonState = LOW;

bool freeLinSent = false;

void phone()
{       
    int readingPhone = digitalRead(dialIn);
  
      if ((millis() - lastStateChangeTime) > dialHasFinishedRotatingAfterMs) {
          // the dial isn't being dialed, or has just finished being dialed.
          if (needToPrint) {
              // if it's only just finished being dialed, we need to send the number down the serial
              // line and reset the count. We mod the count by 10 because '0' will send 10 pulses.
              targetProject += String(count % 10);
              //Serial.println(count % 10, DEC);
  
              if(targetProject.length() == numberLength)
              {
                  Serial.println(targetProject);
                  //targetProject = "";
              }
              needToPrint = 0;
              count = 0;
              cleared = 0;
          }
      } 
  
      if (readingPhone != lastState) {
          lastStateChangeTime = millis();
      }
  
      if ((millis() - lastStateChangeTime) > debounceDelay) {
          // debounce - this happens once it's stablized
          if (readingPhone != trueState) {
              // this means that the switch has either just gone from closed->open or vice versa.
              trueState = readingPhone;
              if (trueState == HIGH) {
                  // increment the count of pulses if it's gone high.
                  count++; 
                  needToPrint = 1; // we'll need to print this number (once the dial has finished rotating)
              } 
          }
      }
      lastState = readingPhone;
}
void loop()
{
   buttonState = digitalRead(buttonIn);
 
  
    if ( buttonState == HIGH) {
      printNoSound();
      targetProject = "";
    }
    else if ( buttonState == LOW) {
      if(targetProject.length() == 0)
        printFreeLine();
      else if(targetProject.length() < numberLength) 
        printNoSound();
      phone();
    }
}
