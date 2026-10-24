#!/usr/bin/env bash
# Add music to Diwali 01: "Vadodora" (Kevin MacLeod) under the silent render; original clip audio muted.
# usage: tools/mix_diwali01.sh <workdir>   (workdir holds diwali01_video_only.mp4 and music/Vadodora.mp3)
set -euo pipefail
cd "$1"
ffmpeg -v error -y -i music/Vadodora.mp3 -af "atrim=start=1.2:duration=30,asetpts=PTS-STARTPTS,aresample=48000,\
volume=-4dB,afade=t=in:d=0.4,afade=t=out:st=28:d=2,alimiter=limit=0.89" mix_music.wav
ffmpeg -v error -y -i diwali01_video_only.mp4 -i mix_music.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 192k \
  -shortest -movflags +faststart diwali01_music_only.mp4

# Teaser (tools/render_teaser01.py -> teaser01_video_only.mp4): 10s, music only, fades with the picture.
if [ -f teaser01_video_only.mp4 ]; then
  ffmpeg -v error -y -i music/Vadodora.mp3 -af "atrim=start=1.2:duration=10,asetpts=PTS-STARTPTS,aresample=48000,\
volume=-3dB,afade=t=in:d=0.3,afade=t=out:st=9.0:d=1,alimiter=limit=0.89" teaser_music.wav
  ffmpeg -v error -y -i teaser01_video_only.mp4 -i teaser_music.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 192k \
    -shortest -movflags +faststart teaser01_music.mp4
fi
