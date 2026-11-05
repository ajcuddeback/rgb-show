# RGB Show — Christmas Tree Light Controller

Control a strand of NeoPixels (WS2811 / WS2812) wrapped around a Christmas tree from your phone.
Flask + Python on a Raspberry Pi drives the lights; a small Angular app (pre-built, no Node needed on the Pi) is the remote.

- **33 animations** that understand the *shape* of the tree (height, angle, wraps): spirals, climbing rings, falling snow, fireworks that launch up the tree, aurora curtains, a pulsing tree-top star, glinting ornaments, a rotating beacon, fireflies, icicles, a starry night, and more.
- **Every animation is customizable** — colors (with palettes), speeds, densities, directions — and changes apply **live** while it plays.
- **Live preview** of the tree in the browser, mirroring exactly what the strand is showing.
- **Presets**: save and recall your favorite looks.
- **Survives reboots**: last animation, brightness and speed are restored on boot.
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
| `RGB_NUM_PIXELS` | `100` | Number of lights on the strand |
| `RGB_PIN` | `D18` | `board` pin name the data line is on (`D18`, `D12`, `D21`, …) |
| `RGB_TREE_RINGS` | auto | Lights per wrap, **bottom → top**, comma-separated, e.g. `32,26,20,14,8` (the default). Must sum to `RGB_NUM_PIXELS` (it's normalized if not). Unset = a cone layout is synthesized from the pixel count. |
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

Count how many lights are on each wrap starting at the bottom and set `RGB_TREE_RINGS`.
The spiral/climb/snow/fireworks effects use this to know which lights are at the same height and
which side of the tree they're on. Close enough is fine.

## Using the app

- Tap any animation card to play it immediately. The card glows green while live.
- The settings panel (right column on desktop, bottom sheet on phones) shows that animation's knobs. While it's live, every change applies instantly.
- Color lists have palette chips (Classic, Candy Cane, Winter, Aurora, …), `+` to add, `×` to remove, shuffle and random buttons.
- **Brightness** and **Speed** are global. Speed is a multiplier (0.25×–4×) applied on top of each animation's own tempo.
- **Save as preset** stores the current animation + settings on the Pi.
- The power toggle turns the lights off and remembers what was playing, so toggling back on resumes it.

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

### Client

```bash
cd client
npm ci
npm start                              # dev server on :4200, proxies /api to :5000
npm run build                          # production build straight into ../templates
```

**Commit the rebuilt `templates/` folder** — that's what the Pi serves.

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

`self.tree.height[i]`, `self.tree.angle[i]` and `self.tree.ring_of[i]` tell you where pixel `i` is on the tree.
Param types: `color`, `colors`, `number`, `select`, `boolean`.

## HTTP API

| Method | Path | Body | Purpose |
| --- | --- | --- | --- |
| GET | `/api/state` | | Power, current animation + params, speed, brightness, tree config |
| GET | `/api/animations` | | All animations with their param schemas |
| POST | `/api/animations/<name>/start` | `{"params": {...}}` | Start an animation (missing params use defaults) |
| PATCH | `/api/params` | `{"params": {...}}` | Live-update the running animation |
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
- `server/tree.py` — pixel → (height, angle, wrap) geometry
- `server/animations/` — base class, color helpers, registry, `effects/*`
- `client/` — Angular 17 UI (standalone components + signals)
- `templates/` — **built** UI, served by Flask
- `deploy/` — systemd units, nginx config, Home Assistant files

## License

MIT — see [LICENSE](LICENSE).
