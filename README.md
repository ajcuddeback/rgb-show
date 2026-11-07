# RGB Show — Christmas Tree Light Controller

Control a strand of NeoPixels (WS2811 / WS2812) wrapped around a Christmas tree from your phone.
Flask + Python on a Raspberry Pi drives the lights; a small Angular app (pre-built, no Node needed on the Pi) is the remote.

- **41 animations** that understand the *shape* of the tree (height, angle, wraps): spirals, climbing rings, falling snow, fireworks that launch up the tree, aurora curtains, a pulsing tree-top star, glinting ornaments, a rotating beacon, fireflies, icicles, a starry night, and true-3D sweeps, pulses and orbits.
- **Every animation is customizable** — colors (with palettes), speeds, densities, directions — and changes apply **live** while it plays.
- **Live preview** of the tree in the browser, mirroring exactly what the strand is showing.
- **Presets**: save and recall your favorite looks.
- **Installable**: it's a PWA — add it to your phone's home screen and it opens like an app, full screen, and updates itself when you deploy.
- **Map your tree with your phone's camera**: the app flashes each light while the camera watches, from two or more angles, and solves every light's 3D position. Every effect then follows the real shape of *your* tree. (Or just type lights-per-wrap in the app — no config files either way.)
- **Survives reboots**: last animation, brightness and speed are restored on boot.
- **Music**: make the Pi a Spotify Connect speaker, and the lights follow the song — five music-reactive effects plus a one-tap *sync every animation to the music* mode (tempo-locked, pumping on the beat). A built-in demo beat means you can see it without a speaker.
- **Home Assistant** integration: shows up as a light with every animation as an effect, plus presets and speed. One service, zero HA config.
- **Runs anywhere**: without NeoPixel hardware the server falls back to a simulator, so you can develop on a laptop.

## Hardware

- Raspberry Pi (any model with GPIO; Zero W through Pi 5) with the data line on **GPIO18** (`board.D18`) by default. `setup.sh` installs the extra PIO driver a Pi 5 needs automatically.
- NeoPixel-compatible strand (WS2811 / WS2812 / SK6812). Count and tree layout are configured, not hard-coded.
- Adequate 5V/12V supply for the strand, common ground with the Pi, ideally a level shifter on the data line.

## Quick start on the Pi

```bash
git clone https://github.com/ajcuddeback/rgb-show.git ~/rgb-show
cd ~/rgb-show
./setup.sh
```

`setup.sh` creates a venv in `server/.venv` with the Python dependencies (Raspberry Pi OS blocks system-wide pip), a **systemd service** (`rgb-show`) that starts on boot, and an nginx proxy on port 80. Open `http://<pi-ip>/`.

Useful commands:

```bash
sudo systemctl status rgb-show      # is it running?
journalctl -u rgb-show -f           # live logs
sudo systemctl restart rgb-show     # after changing config or pulling code
```

### Redeploying after a `git pull`

The UI is committed pre-built in `templates/`, so a redeploy is just:

```bash
cd ~/rgb-show && git pull && sudo systemctl restart rgb-show
```

