ffmpeg -ss 6 -t 3 -i 0bf116b3-bc8a-455f-81a4-a438aa6e1b73.mp4 -vf "fps=25,scale=320:-1:flags=lanczos,split[s0][s1];[s0]palettegen[p];[s1][p]paletteuse" -loop 0 output.gif
