import { Component, inject } from '@angular/core';
import { RgbService } from '../../services/rgb.service';
import { Preset, rgbToHex } from '../../models';

@Component({
  selector: 'app-presets-panel',
  standalone: true,
  template: `
    @if (svc.presets().length === 0) {
      <p class="muted small">Nothing saved yet. Dial in an animation and hit “Save preset”.</p>
    } @else {
      <ul>
        @for (p of svc.presets(); track p.id) {
          <li [class.active]="isActive(p)">
            <button type="button" class="apply" (click)="apply(p)">
              <span class="dots" aria-hidden="true">
                @for (c of colorsOf(p); track $index) { <span class="dot" [style.background]="c"></span> }
              </span>
              <span class="text">
                <span class="name">{{ p.name }}</span>
                <span class="muted small">{{ labelOf(p) }}</span>
              </span>
            </button>
            <button type="button" class="remove" (click)="remove(p)" aria-label="Delete preset">
              <svg viewBox="0 0 24 24" width="16" height="16"><path d="M6 6l12 12M18 6L6 18" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>
            </button>
          </li>
        }
      </ul>
    }
  `,
  styles: [`
    ul { list-style: none; margin: 0; padding: 0; display: grid; gap: 4px; }
    li { display: flex; align-items: center; gap: 2px; border-radius: 12px; }
    li.active { background: var(--surface-2); }
    li.active .name { color: var(--green); }
    .apply {
      flex: 1; display: flex; align-items: center; gap: 12px; text-align: left; min-width: 0; cursor: pointer;
      background: transparent; border: 0; padding: 8px 10px; border-radius: 12px;
      &:hover { background: var(--surface-2); }
    }
    .dots { display: inline-flex; flex: 0 0 auto; }
    .dot { width: 14px; height: 14px; border-radius: 50%; margin-right: -5px; box-shadow: 0 0 0 2px var(--surface); }
    .text { display: flex; flex-direction: column; min-width: 0; line-height: 1.25; }
    .name { font-weight: 500; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
    .remove { border: 0; background: transparent; color: var(--text-3); padding: 8px; cursor: pointer; border-radius: 8px; display: inline-flex; &:hover { color: var(--red); background: var(--surface-2); } }
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
  labelOf(p: Preset): string { return this.svc.byName().get(p.animation)?.label ?? p.animation; }
  colorsOf(p: Preset): string[] {
    const params = p.params ?? {};
    for (const v of Object.values(params)) {
      if (Array.isArray(v) && v.length && Array.isArray(v[0])) { return (v as number[][]).slice(0, 5).map(rgbToHex); }
    }
    for (const v of Object.values(params)) {
      if (Array.isArray(v) && v.length === 3 && typeof v[0] === 'number') { return [rgbToHex(v)]; }
    }
    return (this.svc.byName().get(p.animation)?.preview ?? []).slice(0, 5).map(rgbToHex);
  }
}
