import { Component, computed, effect, inject, signal } from '@angular/core';
import { RgbService } from '../../services/rgb.service';

/**
 * Edit how many lights are on the strand and how they're wrapped around the
 * tree (lights per wrap, bottom to top). Saved on the Pi; the strand is
 * reconfigured live.
 */
@Component({
  selector: 'app-tree-setup',
  standalone: true,
  template: `
    @if (!open()) {
      <button type="button" class="btn quiet small opener" (click)="start()">
        Set up tree · {{ svc.config()?.numPixels }} lights, {{ svc.config()?.rings?.length }} wraps
      </button>
    } @else {
      <form class="setup" (submit)="$event.preventDefault(); save()">
        <div class="field">
          <label for="count">Lights on the strand</label>
          <input id="count" type="number" min="1" max="5000" [value]="count()" (input)="setCount($event)">
        </div>

        <div class="field">
          <div class="label-row">
            <label>Lights per wrap, bottom to top</label>
            <button type="button" class="btn quiet small" (click)="even()">Even cone</button>
          </div>
          <ol class="wraps">
            @for (r of rings(); track $index) {
              <li>
                <span class="muted small">{{ $index + 1 }}</span>
                <input type="number" min="1" [value]="r" (input)="setRing($index, $event)" [attr.aria-label]="'Wrap ' + ($index + 1)">
                @if (rings().length > 1) {
                  <button type="button" class="x" (click)="removeRing($index)" aria-label="Remove wrap">×</button>
                }
              </li>
            }
          </ol>
          <div class="row">
            <button type="button" class="btn quiet small" (click)="addRing()">+ Add a wrap on top</button>
            <span class="spacer"></span>
            <span class="small" [class.bad]="total() !== count()" [class.muted]="total() === count()">
              {{ total() }} of {{ count() }} lights placed
            </span>
          </div>
        </div>

        <div class="row">
          <button type="submit" class="btn primary" [disabled]="total() !== count() || saving()">Save</button>
          <button type="button" class="btn quiet" (click)="open.set(false)">Cancel</button>
        </div>
        <p class="muted small">Count the lights on each wrap starting at the bottom. Close enough is fine — the spiral, climb and snow effects just need to know which lights sit at the same height.</p>
      </form>
    }
  `,
  styles: [`
    :host { display: block; }
    .opener { margin-left: -8px; }
    .setup { display: grid; gap: 14px; }
    .field { display: grid; gap: 6px; }
    label { font-size: 0.9rem; }
    .label-row { display: flex; justify-content: space-between; align-items: center; }
    input[type="number"] {
      font: inherit; color: var(--ink); background: transparent; border: 0; border-bottom: 1px solid var(--line-strong);
      padding: 4px 2px; width: 72px; border-radius: 0;
      &:focus { outline: none; border-bottom-color: var(--ink); }
    }
    .wraps { list-style: none; margin: 0; padding: 0; display: flex; flex-wrap: wrap; gap: 6px 14px; }
    .wraps li { display: flex; align-items: center; gap: 6px; }
    .x { border: 0; background: transparent; color: var(--ink-3); cursor: pointer; font-size: 1rem; padding: 2px 4px; &:hover { color: var(--red); } }
    .bad { color: var(--red); }
  `],
})
export class TreeSetupComponent {
  svc = inject(RgbService);
  open = signal(false);
  saving = signal(false);
  count = signal(100);
  rings = signal<number[]>([]);
  total = computed(() => this.rings().reduce((a, b) => a + (b || 0), 0));

  start(): void {
    const cfg = this.svc.config();
    this.count.set(cfg?.numPixels ?? 100);
    this.rings.set([...(cfg?.rings ?? [100])]);
    this.open.set(true);
  }

  setCount(e: Event): void {
    this.count.set(Math.max(1, Math.floor(Number((e.target as HTMLInputElement).value) || 0)));
  }

  setRing(i: number, e: Event): void {
    const v = Math.max(1, Math.floor(Number((e.target as HTMLInputElement).value) || 0));
    this.rings.update(r => r.map((x, k) => (k === i ? v : x)));
  }

  addRing(): void {
    this.rings.update(r => [...r, Math.max(1, Math.round((r[r.length - 1] ?? 10) * 0.7))]);
  }

  removeRing(i: number): void {
    this.rings.update(r => r.filter((_, k) => k !== i));
  }

  /** Distribute the count over the current number of wraps as a tapering cone. */
  even(): void {
    const n = this.count();
    const wraps = Math.max(1, this.rings().length);
    const weights = Array.from({ length: wraps }, (_, i) => wraps - i + 0.6);
    const sum = weights.reduce((a, b) => a + b, 0);
    const out = weights.map(w => Math.max(1, Math.floor((w / sum) * n)));
    let rem = n - out.reduce((a, b) => a + b, 0);
    for (let i = 0; rem > 0; i = (i + 1) % wraps, rem--) { out[i]++; }
    for (let i = wraps - 1; rem < 0 && i >= 0; i--) { if (out[i] > 1) { out[i]--; rem++; } }
    this.rings.set(out);
  }

  async save(): Promise<void> {
    this.saving.set(true);
    const ok = await this.svc.setLayout(this.count(), this.rings());
    this.saving.set(false);
    if (ok) { this.open.set(false); }
  }
}
