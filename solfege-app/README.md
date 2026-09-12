# Solfa — Sheet Music to Solfège

Upload a photo of a line of sheet music and get movable-do solfège
(Do, Re, Mi, Fa, Sol, La, Ti) back, measure by measure.

## How it works
1. **OMR (oemer)** reads the image and produces a MusicXML transcription.
2. **music21** parses the MusicXML, detects the key signature.
3. A solfège engine maps each note's pitch to a movable-do syllable
   relative to that key (including chromatic syllables like Fi, Se, Te
   for accidentals).
4. A small web UI lets you drag-and-drop an image and see the result.

## Setup

```bash
pip install -r requirements.txt
```

## Run

```bash
cd backend
uvicorn app:app --reload --port 8000
```

Then open http://localhost:8000 in your browser.

## Notes
- First run downloads oemer's model weights (needs internet access once).
- Works best on a single clean staff line/system per image — clear
  printed scores, minimal skew, good lighting.
- Currently reads the top staff/part as the melody line.

## Deploying to a real public URL (Render, free tier)

This gives you an actual `https://your-app.onrender.com` link that anyone
can open — the backend (OMR) and frontend are served together from one
container, so there's nothing else to wire up.

1. Push this folder to a new GitHub repo.
2. Go to https://render.com → New → Web Service → connect the repo.
3. Render will detect `render.yaml`/`Dockerfile` automatically. If it
   asks: runtime = **Docker**, plan = **Free**.
4. Click Create Web Service. First build takes ~10-15 min (it's
   installing OMR's ML dependencies). First real request will also be
   slow the first time, since oemer downloads its model weights then.
5. Once live, open the URL it gives you — that's your working site.

**Honest limitations to know about:**
- Free tiers are CPU-only and have limited RAM. OMR is a real neural
  network doing image inference — expect each conversion to take
  30 seconds to a couple of minutes, and very large/complex images
  may fail or time out on the smallest free tiers.
- Free web services on Render sleep after inactivity; the first
  request after sleeping takes longer while it wakes up.
- If you outgrow the free tier, bumping to a small paid instance
  (more RAM/CPU) is the main lever for speed and reliability.
