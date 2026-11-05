import { Injectable, computed, inject, signal } from '@angular/core';
import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { Subject, catchError, debounceTime, firstValueFrom, forkJoin, map, of, switchMap } from 'rxjs';
import { AnimationDef, Params, Preset, RgbState, RGB } from '../models';

const CATEGORY_ORDER = ['Static', 'Motion', 'Sparkle', 'Nature', 'Showpiece'];

@Injectable({ providedIn: 'root' })
export class RgbService {
  private http = inject(HttpClient);

  readonly state = signal<RgbState | null>(null);
  readonly animations = signal<AnimationDef[]>([]);
  readonly presets = signal<Preset[]>([]);
  readonly error = signal<string | null>(null);
  readonly offline = signal(false);
  readonly loading = signal(true);

  /** Animation currently shown in the editor (not necessarily the one playing). */
  readonly selected = signal<string | null>(null);
  /** Last-used params per animation so switching back keeps your tweaks. */
  readonly drafts = signal<Record<string, Params>>({});
  /** Bumps every time the user taps an animation tile (UI uses it to open the settings sheet). */
  readonly lastTap = signal(0);

  readonly power = computed(() => this.state()?.power ?? false);
  readonly current = computed(() => this.state()?.animation ?? null);
  readonly config = computed(() => this.state()?.config ?? null);
  readonly brightness = computed(() => this.state()?.brightness ?? 0.1);
  readonly speed = computed(() => this.state()?.speed ?? 1);

  readonly byName = computed(() => new Map(this.animations().map(a => [a.name, a])));
  readonly selectedDef = computed(() => this.byName().get(this.selected() ?? '') ?? null);
  readonly currentDef = computed(() => this.byName().get(this.current() ?? '') ?? null);
  readonly selectedIsPlaying = computed(() => !!this.selected() && this.selected() === this.current() && this.power());
  readonly selectedParams = computed<Params>(() => {
    const name = this.selected();
    if (!name) { return {}; }
    return this.drafts()[name] ?? this.defaultsFor(name);
  });
  readonly categories = computed(() => {
    const groups = new Map<string, AnimationDef[]>();
    for (const a of this.animations()) {
      groups.set(a.category, [...(groups.get(a.category) ?? []), a]);
    }
    return [...groups.entries()]
      .sort((a, b) => CATEGORY_ORDER.indexOf(a[0]) - CATEGORY_ORDER.indexOf(b[0]))
      .map(([name, items]) => ({ name, items }));
  });

  private paramPatch$ = new Subject<Params>();
  private brightness$ = new Subject<number>();
  private speed$ = new Subject<number>();
  private errorTimer: ReturnType<typeof setTimeout> | null = null;

  constructor() {
    this.paramPatch$.pipe(
      debounceTime(120),
      switchMap(params => this.http.patch<RgbState>('/api/params', { params }).pipe(catchError(e => this.fail(e)))),
    ).subscribe(s => this.applyState(s, false));

    this.brightness$.pipe(
      debounceTime(80),
      switchMap(brightness => this.http.post<RgbState>('/api/brightness', { brightness }).pipe(catchError(e => this.fail(e)))),
    ).subscribe(s => this.applyState(s, false));

    this.speed$.pipe(
      debounceTime(80),
      switchMap(speed => this.http.post<RgbState>('/api/speed', { speed }).pipe(catchError(e => this.fail(e)))),
    ).subscribe(s => this.applyState(s, false));
  }

  // ------------------------------------------------------------------ loading
  async load(): Promise<void> {
    try {
      const { state, animations, presets } = await firstValueFrom(forkJoin({
        state: this.http.get<RgbState>('/api/state'),
        animations: this.http.get<{ animations: AnimationDef[] }>('/api/animations'),
        presets: this.http.get<{ presets: Preset[] }>('/api/presets'),
      }));
      this.animations.set(animations.animations);
      this.presets.set(presets.presets);
      this.applyState(state, true);
      if (!this.selected()) {
        this.selected.set(state.animation ?? animations.animations[0]?.name ?? null);
      }
      this.offline.set(false);
    } catch (e) {
      this.offline.set(true);
      this.fail(e as HttpErrorResponse);
    } finally {
      this.loading.set(false);
    }
  }

  async refreshState(): Promise<void> {
    try {
      const s = await firstValueFrom(this.http.get<RgbState>('/api/state'));
      this.applyState(s, false);
      this.offline.set(false);
    } catch {
      this.offline.set(true);
    }
  }

