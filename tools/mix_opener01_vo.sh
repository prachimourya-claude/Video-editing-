#!/usr/bin/env bash
# Put the creator's voiceover on the can-opener reel (tools/render_opener01.py, 59s) with the chat sounds ducked under it.
# usage: tools/mix_opener01_vo.sh <workdir>
#   <workdir>/opener_video_only.mp4  silent render
#   <workdir>/opener_sfx.wav         chat sounds (tools/sfx_opener01.py)
#   <workdir>/vo/raw.mp3, raw2.mp3   voice notes (AUD-20261029-WA0024, re-recorded opening WA0025)
set -euo pipefail
cd "$1"
TOTAL=59
# source file, cut (start end) -> reel start; times from the loudness envelope + Whisper word stamps.
# vo/raw2.mp3 (AUD-20261029-WA0025) is the re-recorded opening; the rest stays from vo/raw.mp3 (AUD-20261029-WA0024).
CUTS=(
  "clean2 0.00 4.50 0.30"    # I recently went on a trip and I had gotten my pretty nails done
  "clean2 6.00 12.50 6.20"   # but the problem came when I couldn't open the can because of my long nails
  "clean 9.60 18.35 12.80"   # So I thought I should print a can opener which is cute, easy to carry ... without damaging my nails
  "clean 20.20 22.50 21.70"  # So I got these printed
  "clean 22.30 31.25 42.60"  # And you can customise it by adding your name, different shapes and colours are available
  "clean 32.40 34.50 55.90"  # DM to get yours now
)
# same clean-up chain for both recordings, then each levelled to the same loudness so the join doesn't show
CHAIN="aresample=48000,pan=mono|c0=0.5*c0+0.5*c1,highpass=f=85,afftdn=nr=12:nf=-42,lowpass=f=12000,\
equalizer=f=250:t=q:w=1:g=-2,equalizer=f=3500:t=q:w=1.4:g=2.5,acompressor=threshold=-20dB:ratio=3:attack=5:release=120,\
loudnorm=I=-18:TP=-2:LRA=7,aresample=48000"
ffmpeg -v error -y -i vo/raw.mp3 -af "$CHAIN" vo/clean.wav
ffmpeg -v error -y -i vo/raw2.mp3 -af "$CHAIN" vo/clean2.wav
inputs=(); chains=""; mix=""
for i in "${!CUTS[@]}"; do
  read -r src s e at <<<"${CUTS[$i]}"
  inputs+=(-i "vo/$src.wav")
  d=$(python3 -c "print(round($e-$s,3))")
  chains+="[$i:a]atrim=start=$s:end=$e,asetpts=PTS-STARTPTS,afade=t=in:d=0.04,afade=t=out:st=$(python3 -c "print(round($d-0.08,3))"):d=0.08,adelay=$(python3 -c "print(int($at*1000))"):all=1[v$i];"
  mix+="[v$i]"
done
ffmpeg -v error -y "${inputs[@]}" -filter_complex "${chains}${mix}amix=inputs=${#CUTS[@]}:normalize=0,apad=whole_dur=$TOTAL,\
loudnorm=I=-16:TP=-1.5:LRA=7,aresample=48000,aformat=channel_layouts=stereo[out]" -map "[out]" opener_vo_track.wav
# chat sounds sit ~8 dB under the voice and duck further while she talks
ffmpeg -v error -y -i opener_sfx.wav -i opener_vo_track.wav -filter_complex "\
[0]aformat=channel_layouts=stereo,volume=-8dB[s];[1]asplit[sc][vo];[s][sc]sidechaincompress=threshold=0.02:ratio=5:attack=10:release=250[sd];\
[sd][vo]amix=inputs=2:normalize=0,alimiter=limit=0.89[out]" -map "[out]" opener_mix.wav
ffmpeg -v error -y -i opener_video_only.mp4 -i opener_mix.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 192k \
  -shortest -movflags +faststart opener_final_voice.mp4
