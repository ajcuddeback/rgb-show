import { Component, computed, inject, signal } from '@angular/core';
import { RgbService } from '../../services/rgb.service';
import { PALETTES, ParamSchema, hexToRgb, randomHex, rgbToHex } from '../../models';

@Component({
  selector: 'app-param-editor',
  standalone: true,
  templateUrl: './param-editor.component.html',
  styleUrls: ['./param-editor.component.scss'],
})
export class ParamEditorComponent {
  svc = inject(RgbService);
  palettes = PALETTES;

  def = this.svc.selectedDef;
  params = this.svc.selectedParams;
  playing = this.svc.selectedIsPlaying;

  presetName = signal('');
  savingPreset = signal(false);

  hasColorsParam = computed(() => (this.def()?.params ?? []).some(p => p.type === 'colors'));

  // ------------------------------------------------------------ value access
  num(p: ParamSchema): number {
    const v = Number(this.params()[p.key]);
    return Number.isFinite(v) ? v : Number(p.default ?? 0);
  }

  str(p: ParamSchema): string {
    return String(this.params()[p.key] ?? p.default ?? '');
  }

  bool(p: ParamSchema): boolean {
    return Boolean(this.params()[p.key] ?? p.default);
  }

  hex(p: ParamSchema): string {
    return rgbToHex(this.params()[p.key] ?? p.default);
  }

  hexList(p: ParamSchema): string[] {
    const v = this.params()[p.key] ?? p.default;
    return Array.isArray(v) ? v.map(rgbToHex) : [];
  }

  fill(p: ParamSchema): number {
    const min = p.min ?? 0, max = p.max ?? 100;
    return max > min ? Math.round(((this.num(p) - min) / (max - min)) * 100) : 0;
  }

  format(p: ParamSchema): string {
    const v = this.num(p);
    const step = p.step ?? 1;
    const decimals = step >= 1 ? 0 : Math.min(2, Math.ceil(-Math.log10(step)));
    return v.toFixed(decimals);
  }

  // ---------------------------------------------------------------- setters
  setNumber(p: ParamSchema, event: Event): void {
    this.svc.setParam(p.key, Number((event.target as HTMLInputElement).value));
  }

  setSelect(p: ParamSchema, value: string): void {
    this.svc.setParam(p.key, value);
  }

  setBool(p: ParamSchema, event: Event): void {
    this.svc.setParam(p.key, (event.target as HTMLInputElement).checked);
  }

  setColor(p: ParamSchema, event: Event): void {
    this.svc.setParam(p.key, hexToRgb((event.target as HTMLInputElement).value));
  }

  setColorAt(p: ParamSchema, index: number, event: Event): void {
    const list = this.hexList(p);
    list[index] = (event.target as HTMLInputElement).value;
    this.svc.setParam(p.key, list.map(hexToRgb));
  }

  addColor(p: ParamSchema): void {
    const list = this.hexList(p);
    if (list.length >= (p.max_items ?? 8)) { return; }
    this.svc.setParam(p.key, [...list, randomHex()].map(hexToRgb));
  }

  removeColor(p: ParamSchema, index: number): void {
    const list = this.hexList(p);
    if (list.length <= (p.min_items ?? 1)) { return; }
    list.splice(index, 1);
    this.svc.setParam(p.key, list.map(hexToRgb));
  }

  applyPalette(p: ParamSchema, colors: string[]): void {
    this.svc.setParam(p.key, colors.slice(0, p.max_items ?? 8).map(hexToRgb));
  }

  shuffle(p: ParamSchema): void {
    const list = this.hexList(p);
    for (let i = list.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [list[i], list[j]] = [list[j], list[i]];
    }
    this.svc.setParam(p.key, list.map(hexToRgb));
  }

  randomize(p: ParamSchema): void {
    const count = Math.max(p.min_items ?? 1, this.hexList(p).length || 3);
    this.svc.setParam(p.key, Array.from({ length: count }, () => hexToRgb(randomHex())));
  }

  paletteActive(p: ParamSchema, colors: string[]): boolean {
    const cur = this.hexList(p);
    return cur.length === colors.length && cur.every((c, i) => c.toLowerCase() === colors[i].toLowerCase());
  }

  // ---------------------------------------------------------------- actions
  start(): void {
    const name = this.def()?.name;
    if (name) { void this.svc.start(name, this.params()); }
  }

  reset(): void {
    this.svc.resetParams();
  }

  async savePreset(): Promise<void> {
    const name = this.presetName().trim() || `${this.def()?.label ?? 'Preset'}`;
    await this.svc.savePreset(name);
    this.presetName.set('');
    this.savingPreset.set(false);
  }

  onPresetNameInput(event: Event): void {
    this.presetName.set((event.target as HTMLInputElement).value);
  }
}
