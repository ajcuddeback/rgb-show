import { AfterViewInit, Component, ElementRef, OnDestroy, ViewChild, effect, inject } from '@angular/core';
import { RgbService } from '../../services/rgb.service';
import { RGB } from '../../models';

interface Dot { x: number; y: number; depth: number; r: number; }

/**
 * Hero card: a live mirror of the tree. Polls /api/frame and draws the pixels on a
 * cone using the same wrap geometry as the server, with a soft ambient glow.
 */
@Component({
  selector: 'app-tree-preview',
  standalone: true,
  template: `
    <div class="hero card">
      <canvas #canvas></canvas>
      <div class="hud">
        <div class="status">
          <h1>Tree Lights</h1>
          <p class="muted small">
            @if (svc.offline()) { Offline }
            @else if (svc.power()) { <span class="live-dot"></span> {{ svc.currentDef()?.label }} }
            @else { Off }
          </p>
        </div>
        <button type="button" class="power" [class.on]="svc.power()" (click)="svc.setPower(!svc.power())"
                [attr.aria-pressed]="svc.power()" [attr.aria-label]="svc.power() ? 'Turn off' : 'Turn on'">
          <svg viewBox="0 0 24 24" width="22" height="22" aria-hidden="true">
            <path d="M12 3v9" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"/>
            <path d="M7.2 6.3a7 7 0 1 0 9.6 0" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"/>
          </svg>
        </button>
      </div>
      @if (svc.config()?.simulated) { <span class="sim faint small">Simulated</span> }
    </div>
  `,
  styles: [`
    :host { display: block; }
    .hero { position: relative; overflow: hidden; aspect-ratio: 4 / 5; background: radial-gradient(120% 90% at 50% 100%, #1a1d23 0%, var(--surface) 60%); }
    canvas { position: absolute; inset: 0; width: 100%; height: 100%; display: block; }
    .hud { position: absolute; left: 18px; right: 18px; top: 16px; display: flex; justify-content: space-between; align-items: flex-start; gap: 12px; }
    .status p { display: flex; align-items: center; gap: 6px; margin-top: 2px; }
    .live-dot { width: 7px; height: 7px; border-radius: 50%; background: var(--green); animation: breathe 2s ease-in-out infinite; }
    .power {
      width: 46px; height: 46px; border-radius: 50%; cursor: pointer; flex: 0 0 auto;
      border: 1px solid var(--border-2); background: rgba(255,255,255,0.06); color: var(--text-2);
      display: inline-flex; align-items: center; justify-content: center; transition: all 0.2s; backdrop-filter: blur(8px);
      &:hover { color: var(--text); background: rgba(255,255,255,0.1); }
      &.on { background: var(--accent); border-color: var(--accent); color: var(--accent-ink); box-shadow: 0 0 24px rgba(246,196,83,0.35); }
      &:focus-visible { outline: none; box-shadow: 0 0 0 3px var(--accent-soft); }
    }
    .sim { position: absolute; right: 16px; bottom: 12px; }
  `],
})
export class TreePreviewComponent implements AfterViewInit, OnDestroy {
  svc = inject(RgbService);
  @ViewChild('canvas') canvasRef!: ElementRef<HTMLCanvasElement>;

  private dots: Dot[] = [];
  private order: number[] = [];
  private frame: RGB[] = [];
  private timer: ReturnType<typeof setInterval> | null = null;
  private inflight = false;
  private ringsKey = '';

  constructor() {
    effect(() => {
      const cfg = this.svc.config();
      if (!cfg) { return; }
      const key = cfg.rings.join(',');
      if (key !== this.ringsKey) { this.ringsKey = key; this.layout(cfg.rings); this.draw(); }
    });
    effect(() => { if (!this.svc.power()) { this.frame = []; this.draw(); } });
  }

  ngAfterViewInit(): void {
    const canvas = this.canvasRef.nativeElement;
    new ResizeObserver(() => this.resize()).observe(canvas);
    this.resize();
    this.timer = setInterval(() => this.poll(), 125);
  }

  ngOnDestroy(): void { if (this.timer) { clearInterval(this.timer); } }

  private resize(): void {
    const canvas = this.canvasRef?.nativeElement;
    if (!canvas) { return; }
    const dpr = Math.min(2, window.devicePixelRatio || 1);
    canvas.width = Math.round((canvas.clientWidth || 300) * dpr);
    canvas.height = Math.round((canvas.clientHeight || 375) * dpr);
    const cfg = this.svc.config();
    if (cfg) { this.layout(cfg.rings); }
    this.draw();
  }

