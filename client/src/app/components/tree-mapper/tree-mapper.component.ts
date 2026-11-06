import { AfterViewInit, Component, ElementRef, OnDestroy, ViewChild, computed, inject, signal } from '@angular/core';
import { DecimalPipe } from '@angular/common';
import { RgbService } from '../../services/rgb.service';
import { DeviceCamera, FrameSource, SimulatedCamera } from '../../mapping/camera';
import { Observation, Point3, detectBlob, solvePoints } from '../../mapping/solve';

type Step = 'intro' | 'capture' | 'result';

/**
 * Full-screen flow that maps every light's 3D position with the phone camera:
 * dark frame -> flash each LED and find it -> repeat from 2-4 angles -> solve.
 */
@Component({
  selector: 'app-tree-mapper',
  standalone: true,
  imports: [DecimalPipe],
  templateUrl: './tree-mapper.component.html',
  styleUrls: ['./tree-mapper.component.scss'],
})
export class TreeMapperComponent implements AfterViewInit, OnDestroy {
  svc = inject(RgbService);
  @ViewChild('viewport') viewport!: ElementRef<HTMLDivElement>;

  step = signal<Step>('intro');
  angles = signal(2);
  useSim = signal(false);
  angleIndex = signal(0);
  running = signal(false);
  progress = signal(0);          // 0..n during a capture
  total = computed(() => this.svc.config()?.numPixels ?? 0);
  foundThisAngle = signal<number | null>(null);
  dots = signal<{ x: number; y: number; ok: boolean }[]>([]);
  error = signal<string | null>(null);
  result = signal<{ points: (Point3 | null)[]; located: number; partial: number; missing: number; outliers: number } | null>(null);
  saving = signal(false);
  viewW = signal(320);
  viewH = signal(240);

  private source: FrameSource | null = null;
  private views: Observation[][] = [];
  private cancelled = false;

  get simulated(): boolean { return !!this.svc.config()?.simulated; }

  angleLabel = computed(() => {
    const k = this.angleIndex(), n = this.angles();
    if (k === 0) { return 'Stand in front of the tree'; }
    const frac = n === 3 ? 'a third' : 'a quarter';
    return `Walk to your right, ${frac} of the way around the tree`;
  });

  ngAfterViewInit(): void {
    this.useSim.set(this.simulated);
  }

  ngOnDestroy(): void {
    this.teardown();
  }

  // ------------------------------------------------------------------ flow
  async begin(): Promise<void> {
    this.error.set(null);
    try {
      if (this.useSim()) {
        const truth = (this.svc.config()?.points ?? []) as Point3[];
        this.source = new SimulatedCamera(truth, () => this.svc.frameRgb());
      } else {
        if (!navigator.mediaDevices?.getUserMedia) {
          throw new Error('Camera access needs a secure (https) connection or localhost.');
        }
        this.source = new DeviceCamera();
      }
      await this.source.start();
      this.viewW.set(this.source.width);
      this.viewH.set(this.source.height);
      this.views = [];
      this.angleIndex.set(0);
      this.step.set('capture');
      // The capture view renders on the next change-detection pass; attach the camera element then.
      for (let tries = 0; !this.viewport && tries < 50; tries++) { await this.sleep(10); }
      const host = this.viewport?.nativeElement;
      if (!host) { throw new Error('Could not show the camera preview.'); }
      host.innerHTML = '';
      host.appendChild(this.source.element);
    } catch (e) {
      this.error.set((e as Error).message || 'Could not start the camera.');
    }
  }

  async captureAngle(): Promise<void> {
    if (!this.source || this.running()) { return; }
    this.running.set(true);
    this.cancelled = false;
    this.error.set(null);
    this.dots.set([]);
    this.foundThisAngle.set(null);
    const n = this.total();
    const src = this.source;
    const w = src.width, h = src.height;
    try {
      if (src instanceof SimulatedCamera) { src.azimuthDeg = this.azimuth(this.angleIndex()); }
      await this.svc.calibrationStart(0.6);
      await this.svc.calibrationLight(null);
      await this.sleep(Math.max(src.settleMs, 120));
      // dark reference: average of a few frames
      const dark = await src.grab();
      for (let k = 0; k < 2; k++) {
        const f = await src.grab();
        for (let i = 0; i < dark.length; i++) { dark[i] = (dark[i] + f[i]) / 2; }
      }
      const obs: Observation[] = new Array(n).fill(null);
      let found = 0;
      for (let i = 0; i < n; i++) {
        if (this.cancelled) { break; }
        await this.svc.calibrationLight(i);
        if (src.settleMs) { await this.sleep(src.settleMs); }
        const cur = await src.grab();
        const b = detectBlob(cur, dark, w, h);
        obs[i] = b;
        if (b) { found++; this.dots.update(d => [...d, { x: b.x, y: b.y, ok: true }]); }
        this.progress.set(i + 1);
      }
      await this.svc.calibrationLight(null);
      if (!this.cancelled) {
        this.views[this.angleIndex()] = obs;
        this.foundThisAngle.set(found);
      }
    } catch (e) {
      this.error.set((e as Error).message || 'Capture failed.');
    } finally {
      this.running.set(false);
    }
  }

  cancelCapture(): void { this.cancelled = true; }

  retake(): void {
    this.foundThisAngle.set(null);
    this.dots.set([]);
  }

  nextAngle(): void {
    if (this.angleIndex() + 1 < this.angles()) {
      this.angleIndex.update(k => k + 1);
      this.foundThisAngle.set(null);
      this.dots.set([]);
    } else {
      this.finish();
    }
  }

  finish(): void {
    const az = Array.from({ length: this.angles() }, (_, k) => this.azimuth(k));
    const views = this.views.filter(v => !!v);
    const res = solvePoints(views, az.slice(0, views.length), this.viewW(), this.viewH());
    this.result.set(res);
    this.step.set('result');
    void this.svc.calibrationStop();
    this.source?.stop();
  }

  async save(): Promise<void> {
    const r = this.result();
    if (!r) { return; }
    this.saving.set(true);
    const ok = await this.svc.saveMappedLayout(r.points);
    this.saving.set(false);
    if (ok) { this.close(); }
  }

  close(): void {
    this.teardown();
    this.svc.mapperOpen.set(false);
  }

  // --------------------------------------------------------------- helpers
  /** Camera azimuth for angle k. Two angles are a quarter turn apart (front + side); more spread evenly. */
  azimuth(k: number): number { return this.angles() === 2 ? 90 * k : (360 / this.angles()) * k; }

  dotStyle(d: { x: number; y: number }): Record<string, string> {
    return { left: `${(d.x / this.viewW()) * 100}%`, top: `${(d.y / this.viewH()) * 100}%` };
  }

  private teardown(): void {
    this.cancelled = true;
    this.source?.stop();
    this.source = null;
    void this.svc.calibrationStop();
  }

  private sleep(ms: number): Promise<void> { return new Promise(r => setTimeout(r, ms)); }
}
