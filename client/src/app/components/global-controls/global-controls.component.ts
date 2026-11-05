import { Component, computed, inject } from '@angular/core';
import { RgbService } from '../../services/rgb.service';

@Component({
  selector: 'app-global-controls',
  standalone: true,
  template: `
    <div class="control">
      <div class="label-row">
        <label for="brightness">Brightness</label>
        <span class="value">{{ brightnessPct() }}%</span>
      </div>
      <input id="brightness" type="range" min="1" max="100" step="1"
             [value]="brightnessPct()" (input)="onBrightness($event)"
             style="--track: linear-gradient(90deg, #222 0%, #ffd166 100%)">
    </div>

    <div class="control">
      <div class="label-row">
        <label for="speed">Speed</label>
        <span class="value">{{ speedLabel() }}</span>
      </div>
      <input id="speed" type="range" min="0" max="100" step="1"
             [value]="speedSlider()" (input)="onSpeed($event)">
      <div class="ticks"><span>slow</span><span>normal</span><span>fast</span></div>
    </div>
  `,
  styles: [`
    :host { display: grid; gap: 14px; }
    .label-row { display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 2px; }
    label { font-weight: 600; font-size: 0.92rem; }
    .value { color: var(--muted); font-variant-numeric: tabular-nums; font-size: 0.85rem; }
    .ticks { display: flex; justify-content: space-between; color: var(--muted); font-size: 0.7rem; margin-top: -4px; }
  `],
})
export class GlobalControlsComponent {
  svc = inject(RgbService);

  brightnessPct = computed(() => Math.round(this.svc.brightness() * 100));
  /** Speed multiplier 0.25x .. 4x on a log scale so "normal" sits in the middle. */
  speedSlider = computed(() => Math.round((Math.log2(this.svc.speed()) + 2) / 4 * 100));
  speedLabel = computed(() => `${this.svc.speed().toFixed(2).replace(/\.?0+$/, '')}×`);

  onBrightness(event: Event): void {
    const pct = Number((event.target as HTMLInputElement).value);
    this.svc.setBrightness(pct / 100);
  }

  onSpeed(event: Event): void {
    const v = Number((event.target as HTMLInputElement).value);
    const mult = Math.pow(2, (v / 100) * 4 - 2);
    this.svc.setSpeed(Math.round(mult * 100) / 100);
  }
}
