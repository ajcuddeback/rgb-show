import { Point3, luma } from './solve';
import { RGB } from '../models';

/** Something that can hand us grayscale frames of the tree. */
export interface FrameSource {
  readonly width: number;
  readonly height: number;
  /** Element to show in the UI (the live preview). */
  readonly element: HTMLElement;
  start(): Promise<void>;
  stop(): void;
  /** Grab the current frame as luma. */
  grab(): Promise<Float32Array>;
  /** Milliseconds to wait after changing the lights before grabbing. */
  readonly settleMs: number;
}

/** The phone's rear camera via getUserMedia, downscaled for processing. */
export class DeviceCamera implements FrameSource {
  readonly element: HTMLVideoElement;
  private stream: MediaStream | null = null;
  private canvas = document.createElement('canvas');
  width = 320;
  height = 240;
  readonly settleMs = 180;
  /** Back-facing cameras found after permission was granted (labels need permission). */
  cameras: MediaDeviceInfo[] = [];
  activeDeviceId: string | null = null;
  activeLabel = '';

  constructor() {
    this.element = document.createElement('video');
    this.element.playsInline = true;
    this.element.muted = true;
    this.element.autoplay = true;
  }

  async start(deviceId?: string): Promise<void> {
    this.stop();
    // Samsung/Chrome quirk: facingMode "environment" + a resolution hint often lands on the
    // telephoto lens. So: no resolution hint, and once we have permission (labels), reopen the
    // main wide camera by deviceId.
    const video: MediaTrackConstraints = deviceId ? { deviceId: { exact: deviceId } } : { facingMode: { ideal: 'environment' } };
    this.stream = await navigator.mediaDevices.getUserMedia({ video, audio: false });
    this.element.srcObject = this.stream;
    await this.element.play().catch(() => undefined);
    await this.waitForMetadata();

    const track = this.stream.getVideoTracks()[0];
    this.activeDeviceId = track.getSettings().deviceId ?? null;
    this.activeLabel = track.label;

    if (!deviceId) {
      await this.enumerate();
      const best = this.pickMainCamera();
      if (best && best.deviceId !== this.activeDeviceId) {
        return this.start(best.deviceId);
      }
    } else if (!this.cameras.length) {
      await this.enumerate();
    }

    // Widest view: zoom all the way out where the browser exposes zoom; fixed exposure/focus if available.
    try {
      const caps = (track.getCapabilities?.() ?? {}) as MediaTrackCapabilities & { zoom?: { min?: number } };
      const adv: Record<string, unknown>[] = [];
      if (caps.zoom && typeof caps.zoom.min === 'number') { adv.push({ zoom: caps.zoom.min }); }
      adv.push({ exposureMode: 'manual', focusMode: 'manual', whiteBalanceMode: 'manual' });
      for (const a of adv) { await track.applyConstraints({ advanced: [a as MediaTrackConstraintSet] }).catch(() => undefined); }
    } catch { /* not supported */ }

    const vw = this.element.videoWidth || 640, vh = this.element.videoHeight || 480;
    this.width = 320;
    this.height = Math.round((320 * vh) / vw);
    this.canvas.width = this.width;
    this.canvas.height = this.height;
  }

  /** Cycle to the next back camera (for phones where the auto-pick is wrong). */
  async switchCamera(): Promise<void> {
    if (this.cameras.length < 2) { return; }
    const i = this.cameras.findIndex(c => c.deviceId === this.activeDeviceId);
    const next = this.cameras[(i + 1) % this.cameras.length];
    await this.start(next.deviceId);
  }

  stop(): void {
    this.stream?.getTracks().forEach(t => t.stop());
    this.stream = null;
  }

  async grab(): Promise<Float32Array> {
    const ctx = this.canvas.getContext('2d', { willReadFrequently: true })!;
    ctx.drawImage(this.element, 0, 0, this.width, this.height);
    const img = ctx.getImageData(0, 0, this.width, this.height);
    return luma(img.data, this.width, this.height);
  }

  private async waitForMetadata(): Promise<void> {
    for (let i = 0; i < 100 && !(this.element.videoWidth > 0); i++) {
      await new Promise(r => setTimeout(r, 30));
    }
  }

