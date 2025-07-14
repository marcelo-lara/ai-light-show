# Expected output

- sample song: /songs/born_slippy.mp3
- genre: EDM

## Drums track identified sections

| start  | end    | section | description                                     |
| ------ | ------ | ------- | ----------------------------------------------- |
| 0s     | 27.5s  |       0 | silence
| 27.5s  | 34.2s  |       1 | snares only
| 34.2s  | 55.2s  |       2 | kick triplet with snares
| 55.2s  | 81.2s  |       3 | kick triplet with snares and closed hihat
| 81.2s  | 97.1s  |       4 | kick triplet with snares, plus a tom pattern
| 97.1s  | 117.1s |       5 | tom plus hihat pattern
| 102.3s | 120s   |       6 | one beat kicks, one beat closed hihat
| 120.3s | 122s   |       7 | closed hihat
| 122s   | 130s   |       8 | a tom+hihat pattern


## Instructions
- don't limit to the current song, use it as a reference to adjust the algorithm.
- compare the output with the provided example to determine the best algorithm.
- if you think there's a better library to the goal, just try it.
- keep the return schema (backwards compatible)
- it is important that every match is aligned with the perceptual start of the sound.
- cluster length doesn't need to be the same lengt, but limit the maximun to 4 beats
- use small segments (at least 0.125 beat)
- use only this command to test results "cd /home/darkangel/ai-light-show && clear && python -m backend.ai.pattern_finder"