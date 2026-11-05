import { Component, inject } from '@angular/core';
import { RgbService } from '../../services/rgb.service';
import { AnimationDef, rgbToHex } from '../../models';

@Component({
  selector: 'app-animation-grid',
  standalone: true,
  templateUrl: './animation-grid.component.html',
  styleUrls: ['./animation-grid.component.scss'],
})
export class AnimationGridComponent {
  svc = inject(RgbService);

  /** Soft, blurred-looking "album art" built from the animation's preview colors. */
  art(def: AnimationDef): string {
    const cs = (def.preview.length ? def.preview : [[90, 90, 100]]).map(rgbToHex);
    if (cs.length === 1) { return `radial-gradient(120% 120% at 30% 25%, ${cs[0]}, ${shade(cs[0])})`; }
    const spots = [['20% 20%'], ['80% 30%'], ['30% 80%'], ['85% 85%'], ['55% 50%'], ['10% 60%'], ['70% 10%'], ['50% 95%']];
    const layers = cs.slice(0, 6).map((c, i) => `radial-gradient(70% 70% at ${spots[i % spots.length][0]}, ${c} 0%, transparent 70%)`);
    return `${layers.join(', ')}, ${cs[cs.length - 1]}`;
  }
  isPlaying(def: AnimationDef): boolean { return this.svc.power() && this.svc.current() === def.name; }
  isSelected(def: AnimationDef): boolean { return this.svc.selected() === def.name; }
  play(def: AnimationDef): void { void this.svc.start(def.name, undefined, true); }
}

function shade(hex: string): string {
  const n = parseInt(hex.slice(1), 16);
  const f = (v: number) => Math.round(v * 0.45);
  return `rgb(${f(n >> 16)}, ${f((n >> 8) & 255)}, ${f(n & 255)})`;
}
