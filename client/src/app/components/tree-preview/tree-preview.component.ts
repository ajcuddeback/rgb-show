import { AfterViewInit, Component, ElementRef, OnDestroy, ViewChild, effect, inject } from '@angular/core';
import { RgbService } from '../../services/rgb.service';
import { RGB } from '../../models';

interface Dot { x: number; y: number; depth: number; r: number; }

/**
 * Live mirror of the tree: polls /api/frame and draws the pixels on a cone
 * using the same ring geometry the server uses.
 */
@Component({
  selector: 'app-tree-preview',
  standalone: true,
  template: `
    <canvas #canvas></canvas>
    @if (svc.config()?.simulated) { <p class="muted small sim">Simulated — no strand connected</p> }
  `,
  styles: [`
    :host { display: block; }
    canvas { width: 100%; max-width: 280px; aspect-ratio: 3 / 4; display: block; margin: 0 auto; }
    .sim { text-align: center; margin-top: 4px; }
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
  private visible = () => document.visibilityState === 'visible';

  constructor() {
    effect(() => {
      const cfg = this.svc.config();
      if (!cfg) { return; }
      const key = cfg.rings.join(',');
      if (key !== this.ringsKey) {
        this.ringsKey = key;
        this.layout(cfg.rings);
        this.draw();
      }
    });
    effect(() => {
      // When powered off we don't need to poll; draw a dark tree once.
      if (!this.svc.power()) {
        this.frame = [];
        this.draw();
      }
    });
  }

  ngAfterViewInit(): void {
    const canvas = this.canvasRef.nativeElement;
    const ro = new ResizeObserver(() => this.resize());
    ro.observe(canvas);
    this.resize();
    this.timer = setInterval(() => this.poll(), 125);
  }

  ngOnDestroy(): void {
    if (this.timer) { clearInterval(this.timer); }
  }

  private resize(): void {
    const canvas = this.canvasRef?.nativeElement;
    if (!canvas) { return; }
    const dpr = Math.min(2, window.devicePixelRatio || 1);
    const w = canvas.clientWidth || 300;
    const h = canvas.clientHeight || 400;
    canvas.width = Math.round(w * dpr);
    canvas.height = Math.round(h * dpr);
    const cfg = this.svc.config();
    if (cfg) { this.layout(cfg.rings); }
    this.draw();
  }

  private layout(rings: number[]): void {
    const canvas = this.canvasRef?.nativeElement;
    if (!canvas) { return; }
    const W = canvas.width, H = canvas.height;
    const top = H * 0.09, base = H * 0.86, cx = W / 2, R = W * 0.42;
    const total = rings.reduce((a, b) => a + b, 0) || 1;
    const dots: Dot[] = [];
    const numRings = rings.length;
    let idx = 0;
    for (let r = 0; r < numRings; r++) {
      for (let k = 0; k < rings[r]; k++) {
        const frac = k / rings[r];
        let h = (r + frac) / numRings;
        if (numRings === 1) { h = frac; }
        const hn = h / ((numRings - 1 + (rings[numRings - 1] - 1) / rings[numRings - 1]) / numRings || 1);
        const theta = frac * Math.PI * 2 - Math.PI / 2;
        const radius = R * (1 - Math.min(1, hn) * 0.92) + W * 0.02;
        const depth = Math.sin(theta); // +1 = front, -1 = back
        dots.push({
          x: cx + radius * Math.cos(theta),
          y: base - Math.min(1, hn) * (base - top) + radius * 0.26 * depth,
          depth,
          r: W * (0.012 + 0.006 * (depth + 1) / 2) * (total > 150 ? 0.7 : 1),
        });
        idx++;
      }
    }
    this.dots = dots;
    this.order = dots.map((_, i) => i).sort((a, b) => dots[a].depth - dots[b].depth);
  }

  private poll(): void {
    if (!this.svc.power() || this.inflight || !this.visible()) { return; }
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

    // Tree silhouette, colored from the theme so it works on paper and dark
    const css = getComputedStyle(document.documentElement);
    const treeColor = css.getPropertyValue('--tree').trim() || '#2a4d33';
    const trunkColor = css.getPropertyValue('--trunk').trim() || '#6b4a2c';
    const dark = matchMedia('(prefers-color-scheme: dark)').matches;
    const top = H * 0.07, base = H * 0.88, cx = W / 2, R = W * 0.46;
    ctx.fillStyle = treeColor;
    ctx.beginPath();
    ctx.moveTo(cx, top);
    ctx.lineTo(cx + R, base);
    ctx.quadraticCurveTo(cx, base + H * 0.04, cx - R, base);
    ctx.closePath();
    ctx.fill();
    ctx.fillStyle = trunkColor;
    ctx.fillRect(cx - W * 0.05, base + H * 0.015, W * 0.1, H * 0.07);

    const frame = this.frame;
    const bright = 0.45 + 0.55 * Math.sqrt(this.svc.brightness());
    const on = this.svc.power() && frame.length > 0;

    for (const i of this.order) {
      const d = this.dots[i];
      const px = on ? frame[i] : undefined;
      const [r, g, b] = px ?? [0, 0, 0];
      const lit = r + g + b > 12;
      const depthFade = 0.55 + 0.45 * (d.depth + 1) / 2;
      if (lit) {
        const glow = ctx.createRadialGradient(d.x, d.y, 0, d.x, d.y, d.r * 3.2);
        glow.addColorStop(0, `rgba(${r},${g},${b},${0.55 * bright * depthFade})`);
        glow.addColorStop(1, `rgba(${r},${g},${b},0)`);
        ctx.fillStyle = glow;
        ctx.beginPath(); ctx.arc(d.x, d.y, d.r * 3.2, 0, Math.PI * 2); ctx.fill();
        ctx.fillStyle = `rgba(${Math.min(255, r + 60)},${Math.min(255, g + 60)},${Math.min(255, b + 60)},${depthFade})`;
      } else {
        ctx.fillStyle = dark ? `rgba(255,255,255,${0.08 * depthFade})` : `rgba(0,0,0,${0.18 * depthFade})`;
      }
      ctx.beginPath(); ctx.arc(d.x, d.y, d.r, 0, Math.PI * 2); ctx.fill();
      if (lit) {
        ctx.lineWidth = Math.max(1, d.r * 0.25);
        ctx.strokeStyle = `rgba(0,0,0,${0.35 * depthFade})`;
        ctx.stroke();
      }
    }
  }
}
