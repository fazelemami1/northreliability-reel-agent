# NorthReliability reel brand kit, v1

Decided by Fazel Emami on Nov 11, 2026. Every reel uses these values. `scripts/build_reel.py` holds the same numbers in code; if you change one here, change it there too, and bump the version.

## Colour palette (post 17 palette)

| Token | Hex | Use |
|---|---|---|
| Navy | `#0F2547` | Backgrounds, text panels over footage |
| Navy dark | `#0A192F` | Edges of navy backgrounds |
| Gold | `#FFC107` | Category pill, 2 to 3 key words per headline, keyword boxes |
| Gold bar | `#D4AF37` | Divider bar above every headline, gear of the NR mark |
| White | `#FFFFFF` | Headlines |
| Body | `#E8EDF3` | Body text |
| Muted | `#AABACE` | Small notes |
| Status red / amber / green | `#E5484D` / `#F5A524` / `#30A46C` | Only for red/amber/green status chips |

## Type

- Inter (official release, v4.0). Headline 72 px ExtraBold, body 42 px Medium.
- Pill: Inter ExtraBold 28 px, letter-spaced, navy on gold.
- CTA keyword: Inter Black 132 px, navy on a gold box.
- Signature line: Inter ExtraBold Italic 66 px, gold.

## Layout (phone-safe, from Fazel's phone screenshot, Nov 10, 2026)

- Canvas 1080 × 1920, 30 fps.
- Keep all text inside x 150 to 870 and y 340 to 1300. Instagram covers the top bar, the right-hand icons and the account row and caption at the bottom.
- No logo, no @handle and no slide counter on content slides. Instagram already shows the account.
- Slide 1 carries the gold series pill. Every slide has the gold bar above the headline.
- Footage slides: the text sits on a navy panel (88% opacity) at the top of the safe area, with a soft dark band behind it.
- Text-only slides: navy background, content centred vertically in the safe area.
- End card (last slide): the NR mark (gold gear, white arrow) and "Find it before it fails." Nothing else.

## Voice

| Setting | Value |
|---|---|
| Service | ElevenLabs, through the Composio `elevenlabs` connection |
| Voice | Roger, voice ID `CwhRBWXzGAHq8TQ4Fs17` |
| Model | `eleven_multilingual_v2` |
| Voice settings | stability 0.5, similarity boost 0.75, style 0, speaker boost on |
| Seed | 42 |
| Output | MP3 44.1 kHz 128 kbps |
| Clips | One clip per slide (`beat01.mp3`, `beat02.mp3` ...). The end card has its own clip with the signature line. |

Pace: Roger speaks about 2.95 words per second with these settings. Plan **140 to 160 words** for a reel of about 52 to 60 seconds.

The API key needs the **Text to Speech** permission (and **Voices: Read** to list voices).

## Timing

- 0.35 s before the first word.
- 0.55 s between slides. The slide changes in the middle of that pause.
- 1.4 s after the last word, on the end card.
- Never longer than 90 s.

## Music

Original instrumental bed from `scripts/make_music.py` (no lyrics, no samples), mixed 18 dB under the voice. Final loudness about −14 LUFS.

## Footage

- Real factory footage from Mixkit (free licence, no attribution needed). Use the 1080p file when Mixkit offers it, otherwise 720p.
- Prefer footage of the real asset or line being discussed (Fazel's rule, Nov 3, 2026). Use Fazel's own photos or clips whenever he sends them.
- Say at Gate 2 that the footage is stock, not his plant.

## Caption

1. Hook line (what shows before "... more"): a concrete machine or problem, never our name.
2. 3 to 5 short teaching lines.
3. Source line when a fact comes from a standard, a regulator or the handbook.
4. One ask (a comment keyword, or the handbook link in bio).
5. "Find it before it fails."
6. Hashtags: 3 topic hashtags plus **#NorthReliability** (always).

Plain, professional English. No em dashes. No invented numbers or results. Book case stories are labelled as examples.

## Names

- Files: `NR_YYYY-MM-DD_REEL_Series_Topic_vN` (date = planned post date).
- Drive folder: `North Reliability / Instagram / Sprint N (dates) / Post NN - YYYY-MM-DD - REEL - topic`.
- Lead magnets: `NR_YYYY-MM-DD_PDF_Topic_vN.pdf`, in the same post folder, shared as "anyone with the link can view".
