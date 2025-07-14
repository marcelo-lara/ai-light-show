# 🎛️ DMX Lighting Controller Context

## 1. Fixtures

Fixtures are treated as passive devices that respond only to raw DMX channel values. Each fixture has a type and channel layout:

### Supported Fixture Types:

* **RGB Parcan**

  * Channels: Red, Green, Blue, Dimmer
  * Requires `dimmer = 255` ("ARM" state) to emit RGB light
  
* **Moving Head**

  * Channels: PAN (MSB + LSB), TILT (MSB + LSB), Shutter, Dimmer, Color, Gobo, etc.
  * Requires `shutter = 255` ("ARM" state) to emit light
  * Supports discrete value ranges for modes, e.g.:

    * `color` channel: `0 = white`, `24 = yellow`, etc.
    * `gobo` channel: `0 = open`, `32 = spiral`, etc.

### Each Fixture Definition Includes:

* **channel\_map**: logical name → DMX address
* **arm\_condition**: which channels must be set to a specific value to emit
* **value\_mappings** (optional): symbolic → raw value lookup for discrete ranges

---

## 2. Templates & Chasers

Templates define animations (DMX value changes over time). Chasers apply templates across multiple fixtures.

### Example Templates:

* **Fade to Blue**

  ```json
  {
    "type": "fade",
    "target": "blue",
    "from": 0,
    "to": 255,
    "duration": 1000
  }
  ```

* **Pan Movement** (Moving Head)

  ```json
  {
    "type": "pan_tilt",
    "pan": [0, 255],
    "tilt": [0, 128],
    "duration": 2000
  }
  ```

### Example Chaser:

```json
{
  "type": "chase",
  "template": { "type": "fade", "target": "red", "from": 0, "to": 255, "duration": 800 },
  "fixtures": ["parcan_l", "parcan_r", "parcan_c"],
  "stagger": 200
}
```

---

## 3. Song Timeline & Playback

* Timeline is a **pre-rendered list** of `time → {channel: value}` mappings.
* The backend aligns DMX output to the song position with high precision.
* This avoids real-time overlaps and reduces CPU load.

### Playback Engine Responsibilities:

* Syncs with current song time (from local clock or OSC input)
* Sends Art-Net packets on time
* DEPRECATED: Evaluates all cues `time <= now` (removed)
* Respects ARM conditions before activating light

---

## 4. Backend Architecture

* Maintains `dmx_universe[512]` in memory
* Periodic loop (e.g. 100 fps) checks `timeline[]` against current time
* Sends Art-Net UDP packets using current `dmx_universe` values
* Offers APIs:

  * DEPRECATED: `POST /timeline` to load cues (removed)
  * `GET /timeline` to inspect
  * `POST /dmx/set` for real-time override
  * `WebSocket /ws` for live UI sync

### Optionally:

* Support OSC time sync
* Support looping sections
* Support fixture groups or matrix effects

---

> This system is designed for real-time lighting control driven by music structure, with low-latency output and timeline-driven accuracy.
