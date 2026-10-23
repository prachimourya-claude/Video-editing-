#!/usr/bin/env bash
# Mix Bali Diary 01 audio: AI voiceover (Piper hi_IN-priyamvada) + ducked music, original audio muted.
# usage: tools/mix_bali01.sh <workdir>   (workdir holds bali01_video_only.mp4, music/, tts/)
set -euo pipefail
cd "$1"
i=0
while IFS= read -r line; do
  i=$((i+1))
  echo "$line" | piper -m tts/hi_IN-priyamvada-medium.onnx --length-scale 0.86 --sentence-silence 0.12 -f tts/vo_$i.wav
done < "$(dirname "$0")/../bali-01-malaysia-airlines/voiceover_devanagari.txt"

ffmpeg -v error -y $(for i in 1 2 3 4 5 6 7; do echo -i tts/vo_$i.wav; done) -filter_complex "\
[0]adelay=150:all=1[v1];[1]adelay=7100:all=1[v2];[2]adelay=16000:all=1[v3];[3]adelay=26000:all=1[v4];\
[4]adelay=31800:all=1[v5];[5]adelay=37300:all=1[v6];[6]adelay=47600:all=1[v7];\
[v1][v2][v3][v4][v5][v6][v7]amix=inputs=7:normalize=0,aresample=48000,highpass=f=90,\
equalizer=f=200:t=q:w=1:g=2,equalizer=f=4500:t=q:w=1.5:g=2,acompressor=threshold=-20dB:ratio=3:attack=5:release=120,\
apad,atrim=duration=52,loudnorm=I=-16:TP=-1.5:LRA=7,aresample=48000,aformat=channel_layouts=stereo[out]" -map "[out]" vo_track.wav

ffmpeg -v error -y -i "music/Easy Lemon.mp3" -i vo_track.wav -filter_complex "\
[0]atrim=duration=52,asetpts=PTS-STARTPTS,aresample=48000,aformat=channel_layouts=stereo,volume=-10dB,afade=t=in:d=0.6,afade=t=out:st=49.5:d=2.5[m];\
[1]asplit[sc][vo];[m][sc]sidechaincompress=threshold=0.015:ratio=8:attack=30:release=450:makeup=1[md];\
[md][vo]amix=inputs=2:normalize=0,alimiter=limit=0.89[out]" -map "[out]" mix_vo.wav
ffmpeg -v error -y -i "music/Easy Lemon.mp3" -af "atrim=duration=52,asetpts=PTS-STARTPTS,aresample=48000,volume=-3dB,afade=t=in:d=0.6,afade=t=out:st=49.5:d=2.5,alimiter=limit=0.89" mix_music.wav

for v in ai_voice:mix_vo music_only:mix_music; do
  ffmpeg -v error -y -i bali01_video_only.mp4 -i "${v#*:}.wav" -map 0:v -map 1:a -c:v copy -c:a aac -b:a 192k \
    -shortest -movflags +faststart "bali01_edit_v2_${v%%:*}.mp4"
done
