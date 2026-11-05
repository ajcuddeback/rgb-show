import { Component, computed, inject } from '@angular/core';
import { RgbService } from '../../services/rgb.service';

@Component({
  selector: 'app-global-controls',
  standalone: true,
  template: `
    <div class="control">
      <div class="label"><label for="brightness">Brightness</label><span class="muted">{{ brightnessPct() }}%</span></div>
      <input id="brightness" type="range" min="1" max="100" step="1" [value]="brightnessPct()" (input)="onBrightness($event)">
    </div>
    <div class="control">
      <div class="label"><label for="speed">Speed</label><span class="muted">{{ speedLabel() }}</span></div>
      <input id="speed" type="range" min="0" max="100" step="1" [value]="speedSlider()" (input)="onSpeed($event)">
    </div>
  `,
  styles: [`
    :host { display: grid; gap: 10px; }
    .label { display: flex; justify-content: space-between; font-size: 0.9rem; }
    .label span { font-variant-numeric: tabular-nums; }
  `],
})
export class GlobalControlsComponent {
  svc = inject(RgbService);
  brightnessPct = computed(() => Math.round(this.svc.brightness() * 100));
  speedSlider = computed(() => Math.round((Math.log2(this.svc.speed()) + 2) / 4 * 100));
  speedLabel = computed(() => `${this.svc.speed().toFixed(2).replace(/\.?0+$/, '')}×`);

  onBrightness(event: Event): void {
    this.svc.setBrightness(Number((event.target as HTMLInputElement).value) / 100);
  }
  onSpeed(event: Event): void {
    const v = Number((event.target as HTMLInputElement).value);
    this.svc.setSpeed(Math.round(Math.pow(2, (v / 100) * 4 - 2) * 100) / 100);
  }
}
