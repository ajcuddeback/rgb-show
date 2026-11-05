import { Component, inject } from '@angular/core';
import { RgbService } from '../../services/rgb.service';

@Component({
  selector: 'app-power-toggle',
  standalone: true,
  template: `
    <label class="power" [class.on]="svc.power()">
      <span class="status">
        <span class="led"></span>
        <span class="text">{{ svc.power() ? (svc.currentDef()?.label ?? 'On') : 'Off' }}</span>
      </span>
      <span class="toggle">
        <input type="checkbox" [checked]="svc.power()" (change)="toggle($event)" aria-label="Power">
        <span class="track"></span>
      </span>
    </label>
  `,
  styles: [`
    .power {
      display: inline-flex; align-items: center; gap: 12px;
      padding: 8px 10px 8px 14px; border-radius: 999px;
      background: rgba(0,0,0,0.3); border: 1px solid var(--border-strong); cursor: pointer;
      user-select: none;
    }
    .status { display: inline-flex; align-items: center; gap: 8px; font-weight: 600; font-size: 0.9rem; white-space: nowrap; max-width: 40vw; overflow: hidden; text-overflow: ellipsis; }
    .led { width: 10px; height: 10px; border-radius: 50%; background: #555; flex: 0 0 auto; }
    .on .led { background: var(--green); animation: pulse-ring 1.6s ease-out infinite; }
    @media (max-width: 600px) {
      .power { padding: 8px 10px; gap: 8px; }
      .status .text { display: none; }
    }
  `],
})
export class PowerToggleComponent {
  svc = inject(RgbService);

  toggle(event: Event): void {
    const on = (event.target as HTMLInputElement).checked;
    void this.svc.setPower(on);
  }
}
