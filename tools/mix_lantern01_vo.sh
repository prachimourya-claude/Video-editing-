#!/usr/bin/env bash
# Put the creator's voiceover on the Star Lantern reel (tools/render_lantern01.py, 32.5s). Voice only: music is added on Instagram.
# usage: tools/mix_lantern01_vo.sh <workdir>
#   <workdir>/lantern_video_only.mp4   silent render
#   <workdir>/vo/raw.mp3               voice note (AUD-20261026-WA0005), eight lines with pauses
set -euo pipefail
cd "$1"
TOTAL=32.5
# source cut (start end) -> reel start; times from the loudness envelope + Whisper
CUTS=(
  "0.50 2.20 0.20"     # Another day, another product
  "2.90 7.50 2.20"     # Diwali aa rahi hai, toh humne socha kuch lantern ya tea-light holder jaisa banate hain
  "8.50 9.95 6.80"     # Toh humne ye 3D print kiya
  "11.00 14.50 8.30"   # Upar star pattern aur neeche terracotta look wala base
  "14.90 16.25 12.10"  # Kaafi beautiful lag raha hai
  "17.85 21.15 16.00"  # Tea light ko bas base se on karo aur aapka lantern ready
  "22.45 25.95 19.50"  # Aur battery khatam ho jaye, toh tea light badal bhi sakte ho
  "32.60 34.40 30.10"  # DM to order now
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
loudnorm=I=-16:TP=-1.5:LRA=7,aresample=48000,aformat=channel_layouts=stereo[out]" -map "[out]" lantern_vo_track.wav
ffmpeg -v error -y -i lantern_video_only.mp4 -i lantern_vo_track.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 192k \
  -shortest -movflags +faststart lantern_final_voice_only.mp4