If `server/requirements.txt` changed, run `./setup.sh` again (it's idempotent).

## Configuration

All settings are environment variables. For the systemd service, edit them in
`/etc/systemd/system/rgb-show.service` (or `sudo systemctl edit rgb-show`), then
`sudo systemctl daemon-reload && sudo systemctl restart rgb-show`.

| Variable | Default | Meaning |
| --- | --- | --- |
| `RGB_NUM_PIXELS` | `100` | Number of lights on the strand *(first-boot default — change it in the app under “Set up tree”)* |
| `RGB_PIN` | `D18` | `board` pin name the data line is on (`D18`, `D12`, `D21`, …) |
| `RGB_TREE_RINGS` | auto | Lights per wrap, **bottom → top**, comma-separated, e.g. `32,26,20,14,8` (the default). Must sum to `RGB_NUM_PIXELS` (it's normalized if not). Unset = a cone layout is synthesized from the pixel count. *(First-boot default — edit wraps in the app.)* |
| `RGB_LAYOUT` | `tree` | `tree` (spiral on a cone) or `strand` (straight line, e.g. a roofline) |
| `RGB_BRIGHTNESS` | `0.1` | Startup brightness 0–1 (overridden by the saved state once you change it in the UI) |
| `RGB_PIXEL_ORDER` | `RGB` | Color order of your strand: `RGB`, `GRB`, `BRG`, … If red shows as green, change this. |
| `RGB_GAMMA` | `1.0` | Off by default so colors match the original build exactly. Set `2.2` for perceptually smoother fades/dim colors (tree looks a bit dimmer at the same brightness). |
| `RGB_FPS` | `30` | Animation frame rate cap |
| `RGB_AUTOSTART` | `true` | Resume the last animation on boot |
| `RGB_DATA_DIR` | `server/` | Where `state.json` and `presets.json` are stored |
| `RGB_SIMULATE` | `false` | Use the in-memory simulator. Off-Pi the server also falls back to it (with a warning) when the NeoPixel libraries aren't installed. On a Pi where the libraries *are* installed but the strand can't be opened, the service fails loudly instead of pretending. |
| `RGB_HOST` / `RGB_PORT` | `0.0.0.0` / `5000` | Only used by `python3 app.py` (gunicorn has its own `--bind`) |

### Mapping your tree

Effects need to know where each light *is*. Two ways to tell them, both in the app under **Tree setup**:

**Map with camera (best).** Turn the room lights off, prop your phone up with the whole tree in frame, and tap
*Map with camera*. The app flashes each light in turn while the camera watches (~20 s for 100 lights) and finds it
in the frame; then you walk a quarter of the way around the tree and do it again. Two views at 90° give every
light a real 3D position; three or four help a dense tree. Lights the camera never saw are placed between their
wire-neighbors; reflections are rejected automatically. The result is saved on the Pi and the preview starts
drawing your actual tree (drag it to look around). Needs HTTPS (or localhost) for camera access — so use your
public URL, not the LAN IP, on phones.

*How it works:* per view, a dark reference frame is subtracted from each flash frame and the brightest blob's
centroid is recorded. Views are normalized by the tree's apparent height so phone distance doesn't matter, then
each light's (x, y) is a least-squares fit across views and z is averaged. No ML involved — the lights identify
themselves by blinking. On a simulated server a *simulated camera* runs the same pipeline against the virtual tree.

**Edit lights & wraps (quick).** Enter the number of lights and how many sit on each wrap from the bottom up
(or hit *Even cone*). The server assumes a cone spiral. Close enough is fine.

Either way the strand is reconfigured live, the layout is saved on the Pi (overriding the env defaults above),
and the current animation restarts on the new geometry.

## Using the app

- Tap any animation card to play it immediately. The card glows green while live.
- The settings panel (right column on desktop, bottom sheet on phones) shows that animation's knobs. While it's live, every change applies instantly.
- Color lists have palette chips (Classic, Candy Cane, Winter, Aurora, …), `+` to add, `×` to remove, shuffle and random buttons.
- **Brightness** and **Speed** are global. Speed is a multiplier (0.25×–4×) applied on top of each animation's own tempo.
- **Save as preset** stores the current animation + settings on the Pi.
- The power button turns the lights off and remembers what was playing, so pressing it again resumes.
- **Install it**: on iPhone, Share → *Add to Home Screen*; on Android/desktop Chrome, use the install icon in the address bar. Installed copies pick up new deploys automatically on next open. (Chrome's install prompt needs HTTPS or `localhost`; iOS Add-to-Home-Screen works over plain HTTP too.)

## Music

**How it works.** `raspotify` turns the Pi into a Spotify Connect device called **Christmas Tree**. Instead of
playing straight to the sound card, librespot writes raw PCM into a FIFO (`/var/lib/rgb-show/audio.fifo`); the
rgb-show server reads that stream, analyzes it (FFT → bass/mid/treble, onset detection → beats, autocorrelation →
BPM) and plays it out the speaker itself. Lights and sound are therefore one stream, and the server delays the
features by the measured output latency so the flash lands on the kick. ~2 % CPU on a Pi 5.

**You need a speaker.** The Pi 5 has no headphone jack: use a USB speaker / USB DAC, HDMI audio, or a DAC HAT.
Pick it under *Music → Details → Speaker* if it isn't the system default.

**Using it**
1. `./setup.sh` installs raspotify and the config (skip with `--no-spotify`).
2. In the Spotify app on your phone, tap the device picker and choose **Christmas Tree**.
3. In the web app's **Music** card, set *Source* to **Spotify**. The meters start moving; the status shows the BPM.
4. Either play one of the **Music** effects (VU Meter, Beat Pulse, Spectrum, Energy Glow, Beat Chase) or flip
   **Sync every animation to the music** to make *any* effect follow the tempo and pump on the beat.

*Sensitivity* scales how hard the lights react (auto-gain already evens out quiet vs. loud songs).
**Demo beat** is a built-in drum loop so you can try everything without Spotify or a speaker; other input devices
(a USB mic, a loopback) appear in the source list when PortAudio is installed (`setup.sh` does that).

Environment: `RGB_AUDIO_FIFO` (default `/var/lib/rgb-show/audio.fifo`) must match `LIBRESPOT_DEVICE` in `/etc/raspotify/conf`.

## Home Assistant

### Option A — MQTT bridge (recommended)

A tiny companion service on the Pi (`server/ha_bridge.py`) uses MQTT discovery, so the tree simply
appears in HA as a device named **Christmas Tree** with:

| Entity | What it does |
| --- | --- |
| `light.christmas_tree` | On/off (off remembers, on resumes), brightness, RGB color, and an **effect list of every animation** |
| `select.christmas_tree_preset` | Apply any preset you saved in the web UI |
| `number.christmas_tree_speed` | The global speed multiplier |
| `button.christmas_tree_surprise_me` | Start a random animation |

Requirements: an MQTT broker HA can see (the **Mosquitto** add-on is the usual one) and the MQTT integration enabled in HA.

```bash
sudo nano /etc/rgb-show-ha.env        # set MQTT_HOST, MQTT_USER, MQTT_PASSWORD
```

```bash
sudo systemctl enable --now rgb-show-ha && journalctl -u rgb-show-ha -f
```

Within a few seconds HA shows the device under Settings → Devices → MQTT. Picking a color in HA sets the
animation's main color (for multi-color effects, the first color); picking an effect starts that animation
with its defaults — or with the color you chose, if you set both. State flows back to HA every 2 s and
instantly after a command, so your dashboards stay in sync with the web UI.

Automations are then plain HA:

```yaml
- alias: Tree on at dusk
  trigger: { platform: sun, event: sunset, offset: "-00:30:00" }
  action:
    - service: light.turn_on
      target: { entity_id: light.christmas_tree }
      data: { effect: "Twinkle", brightness_pct: 40 }
- alias: Tree off at bedtime
  trigger: { platform: time, at: "23:30:00" }
  action:
    - service: light.turn_off
      target: { entity_id: light.christmas_tree }
```

### Option B — REST only (no broker)

`deploy/home-assistant/rgb_show_rest.yaml` is a HA *package* that builds the same `light.christmas_tree`
from `rest` sensors, `rest_command`s and a template light. Copy it to `config/packages/`, change the IP, restart HA.
It polls every 5 s, so state in HA lags a little behind the web UI.

## Developing

### Server (no Pi required)

```bash
cd server
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements-dev.txt
RGB_SIMULATE=1 python app.py          # http://localhost:5000
pytest                                 # 170+ tests covering every animation and the API
```

### Why the preview polls instead of using WebSockets

The live preview fetches `/api/frame` ~8×/s (only while the tab is visible and the lights are on). That's a
~600-byte response over a kept-alive connection — cheap, and it works through any reverse proxy with no
special config. WebSockets would add a Flask extension, a different gunicorn worker class and a proxy toggle;
Server-Sent Events would pin one of gunicorn's few worker threads per open tab. Neither buys anything for a
single-household light controller, so polling stays.

### Client

```bash
cd client
npm ci
npm start                              # dev server on :4200, proxies /api to :5000
npm run build                          # production build straight into ../templates
```

**Commit the rebuilt `templates/` folder** — that's what the Pi serves. The build includes the service worker
(`ngsw-worker.js`, `ngsw.json`); the included nginx config and Flask both serve those with `no-cache` so installed apps update.

### Adding an animation

Drop a class into `server/animations/effects/` — it's auto-discovered, and the UI builds its controls from `PARAMS`:

```python
from ..base import Animation, Param
from ..colors import gradient

class Heartbeat(Animation):
    LABEL = "Heartbeat"
    DESCRIPTION = "Two quick pulses, then a rest."
    CATEGORY = "Motion"            # Static | Motion | Sparkle | Nature | Showpiece
    PARAMS = [
        Param("colors", "colors", "Colors", [(255, 0, 0), (120, 0, 0)]),
        Param("bpm", "number", "Beats per minute", 60, min=30, max=180, step=1),
    ]
    PREVIEW = [(255, 0, 0)]

    def render(self, t):           # t = seconds, already scaled by the global speed
        beat = (t * self.p("bpm") / 60) % 1
        level = max(0.0, 1 - beat * 3) + max(0.0, 1 - abs(beat - 0.3) * 6) * 0.6
        self.fill(gradient(self.p("colors"), 1 - level, wrap=False))
```

`self.af` holds the current audio features (`level`, `bass`, `mid`, `treble`, `beat`, `beat_env`, `bpm`, `phase`, `active`) for music-reactive effects.
`self.tree.x[i]`, `.y[i]`, `.z[i]` (normalized 3D; front of the tree is -y), `.height[i]` (= z), `.angle[i]` (turns around
the trunk, 0..1), `.radius[i]` and `.ring_of[i]` (height band) tell you where pixel `i` is. `tree.pixels_in_ring(r)` and
`tree.top_pixels(k)` are handy. These come from the camera map when there is one, otherwise from the cone estimate,
so effects written against them look right either way.
Param types: `color`, `colors`, `number`, `select`, `boolean`.

## HTTP API

| Method | Path | Body | Purpose |
| --- | --- | --- | --- |
| GET | `/api/state` | | Power, current animation + params, speed, brightness, tree config |
| GET | `/api/animations` | | All animations with their param schemas |
| POST | `/api/animations/<name>/start` | `{"params": {...}}` | Start an animation (missing params use defaults) |
| PATCH | `/api/params` | `{"params": {...}}` | Live-update the running animation |
| GET/PUT | `/api/layout` | `{"numPixels": 100, "rings": [32,26,20,14,8]}` or `{"numPixels": 100, "points": [[x,y,z]|null, ...]}` | Read / change the strand length and geometry (live, persisted). Response includes normalized `points` and `source` |
| POST | `/api/calibration/start` | `{"brightness": 0.6}` | Enter mapping mode: show paused, lights off |
| POST | `/api/calibration/light` | `{"index": 42}` / `{"all": true}` / `{"index": null}` | Light exactly one pixel (or all / none) |
| POST | `/api/calibration/stop` | | Leave mapping mode and resume what was playing |
| GET/POST | `/api/audio` | `{"source": "spotify"|"synthetic"|"off"|"device:N", "sensitivity": 1.0, "sync": true, "output": "default", "demoBpm": 120}` | Music source, sensitivity, sync-to-music; GET includes live features and device lists |
| POST | `/api/power` | `{"on": true}` | Off remembers; on resumes |
| POST | `/api/brightness` | `{"brightness": 0.3}` | 0–1 |
| POST | `/api/speed` | `{"speed": 1.5}` | Global multiplier |
| GET | `/api/frame` | | Current pixel colors (what the preview draws) |
| GET/POST | `/api/presets` | `{"name": "..."}` | List / save current as preset |
| POST | `/api/presets/<id>/apply` | | Play a preset |
| DELETE | `/api/presets/<id>` | | Remove a preset |

Handy from a shell or Home Assistant:

```bash
curl -X POST http://tree.local/api/animations/twinkle/start -H 'content-type: application/json' \
     -d '{"params": {"colors": [[255,0,0],[0,255,0]], "density": 0.5}}'
```

## Project structure

- `server/app.py` — Flask app and API
- `server/engine.py` — owns the running animation thread, persistence
- `server/ha_bridge.py` — optional Home Assistant MQTT bridge
- `server/audio/` — analyzer (FFT/beats/BPM), sources (Spotify FIFO, demo loop, input devices), playback
- `server/tree.py` — pixel → 3D position / height / angle / band geometry (from camera map or cone estimate)
- `server/animations/` — base class, color helpers, registry, `effects/*`
- `client/` — Angular 17 UI (standalone components + signals); `src/app/mapping/` holds the camera pipeline and 3D solver
- `templates/` — **built** UI, served by Flask
- `deploy/` — systemd units, nginx config, Home Assistant files

## License

MIT — see [LICENSE](LICENSE).
