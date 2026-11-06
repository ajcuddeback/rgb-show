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

  constructor() {
    this.element = document.createElement('video');
    this.element.playsInline = true;
    this.element.muted = true;
    this.element.autoplay = true;
  }

  async start(): Promise<void> {
    this.stream = await navigator.mediaDevices.getUserMedia({
      video: { facingMode: { ideal: 'environment' }, width: { ideal: 1280 }, height: { ideal: 720 } },
      audio: false,
    });
    this.element.srcObject = this.stream;
    await this.element.play();
    const track = this.stream.getVideoTracks()[0];
    // Fixed exposure/focus help a lot; silently ignore where unsupported (most iPhones).
    try {
      await track.applyConstraints({ advanced: [{ exposureMode: 'manual', focusMode: 'manual', whiteBalanceMode: 'manual' } as MediaTrackConstraintSet] });
    } catch { /* not supported */ }
    const vw = this.element.videoWidth || 640, vh = this.element.videoHeight || 480;
    this.width = 320;
    this.height = Math.round((320 * vh) / vw);
    this.canvas.width = this.width;
    this.canvas.height = this.height;
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
