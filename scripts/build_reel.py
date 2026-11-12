#!/usr/bin/env python3
"""build_reel.py - NorthReliability reel builder (brand kit v1, Nov 2026).

Builds a 1080x1920 Instagram reel from a spec: branded slides over real factory
footage (Mixkit free licence) or plain navy, one voice clip per slide, an original
instrumental bed 18 dB under the voice, and the NR end card.

Why one voice clip per slide: the slide changes are placed in the pause between
two clips, so voice and text can never drift apart (the timing bug found in the
old HTML studio, Nov 11, 2026).

Usage:
    python3 build_reel.py SPEC.json OUT_DIR [--voice DIR] [--clips DIR] [--fonts DIR]
                          [--music make_music.py] [--preview]

  --voice DIR   folder with beat01.mp3, beat02.mp3 ... one per slide, in order
                (ElevenLabs output). Leading and trailing silence is trimmed.
  --preview     no voice yet: slide lengths are estimated from the word count
                and the track is music only. For layout checks.
Outputs in OUT_DIR: <name>.mp4, <name>_cover.jpg, contact_sheet.jpg, report.json,
and _work/ (slide PNGs and segments).
Needs: Python 3, Pillow, numpy, scipy (music), ffmpeg on PATH (or env FFMPEG; ffprobe is
optional), Inter OTF fonts (Medium, Bold, ExtraBold, ExtraBoldItalic, Black), and network
access to assets.mixkit.co for footage not yet in --clips.
Brand values below match brand-kit.md v1.
"""
import argparse, json, math, os, shutil, subprocess, sys, urllib.request, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFont

# ----------------------------------------------------------------- brand kit v1
W, H, FPS = 1080, 1920, 30
NAVY, NAVY_DARK = (15, 37, 71), (10, 25, 47)          # #0F2547, #0A192F
GOLD, GOLD_BAR = (255, 193, 7), (212, 175, 55)        # #FFC107 key words/pills, #D4AF37 bar/gear
WHITE, BODY, MUTED = (255, 255, 255), (232, 237, 243), (170, 186, 206)
STATUS = {"red": (229, 72, 77), "amber": (245, 165, 36), "green": (48, 164, 108)}
# Phone-safe area (Fazel's screenshot, Nov 10): sides are cropped ~60 px, Instagram
# icons sit on the right, account row and caption at the bottom.
LEFT, RIGHT, TOP, BOTTOM = 150, W - 210, 340, 1300
HEAD_PX, BODY_PX = 72, 42
LEAD, GAP, TAIL = 0.35, 0.55, 1.4                     # seconds: before first word, between slides, after last
EST_WPS = 2.95                                         # preview only: Roger, words per second (measured, post 18)
MUSIC_UNDER_DB = 18.0

FF = os.environ.get("FFMPEG", "ffmpeg"); FP = os.environ.get("FFPROBE", "ffprobe")
FONTS = {}


def font(weight, size):
    return ImageFont.truetype(FONTS[weight], size)


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode:
        raise RuntimeError(" ".join(map(str, cmd[:6])) + " ...\n" + r.stderr[-1500:])
    return r


