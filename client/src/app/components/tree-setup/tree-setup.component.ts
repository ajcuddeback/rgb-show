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
      <div class="card setup-card">
        <div class="summary">
          <span class="t">Tree setup</span>
          <span class="muted small">
            {{ svc.config()?.numPixels }} lights ·
            @if (svc.config()?.source === 'camera') { mapped with camera } @else { {{ svc.config()?.rings?.length }} wraps (estimated) }
          </span>
        </div>
        <div class="actions">
          <button type="button" class="btn sm primary map" (click)="svc.mapperOpen.set(true)">
            <svg viewBox="0 0 24 24"><path d="M4 8a2 2 0 0 1 2-2h2l1.5-2h5L16 6h2a2 2 0 0 1 2 2v9a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2z" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round"/><circle cx="12" cy="12.5" r="3.2" fill="none" stroke="currentColor" stroke-width="1.8"/></svg>
            Map with camera
          </button>
          <button type="button" class="btn sm" (click)="start()">Edit lights &amp; wraps</button>
        </div>
      </div>
    } @else {
      <form class="setup card" (submit)="$event.preventDefault(); save()">
        <h2>Tree setup</h2>
        <div class="field">
          <label for="count">Lights on the strand</label>
          <input id="count" type="number" min="1" max="5000" [value]="count()" (input)="setCount($event)">
        </div>

        <div class="field">
          <div class="label-row">
            <label>Lights per wrap, bottom to top</label>
            <button type="button" class="btn ghost sm" (click)="even()">Even cone</button>
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
            <button type="button" class="btn ghost sm" (click)="addRing()">+ Add a wrap on top</button>
            <span class="spacer"></span>
            <span class="small" [class.bad]="total() !== count()" [class.muted]="total() === count()">
              {{ total() }} of {{ count() }} lights placed
            </span>
          </div>
        </div>

        <div class="row">
          <button type="submit" class="btn primary" [disabled]="total() !== count() || saving()">Save</button>
          <button type="button" class="btn ghost" (click)="open.set(false)">Cancel</button>
        </div>
        <p class="faint small">Count the lights on each wrap starting at the bottom. Close enough is fine — the spiral, climb and snow effects just need to know which lights sit at the same height.</p>
      </form>
    }
  `,
  styles: [`
    :host { display: block; }
    .setup-card { padding: 14px 16px; display: grid; gap: 12px; }
    .summary { display: flex; flex-direction: column; }
    .t { font-weight: 500; }
    .actions { display: flex; gap: 8px; flex-wrap: wrap; }
    .setup { display: grid; gap: 14px; padding: 18px; }
    .field { display: grid; gap: 6px; }
    label { font-size: 0.9rem; font-weight: 500; }
    .label-row { display: flex; justify-content: space-between; align-items: center; }
    input[type="number"] {
      font: inherit; color: var(--text); background: var(--surface-2); border: 1px solid var(--border-2);
      padding: 6px 10px; width: 76px; border-radius: 10px;
      &:focus { outline: none; border-color: var(--accent); }
    }
    .wraps { list-style: none; margin: 0; padding: 0; display: flex; flex-wrap: wrap; gap: 8px 14px; }
    .wraps li { display: flex; align-items: center; gap: 6px; }
    .x { border: 0; background: transparent; color: var(--text-3); cursor: pointer; font-size: 1rem; padding: 2px 4px; &:hover { color: var(--red); } }
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
