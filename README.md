# NorthReliability Reel Agent

An AI agent skill that turns a short idea into a finished 60-second Instagram reel for **[@northreliability](https://www.instagram.com/northreliability/)**, a maintenance and reliability engineering account for pharmaceutical, food and automotive plants.

You paste an idea. The agent researches it, writes the script and gets your approval. It then builds branded slides over real factory footage, generates the voice-over, assembles the video and checks it. After your final approval it saves everything to Google Drive and publishes through the Instagram API.

Built by Fazel Emami, North Reliability Consulting (Newmarket, Ontario). *Find it before it fails.*

## How it works

```
Idea → research → GATE 1 (script) → footage, slides, voice, video → GATE 2 (final) → Drive → board → publish
```

- **Two approval gates.** Nothing that costs money happens before the script is approved. Nothing is published before the final video is approved.
- **One voice clip per slide.** Each slide changes in the pause between two clips, so the voice and the on-screen text can't drift apart.
- **One standard every time.** The same voice, pace, palette, layout, end card and hashtag rules, all in [`brand-kit.md`](brand-kit.md).
- **Phone-safe layout.** Text stays clear of Instagram's buttons, account row and caption.

## What's in this repository

```text
northreliability-reel-agent/
├── SKILL.md                     # the agent skill: workflow, gates, build and publish steps
├── requirements.txt             # Python packages for the scripts
├── brand-kit.md                 # fixed standards: palette, type, layout, voice, timing, caption
├── scripts/
│   ├── build_reel.py            # builds the reel from a spec + voice clips (Pillow, numpy, ffmpeg)
│   └── make_music.py            # original instrumental bed, no lyrics (numpy, scipy)
├── examples/
│   └── post-18-obsolete-asset-policy.json   # the spec of the first reel built with the agent
└── studio/
    └── NorthReliability_Safety_Reel_Studio.html   # browser preview for drafting and timing (not production)
```

## Build a reel yourself

```bash
pip install -r requirements.txt
# needs ffmpeg on PATH and the Inter fonts (https://github.com/rsms/inter)
python3 scripts/build_reel.py examples/post-18-obsolete-asset-policy.json out --voice voice/ --fonts /path/to/inter/otf
# no voice yet? check the layout with estimated timing:
python3 scripts/build_reel.py examples/post-18-obsolete-asset-policy.json out --preview --fonts /path/to/inter/otf
```

`--voice` is a folder with `beat01.mp3`, `beat02.mp3` ... one clip per slide. The output folder gets the MP4, a cover image, a contact sheet and `report.json` (length, slide cut times, black-frame check).

## Services the full agent uses

- **ElevenLabs** for the voice. The API key needs the Text to Speech permission.
- **Composio** to reach ElevenLabs, Google Drive and the Instagram Graph API from a Python workbench.
- **Mixkit** for free factory footage (free licence, no attribution needed).

Account IDs, folder IDs and the approval board are kept out of this public repository.

## The HTML studio

The HTML studio in `studio/` previews a script in the browser with its built-in voice. Version 2 fixed the voice/text timing: each slide now waits for its voice to finish. It's useful for drafting and checking timing. Production reels are built with `scripts/build_reel.py` and the ElevenLabs voice.

## Licence

MIT. See [LICENSE](LICENSE).