def probe_dur(path):
    """Duration in seconds. Uses ffprobe if present, else parses 'ffmpeg -i' (imageio-ffmpeg has no ffprobe)."""
    if shutil.which(FP):
        return float(run([FP, "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path]).stdout.strip())
    err = subprocess.run([FF, "-hide_banner", "-i", path], capture_output=True, text=True).stderr
    hh, mm, ss = err.split("Duration:")[1].split(",")[0].strip().split(":")
    return int(hh) * 3600 + int(mm) * 60 + float(ss)


# ------------------------------------------------------------------ the NR mark
def mark(size):
    S = 1080; im = Image.new("RGBA", (S, S), NAVY + (255,)); d = ImageDraw.Draw(im)
    cx = cy = 540; rot = math.radians(-7); pts = []
    for i in range(12):
        a = rot + i * 2 * math.pi / 12
        for ang, r in [(a - math.radians(15), 372), (a - math.radians(10.5), 372), (a - math.radians(6.2), 432),
                       (a + math.radians(6.2), 432), (a + math.radians(10.5), 372), (a + math.radians(15), 372)]:
            pts.append((cx + r * math.sin(ang), cy - r * math.cos(ang)))
    d.polygon(pts, fill=GOLD_BAR); d.ellipse((220, 220, 860, 860), fill=NAVY)
    d.polygon([(540, 300), (365, 720), (540, 630), (715, 720)], fill=WHITE)
    m = Image.new("L", (S, S), 0); ImageDraw.Draw(m).ellipse((0, 0, S - 1, S - 1), fill=255); im.putalpha(m)
    return im.resize((size, size), Image.LANCZOS)


# ------------------------------------------------------------------- text tools
def _key(w):
    return w.lower().strip(".,:;!?\"'()")


def wrap_words(d, text, f, width):
    """Word wrap; a newline in the text forces a break (for deliberate headline breaks)."""
    lines = []
    for para in text.split("\n"):
        cur = []
        for w in para.split():
            t = " ".join(cur + [w])
            if cur and d.textlength(t, font=f) > width:
                lines.append(cur); cur = [w]
            else:
                cur.append(w)
        if cur: lines.append(cur)
    return lines


def draw_words(d, x, y, words, f, color, hl=(), hl_color=GOLD):
    hl = {_key(h) for h in hl}; sp = d.textlength(" ", font=f)
    for w in words:
        d.text((x, y), w, font=f, fill=hl_color if _key(w) in hl else color)
        x += d.textlength(w, font=f) + sp


def spaced(d, xy, text, f, fill, track):
    x, y = xy
    for ch in text:
        d.text((x, y), ch, font=f, fill=fill); x += d.textlength(ch, font=f) + track
    return x


def pill(d, x, y, text):
    f = font("ExtraBold", 28); tw = sum(d.textlength(c, font=f) + 3 for c in text) - 3
    d.rounded_rectangle((x, y, x + tw + 40, y + 52), 8, fill=GOLD)
    spaced(d, (x + 20, y + 10), text, f, NAVY, 3)
    return y + 52


def navy_bg():
    """Navy with darker edges (#0F2547 centre to #0A192F)."""
    yy, xx = np.mgrid[0:H, 0:W]
    r = np.sqrt(((xx - W / 2) / (W * 0.75)) ** 2 + ((yy - H * 0.42) / (H * 0.62)) ** 2).clip(0, 1)
    a = np.array(NAVY, float); b = np.array(NAVY_DARK, float)
    img = (a[None, None, :] * (1 - r[..., None]) + b[None, None, :] * r[..., None]).astype(np.uint8)
    return Image.fromarray(img, "RGB")


# ----------------------------------------------------------------- slide images
def text_block(d, x, y, s, width):
    """Pill (optional), gold bar, headline with gold key words, body. Returns bottom y."""
    if s.get("pill"):
        y = pill(d, x, y, s["pill"].upper()) + 30
    d.rectangle((x, y, x + 96, y + 10), fill=GOLD_BAR); y += 10 + 34
    fh = font("ExtraBold", HEAD_PX); lh = int(HEAD_PX * 1.14)
    for ln in wrap_words(d, s["headline"], fh, width):
        draw_words(d, x, y, ln, fh, WHITE, s.get("hl", ())); y += lh
    if s.get("body"):
        y += 26; fb = font("Medium", BODY_PX); lb = int(BODY_PX * 1.38)
        for ln in wrap_words(d, s["body"], fb, width):
            draw_words(d, x, y, ln, fb, BODY, s.get("body_hl", ())); y += lb
    return y


def measure(s, width):
    im = Image.new("RGB", (W, 200)); d = ImageDraw.Draw(im)
    return text_block(d, 0, 0, s, width)


def overlay_footage(s, path):
    """Transparent overlay for a footage slide: navy panel inside the safe area."""
    width = RIGHT - LEFT; h = measure(s, width)
    y0 = 400; pad = 44
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    # soft dark band behind the panel so busy footage never fights the text
    band = Image.new("L", (1, H), 0)
    for yy in range(H):
        dist = abs(yy - (y0 + h / 2)) / (h / 2 + 260)
        band.putpixel((0, yy), int(110 * max(0.0, 1 - dist) ** 1.5))
    im.paste((0, 0, 0, 255), (0, 0, W, H), band.resize((W, H)))
    d.rounded_rectangle((LEFT - pad, y0 - pad, RIGHT + pad - 10, y0 + h + pad), 26, fill=NAVY + (226,))
    text_block(d, LEFT, y0, s, width)
    assert y0 + h + pad <= BOTTOM, f"text runs below y={BOTTOM}: {s['headline']}"
    im.save(path)


def full_text(s, path):
    width = RIGHT - LEFT; im = navy_bg(); d = ImageDraw.Draw(im)
    if s["kind"] == "rows":
        f_head = font("ExtraBold", HEAD_PX); lh = int(HEAD_PX * 1.14)
        rows_h = len(s["rows"]) * 168; head_lines = wrap_words(d, s["headline"], f_head, width)
        total = 44 + len(head_lines) * lh + (24 + 50 if s.get("note") else 0) + 50 + rows_h
        y = TOP + (BOTTOM - TOP - total) // 2
        d.rectangle((LEFT, y, LEFT + 96, y + 10), fill=GOLD_BAR); y += 44
        for ln in head_lines:
            draw_words(d, LEFT, y, ln, f_head, WHITE, s.get("hl", ())); y += lh
        if s.get("note"):
            y += 24; d.text((LEFT, y), s["note"], font=font("Medium", 32), fill=MUTED); y += 50
        y += 50
        fl, ft = font("ExtraBold", 32), font("Bold", 54)
        for color, label, text in s["rows"]:
            c = STATUS[color]
            lw = sum(d.textlength(ch, font=fl) + 2 for ch in label) - 2
            d.rounded_rectangle((LEFT, y, LEFT + lw + 40, y + 54), 27, fill=c)
            spaced(d, (LEFT + 20, y + 10), label, fl, NAVY_DARK, 2)
            d.text((LEFT, y + 68), text, font=ft, fill=WHITE)
            y += 168
        assert y <= BOTTOM + 40, "rows run below the safe area"
    elif s["kind"] == "cta":
        fh = font("ExtraBold", 84); fk = font("Black", 132); fb = font("Medium", BODY_PX)
        body = wrap_words(d, s["body"], fb, width)
        total = 44 + 100 + 36 + 170 + 40 + len(body) * int(BODY_PX * 1.38)
        y = TOP + (BOTTOM - TOP - total) // 2
        d.rectangle((LEFT, y, LEFT + 96, y + 10), fill=GOLD_BAR); y += 44
        d.text((LEFT, y), s["headline"], font=fh, fill=WHITE); y += 100 + 36
        kw = s["keyword"]; kwid = d.textlength(kw, font=fk)
        d.rounded_rectangle((LEFT, y, LEFT + kwid + 64, y + 170), 22, fill=GOLD)
        d.text((LEFT + 32, y + 85), kw, font=fk, fill=NAVY, anchor="lm"); y += 170 + 40
        for ln in body:
            draw_words(d, LEFT, y, ln, fb, BODY, s.get("body_hl", ())); y += int(BODY_PX * 1.38)
        assert y <= BOTTOM, "CTA runs below the safe area"
    elif s["kind"] == "result":
        # Proof slide: label, a large "before -> after" number, one short line.
        fl, fn, fb = font("Bold", 40), font("Black", 230), font("Medium", BODY_PX)
        before, after = s["before"], s["after"]; arrow = " → "
        wb, wa, wr = d.textlength(before, font=fn), d.textlength(after, font=fn), d.textlength(arrow, font=fn)
        assert wb + wa + wr <= width, "result numbers too wide for the safe area"
        body = wrap_words(d, s.get("body", ""), fb, width) if s.get("body") else []
        total = 44 + 52 + 20 + 250 + 20 + len(body) * int(BODY_PX * 1.38)
        y = TOP + (BOTTOM - TOP - total) // 2
        d.rectangle((LEFT, y, LEFT + 96, y + 10), fill=GOLD_BAR); y += 44
        d.text((LEFT, y), s.get("label", ""), font=fl, fill=BODY); y += 52 + 20
        x = LEFT
        d.text((x, y), before, font=fn, fill=WHITE); x += wb
        d.text((x, y), arrow, font=fn, fill=MUTED); x += wr
        d.text((x, y), after, font=fn, fill=GOLD); y += 250 + 20
        for ln in body:
            draw_words(d, LEFT, y, ln, fb, BODY, s.get("body_hl", ())); y += int(BODY_PX * 1.38)
        assert y <= BOTTOM, "result slide runs below the safe area"
    elif s["kind"] == "end":
        if s.get("follow"):
            # End card with a follow line: mark, "Follow North Reliability / and keep in touch.", signature.
            m = mark(240); im.paste(m, ((W - 240) // 2, 420), m)
            d.text((W // 2, 760), s.get("follow_line", "Follow North Reliability"), font=font("ExtraBold", 58), fill=WHITE, anchor="mm")
            d.text((W // 2, 836), s.get("follow_sub", "and keep in touch."), font=font("Medium", 44), fill=BODY, anchor="mm")
            d.text((W // 2, 990), s.get("line", "Find it before it fails."), font=font("ExtraBoldItalic", 66), fill=GOLD, anchor="mm")
        else:
            m = mark(280); im.paste(m, ((W - 280) // 2, 520), m)
            d.text((W // 2, 960), s.get("line", "Find it before it fails."), font=font("ExtraBoldItalic", 66), fill=GOLD, anchor="mm")
    else:
        h = measure(s, width); y = TOP + (BOTTOM - TOP - h) // 2
        text_block(d, LEFT, y, s, width)
    im.save(path)


# ------------------------------------------------------------------------ voice
def load_wav(path):
    with wave.open(path) as w:
        n, ch, sr = w.getnframes(), w.getnchannels(), w.getframerate()
        a = np.frombuffer(w.readframes(n), np.int16).astype(np.float32) / 32768
    return (a.reshape(-1, ch).mean(1) if ch > 1 else a), sr


def trim_silence(a, sr, db=-45.0):
    thr = 10 ** (db / 20); idx = np.where(np.abs(a) > thr)[0]
    if not len(idx): return a
    s, e = max(0, idx[0] - int(0.02 * sr)), min(len(a), idx[-1] + int(0.06 * sr))
    return a[s:e]


def voice_track(voice_dir, n, work, sr=44100):
    clips = []
    for i in range(1, n + 1):
        src = os.path.join(voice_dir, f"beat{i:02d}.mp3"); tmp = os.path.join(work, f"beat{i:02d}.wav")
        run([FF, "-y", "-loglevel", "error", "-i", src, "-ac", "1", "-ar", str(sr), tmp])
        a, _ = load_wav(tmp); clips.append(trim_silence(a, sr))
    return clips, sr


def timeline(durs):
    """durs: spoken seconds per slide. Returns starts of each voice clip, slide cut times, total."""
    starts, t = [], LEAD
    for i, d in enumerate(durs):
        starts.append(t); t += d + (GAP if i < len(durs) - 1 else 0)
    ends = [s + d for s, d in zip(starts, durs)]
    cuts = [0.0] + [e + GAP / 2 for e in ends[:-1]] + [ends[-1] + TAIL]
    return starts, cuts


# ---------------------------------------------------------------------- footage
def get_clip(cid, clips_dir):
    p = os.path.join(clips_dir, f"{cid}.mp4")
    if not os.path.exists(p):
        os.makedirs(clips_dir, exist_ok=True)
        for q in ("1080", "720"):
            try:
                req = urllib.request.Request(f"https://assets.mixkit.co/videos/{cid}/{cid}-{q}.mp4", headers={"User-Agent": "Mozilla/5.0"})
                with urllib.request.urlopen(req, timeout=120) as r, open(p, "wb") as f: shutil.copyfileobj(r, f)
                break
            except Exception:
                if os.path.exists(p): os.remove(p)
        if not os.path.exists(p): raise RuntimeError(f"Mixkit clip {cid} could not be downloaded")
    return p


def footage_segment(clip, ss, cx, frames, ov, out):
    dur = frames / FPS; avail = max(0.5, probe_dur(clip) - ss)
    slow = min(1.6, max(1.0, dur / avail))                 # gentle slow motion before looping
    loop = ["-stream_loop", "-1"] if avail * slow < dur else []
    vf = (f"[0:v]setpts={slow:.4f}*(PTS-STARTPTS),fps={FPS},scale=-2:{H}:flags=lanczos,"
          f"crop={W}:{H}:x='(iw-{W})*{cx}':y=0,eq=brightness=-0.05:saturation=0.95,setsar=1[b];"
          f"[b][1:v]overlay=0:0,format=yuv420p")
    run([FF, "-y", "-loglevel", "error", *loop, "-ss", str(ss), "-i", clip, "-i", ov, "-filter_complex", vf,
         "-frames:v", str(frames), "-an", "-c:v", "libx264", "-preset", "veryfast", "-crf", "21", "-r", str(FPS), out])


def still_segment(png, frames, out, zoom=0.03):
    vf = (f"scale={W*2}:{H*2},zoompan=z='1+{zoom}*on/{max(frames-1,1)}':x='iw/2-(iw/zoom/2)':"
          f"y='ih/2-(ih/zoom/2)':d={frames}:s={W}x{H}:fps={FPS},format=yuv420p")
    run([FF, "-y", "-loglevel", "error", "-i", png, "-vf", vf, "-frames:v", str(frames),
         "-c:v", "libx264", "-preset", "veryfast", "-crf", "21", out])


# ------------------------------------------------------------------------ build
def build(spec, out, voice_dir, clips_dir, music_script, preview):
    work = os.path.join(out, "_work"); os.makedirs(work, exist_ok=True)
    slides = spec["slides"]; n = len(slides)
    # 1. voice and timing
    if preview or not voice_dir:
        sr = 44100
        clips = [np.zeros(int(sr * len(s["voice"].split()) / EST_WPS), np.float32) for s in slides]
    else:
        clips, sr = voice_track(voice_dir, n, work)
    durs = [len(c) / sr for c in clips]
    starts, cuts = timeline(durs); total = cuts[-1]
    cut_frames = [round(c * FPS) for c in cuts]
    # 2. slide images
    pngs = []
    for i, s in enumerate(slides, 1):
        p = os.path.join(work, f"slide{i:02d}.png")
        (overlay_footage if s["kind"] == "footage" else full_text)(s, p); pngs.append(p)
    # 3. video segments
    segs = []
    for i, s in enumerate(slides):
        frames = cut_frames[i + 1] - cut_frames[i]
        if s["kind"] == "footage":
            shares = [c.get("share", 1) for c in s["clips"]]; acc = 0
            for j, c in enumerate(s["clips"]):
                fr = frames - acc if j == len(s["clips"]) - 1 else round(frames * shares[j] / sum(shares)); acc += fr
                o = os.path.join(work, f"seg{i+1:02d}_{j}.mp4")
                footage_segment(get_clip(c["id"], clips_dir), c.get("ss", 0), c.get("cx", 0.5), fr, pngs[i], o); segs.append(o)
        else:
            o = os.path.join(work, f"seg{i+1:02d}.mp4")
            still_segment(pngs[i], frames, o, 0.0 if s["kind"] == "end" else 0.03); segs.append(o)
    lst = os.path.join(work, "list.txt")
    open(lst, "w").write("".join(f"file '{os.path.abspath(p)}'\n" for p in segs))
    video = os.path.join(work, "video.mp4")
    run([FF, "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", video])
    # 4. audio: voice + music 18 dB under the voice
    N = int(total * sr) + sr; voice = np.zeros(N, np.float32)
    for st, c in zip(starts, clips):
        a = int(st * sr); voice[a:a + len(c)] += c
    mus_wav = os.path.join(work, "music.wav")
    run([sys.executable, music_script, mus_wav, f"{total:.2f}"])
    m, msr = load_wav(mus_wav); assert msr == sr
    m = np.pad(m, (0, max(0, N - len(m))))[:N]
    act = np.abs(voice) > 0.02
    v_rms = np.sqrt(np.mean(voice[act] ** 2)) if act.any() else 0.1
    m_rms = np.sqrt(np.mean(m ** 2)) + 1e-9
    mix = voice + m * (v_rms * 10 ** (-MUSIC_UNDER_DB / 20) / m_rms)
    mix = mix[:int(total * sr)]; mix = mix / max(1e-6, np.max(np.abs(mix))) * 0.89
    mix_wav = os.path.join(work, "mix.wav")
    with wave.open(mix_wav, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr); w.writeframes((mix * 32767).astype(np.int16).tobytes())
    # 5. mux, loudness to about -14 LUFS for Instagram
    final = os.path.join(out, f"{spec['name']}.mp4")
    run([FF, "-y", "-loglevel", "error", "-i", video, "-i", mix_wav, "-map", "0:v", "-map", "1:a", "-c:v", "copy",
         "-af", "loudnorm=I=-14:TP=-1.5:LRA=11,aresample=44100", "-ac", "2", "-c:a", "aac", "-b:a", "160k",
         "-shortest", "-movflags", "+faststart", final])
    # 6. checks: length, black frames, contact sheet, cover
    got = probe_dur(final)
    bd = subprocess.run([FF, "-hide_banner", "-i", final, "-vf", "blackdetect=d=0.4:pix_th=0.08", "-an", "-f", "null", "-"],
                        capture_output=True, text=True).stderr
    blacks = [l.strip() for l in bd.splitlines() if "black_start" in l]
    thumbs = []
    for i in range(n):
        t = (cuts[i] + cuts[i + 1]) / 2; p = os.path.join(work, f"thumb{i+1:02d}.jpg")
        run([FF, "-y", "-loglevel", "error", "-ss", f"{t:.2f}", "-i", final, "-frames:v", "1", "-vf", "scale=360:640", p]); thumbs.append(p)
    sheet = Image.new("RGB", (360 * min(n, 4), 640 * math.ceil(n / 4)), NAVY_DARK)
    for i, p in enumerate(thumbs): sheet.paste(Image.open(p), ((i % 4) * 360, (i // 4) * 640))
    sheet.save(os.path.join(out, "contact_sheet.jpg"), quality=88)
    run([FF, "-y", "-loglevel", "error", "-ss", f"{(cuts[0]+cuts[1])/2:.2f}", "-i", final, "-frames:v", "1", "-q:v", "2",
         os.path.join(out, f"{spec['name']}_cover.jpg")])
    rep = {"name": spec["name"], "mode": "preview" if (preview or not voice_dir) else "final",
           "seconds_planned": round(total, 2), "seconds_file": round(got, 2),
           "spoken_seconds": [round(x, 2) for x in durs], "slide_cuts": [round(c, 2) for c in cuts],
           "black_frames": blacks, "mb": round(os.path.getsize(final) / 1e6, 2), "file": final}
    rep["ok"] = abs(got - total) < 0.2 and not blacks and total <= 90
    json.dump(rep, open(os.path.join(out, "report.json"), "w"), indent=1)
    return rep


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("spec"); ap.add_argument("out")
    ap.add_argument("--voice"); ap.add_argument("--clips", default="clips")
    ap.add_argument("--fonts", default="/usr/share/fonts/opentype/inter")
    ap.add_argument("--music", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "make_music.py"))
    ap.add_argument("--preview", action="store_true")
    a = ap.parse_args()
    for wgt in ["Medium", "Bold", "ExtraBold", "ExtraBoldItalic", "Black"]:
        FONTS[wgt] = os.path.join(a.fonts, f"Inter-{wgt}.otf")
        if not os.path.exists(FONTS[wgt]): sys.exit(f"missing font {FONTS[wgt]}")
    spec = json.load(open(a.spec))
    print(json.dumps(build(spec, a.out, a.voice, a.clips, a.music, a.preview), indent=1))


if __name__ == "__main__":
    main()
