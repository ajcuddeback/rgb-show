import { Component, computed, inject, signal } from '@angular/core';
import { DecimalPipe } from '@angular/common';
import { RgbService } from '../../services/rgb.service';

/**
 * Music: pick where the sound comes from, see it live, and sync animations to it.
 */
@Component({
  selector: 'app-music-panel',
  standalone: true,
  imports: [DecimalPipe],
  templateUrl: './music-panel.component.html',
  styleUrls: ['./music-panel.component.scss'],
})
export class MusicPanelComponent {
  svc = inject(RgbService);
  showAdvanced = signal(false);

  audio = this.svc.audio;
  live = this.svc.audioLive;
  on = computed(() => (this.audio()?.source ?? 'off') !== 'off');
  bars = computed(() => {
    const f = this.live();
    return [
      { key: 'bass', label: 'Bass', v: f?.bass ?? 0 },
      { key: 'mid', label: 'Mid', v: f?.mid ?? 0 },
      { key: 'treble', label: 'Treble', v: f?.treble ?? 0 },
    ];
  });
  status = computed(() => {
    const a = this.audio();
    if (!a) { return 'Audio unavailable'; }
    if (a.source === 'off') { return 'Off'; }
    if (a.error) { return a.error; }
    if (a.source === 'spotify' && !a.streaming) { return 'Waiting for Spotify — pick “Christmas Tree” in the app'; }
    const f = this.live();
    if (f?.active && f.bpm) { return `${Math.round(f.bpm)} BPM`; }
    if (a.source === 'spotify') { return 'Connected, paused'; }
    return 'Listening…';
  });

  setSource(e: Event): void { void this.svc.setAudio({ source: (e.target as HTMLSelectElement).value }); }
  setOutput(e: Event): void { void this.svc.setAudio({ output: (e.target as HTMLSelectElement).value }); }
  setSensitivity(e: Event): void { void this.svc.setAudio({ sensitivity: Number((e.target as HTMLInputElement).value) / 100 }); }
  setDemoBpm(e: Event): void { void this.svc.setAudio({ demoBpm: Number((e.target as HTMLInputElement).value) }); }
  toggleSync(): void { void this.svc.setAudio({ sync: !this.audio()?.sync }); }
  refresh(): void { void this.svc.loadAudio(); }
}
