#!/usr/bin/env bash
# Mix the creator's voiceover into the night-style reel (tools/render_reel01_night.py, 25.8s).
# usage: tools/mix_reel01_vo.sh <workdir>
#   <workdir>/diwali01_video_only.mp4  silent render
#   <workdir>/vo/raw.oga               voice note (WhatsApp), six lines with pauses
#   <workdir>/music/Vadodora.mp3
set -euo pipefail
cd "$1"
TOTAL=25.8
# source cut (start end) -> timeline start, one per line; times found with silencedetect + Whisper word stamps
CUTS=(
  "1.15 4.00 0.20"    # Is Diwali, aapki rangoli ho kuch unique
  "4.60 8.55 3.25"    # Market mein stencils toh bahut hain, par sab ek jaise hain
  "9.57 13.90 7.50"   # Isliye humne khud design kiya hai, special Diwali aur Dhanteras ke liye
  "15.50 17.50 12.70" # Ye hai hamara Kalash stencil
  "19.87 24.20 16.10" # Bas stencil rakho, rang bharo, aur perfect rangoli ready
  "25.48 29.30 21.10" # Diwali se pehle apna order karo, abhi DM karo
)
ffmpeg -v error -y -i vo/raw.oga -af "aresample=48000,adeclip,highpass=f=85,lowpass=f=12000,\
equalizer=f=250:t=q:w=1:g=-2,equalizer=f=3500:t=q:w=1.4:g=2.5,acompressor=threshold=-20dB:ratio=3:attack=5:release=120" vo/clean.wav
inputs=(); chains=""; mix=""
for i in "${!CUTS[@]}"; do
  read -r s e at <<<"${CUTS[$i]}"
  inputs+=(-i vo/clean.wav)
  d=$(python3 -c "print(round($e-$s,3))")
  chains+="[$i:a]atrim=start=$s:end=$e,asetpts=PTS-STARTPTS,afade=t=in:d=0.04,afade=t=out:st=$(python3 -c "print(round($d-0.08,3))"):d=0.08,adelay=$(python3 -c "print(int($at*1000))"):all=1[v$i];"
  mix+="[v$i]"
done
ffmpeg -v error -y "${inputs[@]}" -filter_complex "${chains}${mix}amix=inputs=${#CUTS[@]}:normalize=0,apad=whole_dur=$TOTAL,\
loudnorm=I=-16:TP=-1.5:LRA=7,aresample=48000,aformat=channel_layouts=stereo[out]" -map "[out]" vo_track.wav
ffmpeg -v error -y -i music/Vadodora.mp3 -i vo_track.wav -filter_complex "\
[0]atrim=start=1.2:duration=$TOTAL,asetpts=PTS-STARTPTS,aresample=48000,aformat=channel_layouts=stereo,volume=-9dB,\
afade=t=in:d=0.4,afade=t=out:st=$(python3 -c "print($TOTAL-2)"):d=2[m];\
[1]asplit[sc][vo];[m][sc]sidechaincompress=threshold=0.015:ratio=8:attack=30:release=400:makeup=1[md];\
[md][vo]amix=inputs=2:normalize=0,alimiter=limit=0.89[out]" -map "[out]" mix_vo.wav
ffmpeg -v error -y -i diwali01_video_only.mp4 -i mix_vo.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 192k \
  -shortest -movflags +faststart diwali01_final_voiceover.mp4