  private layout(rings: number[]): void {
    const canvas = this.canvasRef?.nativeElement;
    if (!canvas) { return; }
    const W = canvas.width, H = canvas.height;
    const top = H * 0.2, base = H * 0.86, cx = W / 2, R = W * 0.36;
    const numRings = rings.length;
    const dots: Dot[] = [];
    for (let r = 0; r < numRings; r++) {
      for (let k = 0; k < rings[r]; k++) {
        const frac = k / rings[r];
        const h = numRings === 1 ? frac : (r + frac) / numRings;
        const hn = Math.min(1, h / ((numRings - 1 + (rings[numRings - 1] - 1) / rings[numRings - 1]) / numRings || 1));
        const theta = frac * Math.PI * 2 - Math.PI / 2;
        const radius = R * (1 - hn * 0.9) + W * 0.015;
        const depth = Math.sin(theta);
        dots.push({
          x: cx + radius * Math.cos(theta),
          y: base - hn * (base - top) + radius * 0.28 * depth,
          depth,
          r: W * (0.011 + 0.006 * (depth + 1) / 2) * (rings.reduce((a, b) => a + b, 0) > 150 ? 0.7 : 1),
        });
      }
    }
    this.dots = dots;
    this.order = dots.map((_, i) => i).sort((a, b) => dots[a].depth - dots[b].depth);
  }

  private poll(): void {
    if (!this.svc.power() || this.inflight || document.visibilityState !== 'visible') { return; }
    this.inflight = true;
    this.svc.getFrame().subscribe({
      next: res => { this.inflight = false; this.frame = res.pixels; this.draw(); },
      error: () => { this.inflight = false; },
    });
  }

  private draw(): void {
    const canvas = this.canvasRef?.nativeElement;
    if (!canvas || !this.dots.length) { return; }
    const ctx = canvas.getContext('2d');
    if (!ctx) { return; }
    const W = canvas.width, H = canvas.height;
    ctx.clearRect(0, 0, W, H);
    const frame = this.frame;
    const on = this.svc.power() && frame.length > 0;
    const bright = 0.45 + 0.55 * Math.sqrt(this.svc.brightness());

    // Ambient glow behind the tree in the average lit color
    if (on) {
      let r = 0, g = 0, b = 0, n = 0;
      for (const px of frame) { if (px[0] + px[1] + px[2] > 12) { r += px[0]; g += px[1]; b += px[2]; n++; } }
      if (n) {
        r /= n; g /= n; b /= n;
        const glow = ctx.createRadialGradient(W / 2, H * 0.58, 0, W / 2, H * 0.58, W * 0.6);
        glow.addColorStop(0, `rgba(${r},${g},${b},${0.22 * bright})`);
        glow.addColorStop(1, 'rgba(0,0,0,0)');
        ctx.fillStyle = glow;
        ctx.fillRect(0, 0, W, H);
      }
    }

    // Tree silhouette
    const top = H * 0.18, base = H * 0.88, cx = W / 2, R = W * 0.4;
    ctx.fillStyle = on ? '#1f3a28' : '#1a2a20';
    ctx.beginPath();
    ctx.moveTo(cx, top);
    ctx.lineTo(cx + R, base);
    ctx.quadraticCurveTo(cx, base + H * 0.035, cx - R, base);
    ctx.closePath();
    ctx.fill();
    ctx.fillStyle = '#4a3320';
    ctx.fillRect(cx - W * 0.045, base + H * 0.012, W * 0.09, H * 0.06);

    for (const i of this.order) {
      const d = this.dots[i];
      const [r, g, b] = (on ? frame[i] : undefined) ?? [0, 0, 0];
      const lit = r + g + b > 12;
      const depthFade = 0.5 + 0.5 * (d.depth + 1) / 2;
      if (lit) {
        const glow = ctx.createRadialGradient(d.x, d.y, 0, d.x, d.y, d.r * 3.4);
        glow.addColorStop(0, `rgba(${r},${g},${b},${0.6 * bright * depthFade})`);
        glow.addColorStop(1, `rgba(${r},${g},${b},0)`);
        ctx.fillStyle = glow;
        ctx.beginPath(); ctx.arc(d.x, d.y, d.r * 3.4, 0, Math.PI * 2); ctx.fill();
        ctx.fillStyle = `rgba(${Math.min(255, r + 70)},${Math.min(255, g + 70)},${Math.min(255, b + 70)},${depthFade})`;
      } else {
        ctx.fillStyle = `rgba(255,255,255,${0.07 * depthFade})`;
      }
      ctx.beginPath(); ctx.arc(d.x, d.y, d.r, 0, Math.PI * 2); ctx.fill();
    }
  }
}
