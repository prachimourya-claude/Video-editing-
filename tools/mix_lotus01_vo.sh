#!/usr/bin/env bash
# Put the creator's voiceover on the Lotus reel (tools/render_lotus01.py, 24.5s). Voice only: music is added on Instagram.
# usage: tools/mix_lotus01_vo.sh <workdir>
#   <workdir>/lotus_video_only.mp4   silent render
#   <workdir>/vo/raw.mp3             voice note (AUD-20261025-WA0006), four lines with pauses
set -euo pipefail
cd "$1"
TOTAL=24.5
# source cut (start end) -> timeline start; times from the loudness envelope + Whisper word stamps
CUTS=(
  "0.25 1.85 0.25"     # New day, new product
  "3.05 5.65 3.25"     # Toh is baar humne banaya hai lotus stencil
  "9.15 12.05 16.60"   # Just fill in the colours and you're good to go
  "13.40 15.25 20.90"  # Order now for your Diwali
)
ffmpeg -v error -y -i vo/raw.mp3 -af "aresample=48000,pan=mono|c0=0.5*c0+0.5*c1,highpass=f=85,afftdn=nr=12:nf=-42,lowpass=f=12000,\
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
loudnorm=I=-16:TP=-1.5:LRA=7,aresample=48000,aformat=channel_layouts=stereo[out]" -map "[out]" lotus_vo_track.wav
ffmpeg -v error -y -i lotus_video_only.mp4 -i lotus_vo_track.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 192k \
  -shortest -movflags +faststart lotus_final_voice_only.mp4
