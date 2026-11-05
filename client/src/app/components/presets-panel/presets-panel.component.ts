import { Component, inject } from '@angular/core';
import { RgbService } from '../../services/rgb.service';
import { Preset, rgbToHex } from '../../models';

@Component({
  selector: 'app-presets-panel',
  standalone: true,
  template: `
    @if (svc.presets().length === 0) {
      <p class="muted empty">No presets yet. Dial in an animation you love and hit “Save as preset”.</p>
    } @else {
      <ul class="list">
        @for (p of svc.presets(); track p.id) {
          <li [class.active]="isActive(p)">
            <button type="button" class="apply" (click)="apply(p)">
              <span class="dots">
                @for (c of colorsOf(p); track $index) { <span class="dot" [style.background]="c"></span> }
              </span>
              <span class="text">
                <span class="name">{{ p.name }}</span>
                <span class="muted sub">{{ labelOf(p) }}</span>
              </span>
            </button>
            <button type="button" class="btn ghost icon" (click)="remove(p)" aria-label="Delete preset">🗑</button>
          </li>
        }
      </ul>
    }
  `,
  styles: [`
    .empty { font-size: 0.85rem; }
    .list { list-style: none; margin: 0; padding: 0; display: grid; gap: 6px; }
    li { display: flex; align-items: center; gap: 4px; border-radius: var(--radius-sm); border: 1px solid transparent; }
    li.active { border-color: rgba(61, 220, 132, 0.5); background: rgba(61, 220, 132, 0.06); }
    .apply {
      flex: 1; display: flex; align-items: center; gap: 10px; text-align: left; min-width: 0;
      background: transparent; border: none; color: var(--text); padding: 8px; border-radius: var(--radius-sm); cursor: pointer;
      &:hover { background: rgba(255,255,255,0.05); }
    }
    .dots { display: inline-flex; gap: 2px; flex: 0 0 auto; }
    .dot { width: 10px; height: 10px; border-radius: 50%; box-shadow: inset 0 0 0 1px rgba(0,0,0,0.3); }
    .text { display: flex; flex-direction: column; min-width: 0; }
    .name { font-weight: 600; font-size: 0.9rem; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
    .sub { font-size: 0.75rem; }
  `],
})
export class PresetsPanelComponent {
  svc = inject(RgbService);

  apply(p: Preset): void { void this.svc.applyPreset(p.id); }
  remove(p: Preset): void { void this.svc.deletePreset(p.id); }

  isActive(p: Preset): boolean {
    return this.svc.power() && this.svc.current() === p.animation
      && JSON.stringify(this.svc.state()?.params) === JSON.stringify(p.params);
  }

  labelOf(p: Preset): string {
    return this.svc.byName().get(p.animation)?.label ?? p.animation;
  }

  colorsOf(p: Preset): string[] {
    const params = p.params ?? {};
    for (const v of Object.values(params)) {
      if (Array.isArray(v) && v.length && Array.isArray(v[0])) { return (v as number[][]).slice(0, 6).map(rgbToHex); }
    }
    for (const v of Object.values(params)) {
      if (Array.isArray(v) && v.length === 3 && typeof v[0] === 'number') { return [rgbToHex(v)]; }
    }
    return this.svc.byName().get(p.animation)?.preview.map(rgbToHex) ?? [];
  }
}
