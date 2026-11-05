import { Component, inject } from '@angular/core';
import { RgbService } from '../../services/rgb.service';

@Component({
  selector: 'app-power-toggle',
  standalone: true,
  template: `
    <button type="button" class="power" [class.on]="svc.power()" (click)="toggle()"
            [attr.aria-pressed]="svc.power()" [attr.aria-label]="svc.power() ? 'Turn lights off' : 'Turn lights on'">
      <svg viewBox="0 0 24 24" width="22" height="22" aria-hidden="true">
        <path d="M12 3v9" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
        <path d="M7.5 6.2a7 7 0 1 0 9 0" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
      </svg>
    </button>
  `,
  styles: [`
    .power {
      width: 48px; height: 48px; border-radius: 50%; cursor: pointer; flex: 0 0 auto;
      border: 1px solid var(--line-strong); background: transparent; color: var(--ink-2);
      display: inline-flex; align-items: center; justify-content: center; transition: all 0.15s;
      &:hover { color: var(--ink); }
      &.on { background: var(--red); border-color: var(--red); color: #fff; }
      &:focus-visible { outline: none; box-shadow: 0 0 0 4px var(--red-soft); }
    }
  `],
})
export class PowerToggleComponent {
  svc = inject(RgbService);
  toggle(): void { void this.svc.setPower(!this.svc.power()); }
}