  getFrame() {
    return this.http.get<{ n: number; hex: string; brightness: number }>('/api/frame').pipe(
      map(res => {
        const pixels: RGB[] = new Array(res.n);
        for (let i = 0; i < res.n; i++) {
          const o = i * 6;
          pixels[i] = [parseInt(res.hex.slice(o, o + 2), 16), parseInt(res.hex.slice(o + 2, o + 4), 16), parseInt(res.hex.slice(o + 4, o + 6), 16)];
        }
        return { pixels, brightness: res.brightness };
      }),
    );
  }

  // ----------------------------------------------------------------- actions
  select(name: string): void {
    this.selected.set(name);
  }

  async start(name: string, params?: Params, fromTap = false): Promise<void> {
    const p = params ?? this.drafts()[name] ?? this.defaultsFor(name);
    this.selected.set(name);
    if (fromTap) { this.lastTap.set(Date.now()); }
    this.setDraft(name, p);
    await this.post(`/api/animations/${name}/start`, { params: p }, true);
  }

  setParam(key: string, value: unknown): void {
    const name = this.selected();
    if (!name) { return; }
    const next = { ...this.selectedParams(), [key]: value };
    this.setDraft(name, next);
    if (this.selectedIsPlaying()) {
      this.paramPatch$.next(next);
    }
  }

  resetParams(): void {
    const name = this.selected();
    if (!name) { return; }
    const defaults = this.defaultsFor(name);
    this.setDraft(name, defaults);
    if (this.selectedIsPlaying()) {
      this.paramPatch$.next(defaults);
    }
  }

  setBrightness(value: number): void {
    this.patchLocal({ brightness: value });
    this.brightness$.next(value);
  }

  setSpeed(value: number): void {
    this.patchLocal({ speed: value });
    this.speed$.next(value);
  }

  async setPower(on: boolean): Promise<void> {
    this.patchLocal({ power: on });
    await this.post('/api/power', { on }, true);
  }

  async setLayout(numPixels: number, rings: number[]): Promise<boolean> {
    try {
      const s = await firstValueFrom(this.http.put<RgbState>('/api/layout', { numPixels, rings }));
      this.applyState(s, false);
      return true;
    } catch (e) {
      this.fail(e as HttpErrorResponse);
      return false;
    }
  }

  // ----------------------------------------------------------------- presets
  async savePreset(name: string): Promise<void> {
    const animation = this.selected();
    if (!animation) { return; }
    try {
      const preset = await firstValueFrom(this.http.post<Preset>('/api/presets', {
        name, animation, params: this.selectedParams(), includeSpeed: true,
      }));
      this.presets.update(list => [...list, preset]);
    } catch (e) {
      this.fail(e as HttpErrorResponse);
    }
  }

  async applyPreset(id: string): Promise<void> {
    const s = await this.post(`/api/presets/${id}/apply`, {}, true);
    if (s?.animation) { this.selected.set(s.animation); }
  }

  async deletePreset(id: string): Promise<void> {
    try {
      await firstValueFrom(this.http.delete(`/api/presets/${id}`));
      this.presets.update(list => list.filter(p => p.id !== id));
    } catch (e) {
      this.fail(e as HttpErrorResponse);
    }
  }

  // ----------------------------------------------------------------- helpers
  defaultsFor(name: string): Params {
    const def = this.byName().get(name);
    const out: Params = {};
    for (const p of def?.params ?? []) {
      out[p.key] = p.default;
    }
    return out;
  }

  dismissError(): void {
    this.error.set(null);
  }

  private setDraft(name: string, params: Params): void {
    this.drafts.update(d => ({ ...d, [name]: params }));
  }

  private patchLocal(partial: Partial<RgbState>): void {
    const s = this.state();
    if (s) { this.state.set({ ...s, ...partial }); }
  }

  private async post(url: string, body: unknown, syncDraft: boolean): Promise<RgbState | null> {
    try {
      const s = await firstValueFrom(this.http.post<RgbState>(url, body));
      this.applyState(s, syncDraft);
      return s;
    } catch (e) {
      this.fail(e as HttpErrorResponse);
      await this.refreshState();
      return null;
    }
  }

  private applyState(s: RgbState | null, syncDraft: boolean): void {
    if (!s) { return; }
    this.state.set(s);
    this.offline.set(false);
    if (syncDraft && s.animation) {
      this.setDraft(s.animation, s.params);
    }
  }

  private fail(e: HttpErrorResponse | Error) {
    const http = e as HttpErrorResponse;
    const msg = http?.status === 0
      ? 'Cannot reach the tree. Is the server running?'
      : (http?.error?.error ?? http?.message ?? 'Something went wrong');
    this.error.set(msg);
    if (http?.status === 0) { this.offline.set(true); }
    if (this.errorTimer) { clearTimeout(this.errorTimer); }
    this.errorTimer = setTimeout(() => this.error.set(null), 6000);
    return of(null);
  }
}