  private async enumerate(): Promise<void> {
    try {
      const all = await navigator.mediaDevices.enumerateDevices();
      const vids = all.filter(d => d.kind === 'videoinput');
      const back = vids.filter(d => /back|rear|environment|facing back/i.test(d.label));
      // Android labels look like "camera2 0, facing back"; keep them in id order so 0 (main) comes first.
      const num = (d: MediaDeviceInfo) => { const m = /camera2?\s*(\d+)/i.exec(d.label); return m ? Number(m[1]) : 99; };
      this.cameras = (back.length ? back : vids).sort((a, b) => num(a) - num(b));
    } catch { this.cameras = []; }
  }

  private pickMainCamera(): MediaDeviceInfo | null {
    if (!this.cameras.length) { return null; }
    const isAux = (l: string) => /tele|ultra|zoom|depth|macro|wide angle|periscope/i.test(l);
    // iOS: "Back Camera" is the main wide. Android: the lowest-numbered back camera is.
    return this.cameras.find(c => /^back camera$/i.test(c.label))
      ?? this.cameras.find(c => !isAux(c.label))
      ?? this.cameras[0];
  }
}

/**
 * A pretend camera that photographs the *simulated* tree: it asks the server
 * what the strand is showing and renders those lights at their 3D positions as
 * seen from `azimuthDeg`. Lets the whole mapping flow run without hardware.
 */
export class SimulatedCamera implements FrameSource {
  readonly element: HTMLCanvasElement;
  readonly width = 320;
  readonly height = 426;
  readonly settleMs = 0;
  azimuthDeg = 0;
  private noise = 6;

  constructor(private truth: Point3[], private getFrame: () => Promise<RGB[]>) {
    this.element = document.createElement('canvas');
    this.element.width = this.width;
    this.element.height = this.height;
  }

  async start(): Promise<void> { await this.render([]); }
  stop(): void { /* nothing */ }

  async grab(): Promise<Float32Array> {
    const frame = await this.getFrame();
    await this.render(frame);
    const ctx = this.element.getContext('2d', { willReadFrequently: true })!;
    return luma(ctx.getImageData(0, 0, this.width, this.height).data, this.width, this.height);
  }

  private async render(frame: RGB[]): Promise<void> {
    const ctx = this.element.getContext('2d')!;
    const { width: w, height: h } = this;
    ctx.fillStyle = '#0a0a0c';
    ctx.fillRect(0, 0, w, h);
    // faint "room" so the frame isn't perfectly black
    for (let i = 0; i < 400; i++) {
      ctx.fillStyle = `rgba(255,255,255,${Math.random() * 0.03})`;
      ctx.fillRect(Math.random() * w, Math.random() * h, 2, 2);
    }
    const phi = (this.azimuthDeg * Math.PI) / 180;
    const rx = Math.cos(phi), ry = Math.sin(phi);           // image-right in world XY
    const cx = Math.sin(phi), cy = -Math.cos(phi);          // camera position direction
    const S = h * 0.26;                                     // world radius 1 -> pixels
    for (let i = 0; i < this.truth.length; i++) {
      const [x, y, z] = this.truth[i];
      const px = w / 2 + (x * rx + y * ry) * S;
      const py = h * 0.9 - z * h * 0.72;
      const facing = (x * cx + y * cy);                     // >0 = near side of the tree
      const occl = facing > -0.35 ? 1 : 0.25;               // far side mostly hidden by branches
      const c = frame[i] ?? [0, 0, 0];
      const lum = (c[0] + c[1] + c[2]) / 3;
      if (lum < 8) { continue; }
      const g = ctx.createRadialGradient(px, py, 0, px, py, 7);
      g.addColorStop(0, `rgba(${c[0]},${c[1]},${c[2]},${occl})`);
      g.addColorStop(0.4, `rgba(${c[0]},${c[1]},${c[2]},${0.6 * occl})`);
      g.addColorStop(1, 'rgba(0,0,0,0)');
      ctx.fillStyle = g;
      ctx.beginPath(); ctx.arc(px, py, 7, 0, Math.PI * 2); ctx.fill();
    }
    // sensor noise
    const img = ctx.getImageData(0, 0, w, h);
    for (let i = 0; i < img.data.length; i += 4) {
      const nz = (Math.random() - 0.5) * this.noise;
      img.data[i] += nz; img.data[i + 1] += nz; img.data[i + 2] += nz;
    }
    ctx.putImageData(img, 0, 0);
  }
}
