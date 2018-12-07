#!/bin/bash
for files in *.wav; do /Applications/ffmpeg -i "$files" -acodec pcm_s16le -ar 44100 "./new/$files";done