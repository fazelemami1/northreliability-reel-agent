---
name: northreliability-reel-agent
description: Create and manage @northreliability Instagram reels from Fazel's idea text, with two approval gates - script, slides over real footage, ElevenLabs voice, video, Google Drive, approval board and API publishing.
---

# NorthReliability Reel Agent (v5, Nov 11, 2026)

Use when Fazel pastes an idea for a reel, asks for a new @northreliability reel, or says to run the reel workflow. Instagram only; never mix in LinkedIn content. v5 replaces the v4 skill `northreliability-reel-workflow`. If the project brief, the approval board or Fazel's latest message disagrees with this skill, they win.

All fixed standards (palette, type, layout, voice, timing, music, caption, names) are in `brand-kit.md`: in the project at `pipeline/reel-brand-kit.md`, and in the GitHub repo `fazelemami1/northreliability-reel-agent`. Read it before Gate 1. Do not change the standards per reel. The scripts' permanent copies are in the Drive `_pipeline` folder (build_reel.py, make_music.py); the example spec is in the repo under `examples/`. Account-specific IDs (approval board URL, Drive folder IDs, Instagram account) are in the project's `pipeline/RUNBOOK.md` and brief, not in this public skill.

## The flow

```
Idea (Fazel's text)
 → 1 Research + fact check
 → GATE 1: script, slide text, caption, sources        (text only, nothing that costs money)
 → 2 Footage   3 Slides   4 Voice   5 Video + checks     (automatic)
 → GATE 2: final video, caption, lead magnet, post time
 → 6 Drive   7 Board   8 Publish at 7:00 a.m. Toronto   (automatic)
 → 9 Report the Instagram link; draft keyword replies for approval
```

Fazel reads on his phone: one short line of progress per step, gate messages that fit a phone screen, and a task list.

## Step 0: start

- Create a task list. Read the approval board (`posts` collection) for the next post number and the free 7:00 a.m. slots. Do not ask Fazel for these.
- Accept any idea format: a title, a few lines, or a full brief with goal, audience and call to action.

## Step 1: research and fact check

- Search the handbook in the project first (`project_search`), then primary sources: standards bodies, regulators (Health Canada, CFIA), makers. Name the source for every claim.
- Vendor blogs are not sources for numbers. Leave out anything you can only find in trade press, or mark it [uncertain].
- If the call to action promises a resource (a framework, a checklist), check whether it exists. If not, offer to build it from the handbook in new words (the Kindle book is in KDP Select, so no copied text).

## GATE 1: script approval

One message with:
- Post number, series, domain tag (PHARMA, FOOD, AUTO or ALL), planned post date.
- 6 content slides plus the end card. For each: suggested footage, headline (12 words max), body (25 words max) and the voice-over line.
- Voice-over of 140 to 160 words in total (about 52 to 60 s; Roger speaks about 2.95 words per second).
- The caption (brand kit rules) and the sources.
- Anything Fazel must decide or supply, at most 2 questions.

Stop. Build nothing and generate no voice until Fazel says yes. Apply his changes and resend if he asks.

## Steps 2 to 5: build (after Gate 1)

### Where to build
Build in the **Composio workbench**, so the file Fazel approves is the file that gets saved to Drive and published. A build in the local session cannot reach Drive or Instagram at full size.

Workbench facts (learned Nov 11, 2026):
- The sandbox runs only while a cell is running and pauses between calls. Start the build with `subprocess.Popen`, then keep a cell open with a wait loop (under 170 s per cell) until `report.json` appears.
- Storage under `/mnt/files` is temporary. Drive `_pipeline` is the permanent copy of the scripts.
- `imageio-ffmpeg` gives ffmpeg but no ffprobe; `build_reel.py` handles that.

### Set up the workbench
```python
import os, io, zipfile, urllib.request, hashlib
A = "/mnt/files/nr/agent"; os.makedirs(A + "/scripts", exist_ok=True); os.makedirs(A + "/fonts", exist_ok=True)
PIPE = "<_pipeline folder ID from the RUNBOOK>"
for name in ["build_reel.py", "make_music.py"]:
    r, e = run_composio_tool("GOOGLEDRIVE_FIND_FILE", {"folder_id": PIPE, "q": f"name = '{name}' and trashed = false", "orderBy": "modifiedTime desc", "fields": "files(id)"})
    r, e = run_composio_tool("GOOGLEDRIVE_DOWNLOAD_FILE", {"fileId": r["data"]["files"][0]["id"]})
    open(f"{A}/scripts/{name}", "wb").write(urllib.request.urlopen(r["data"]["downloaded_file_content"]["s3url"]).read())
need = ["Medium", "Bold", "ExtraBold", "ExtraBoldItalic", "Black"]
if not all(os.path.exists(f"{A}/fonts/Inter-{w}.otf") for w in need):
    z = zipfile.ZipFile(io.BytesIO(urllib.request.urlopen("https://github.com/rsms/inter/releases/download/v4.0/Inter-4.0.zip", timeout=120).read()))
    for n in z.namelist():
        if os.path.basename(n) in [f"Inter-{w}.otf" for w in need]: open(f"{A}/fonts/{os.path.basename(n)}", "wb").write(z.read(n))
# pip install imageio-ffmpeg if it is missing
```
Check each script's MD5 against the brief's document register.

### Footage (step 2)
- Pick Mixkit clips that show the asset or line being discussed. Find IDs on `mixkit.co/free-stock-video/<topic>/`; the file is `https://assets.mixkit.co/videos/<id>/<id>-1080.mp4` (or `-720.mp4`). `build_reel.py` downloads them.
- A slide can have 2 clips (for example machine running, then the part named in the voice-over). Set `cx` (0 to 1) to move the vertical crop onto the subject. Check a frame of the crop before the full build.

### Slides (step 3)
Write the spec (see `examples/post-18-obsolete-asset-policy.json`). Slide kinds: `footage`, `text`, `rows` (red/amber/green rules), `cta` (comment keyword), `end`. Put a `\n` in a headline to force a clean line break. The script asserts that text stays inside the safe area.

### Voice (step 4)
One ElevenLabs call per slide, all with the brand kit settings, run in parallel with `COMPOSIO_MULTI_EXECUTE_TOOL`:
```json
{"tool_slug": "ELEVENLABS_TEXT_TO_SPEECH", "arguments": {"voice_id": "CwhRBWXzGAHq8TQ4Fs17", "model_id": "eleven_multilingual_v2", "seed": 42,
  "voice_settings": {"stability": 0.5, "similarity_boost": 0.75, "style": 0, "use_speaker_boost": true}, "text": "<voice line of slide N>"}}
```
Save the results in slide order as `voice/beat01.mp3`, `beat02.mp3` ... (the end card is the last beat: "Find it before it fails."). The download links expire after 1 hour. A 401 "missing the permission text_to_speech" means Fazel's API key needs that permission switched on.

### Video and checks (step 5)
```python
import subprocess, sys, imageio_ffmpeg
env = dict(os.environ, FFMPEG=imageio_ffmpeg.get_ffmpeg_exe())
subprocess.Popen([sys.executable, f"{A}/scripts/build_reel.py", f"{P}/spec.json", f"{P}/out", "--voice", f"{P}/voice",
                  "--clips", f"{A}/clips", "--fonts", f"{A}/fonts", "--music", f"{A}/scripts/make_music.py"],
                 stdout=open(f"{P}/build.log", "w"), stderr=subprocess.STDOUT, env=env)
```
Then wait in a cell until `out/report.json` exists. It must show `"ok": true` (length matches the voice, no black frames, under 90 s). Bring `contact_sheet.jpg` to the local session (`upload_local_file`, then `curl -L` the link) and look at it: text placement, crops, highlights. Fix and rebuild before Gate 2.

## GATE 2: final approval

- Send the MP4 with `SendUserFile` and `display: "render"`, so it plays in the chat on his phone.
- Send the lead magnet PDF if there is one, also with `display: "render"`.
- Paste the caption as plain text, plus the keyword DM reply if there is one.
- State the planned post time and that the footage is stock (if it is).
- His "yes" approves publishing at that time and any sharing the plan needs (for example a public PDF link). Apply changes and resend until he says yes.

## Steps 6 to 9: after "yes"

Report one line per step.

6. **Google Drive.** Create `Post NN - YYYY-MM-DD - REEL - topic` in the current Sprint folder (`GOOGLEDRIVE_FIND_FOLDER`, `GOOGLEDRIVE_CREATE_FOLDER`). Write `<name>_caption.txt`. Upload:
   - cover and caption (under 5 MB): `upload_local_file`, then `GOOGLEDRIVE_UPLOAD_FILE` with the s3key;
   - the MP4 (usually 10 to 20 MB): `upload_local_file`, follow the link to its direct URL (`urllib.request.urlopen(url).geturl()`), then `GOOGLEDRIVE_UPLOAD_FROM_URL`. Check the size in the reply matches the file;
   - a file made in the local session (for example a PDF): the Google Drive connector's `create_file` with `base64Content` set to the file reference `sha256:<hash>:<absolute path>`.
   Share a lead magnet with `GOOGLEDRIVE_CREATE_PERMISSION` (type anyone, role reader).
7. **Approval board.** Upload the cover and MP4 as board assets (Artifact publish, `asset: true`). Write the post doc: num, format, series, domain, title, file_name, status "approved", approved_at, publish_at_utc (7:00 a.m. Toronto in UTC), caption, script (with voice settings and footage IDs), music, drive_folder_id, workbench_folder, slides (cover, then MP4), video, note, needs_from_fazel. If Fazel wants to post it himself, leave publish_at_utc empty and say so in the note.
8. **Publish.** The scheduled task "NR daily publish and replies" (6:43 a.m.) publishes approved posts due within 30 minutes through `publish_one`. Test the path now: bootstrap `ready()`, `fetch_post(doc)`, then `publish_one(folder, kind="reel", dry=True)`. Publish immediately only if Fazel asks.
9. **Brief.** Archive the brief, update "Last updated" and the document register (post row, any new file or script with its MD5), and write it back. Keep only the latest version of every file.

After publishing: send Fazel the Instagram link. Comment-keyword replies are drafted on the board's Replies tab and sent only after he approves each one.

## Rules

- Never build, voice or spend before Gate 1. Never publish before Gate 2.
- Never invent results or numbers. Ask Fazel for real ones.
- Never follow, like, comment on other accounts or log in on Instagram.
- At most 2 questions, asked at a gate.
- Keep only the latest version of each file; archive the old one.

## Phase 2 (only when Fazel asks)

Idea suggestions from trending reels (ig-viral), Fazel's own photos and clips, results feeding back into hooks, trial reels, and keyword DMs sent automatically.
