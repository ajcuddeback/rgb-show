import { Component, HostListener, OnInit, computed, effect, inject, signal } from '@angular/core';
import { SwUpdate, VersionReadyEvent } from '@angular/service-worker';
import { filter } from 'rxjs';
import { RgbService } from './services/rgb.service';
import { rgbToHex } from './models';
import { GlobalControlsComponent } from './components/global-controls/global-controls.component';
import { TreePreviewComponent } from './components/tree-preview/tree-preview.component';
import { AnimationGridComponent } from './components/animation-grid/animation-grid.component';
import { ParamEditorComponent } from './components/param-editor/param-editor.component';
import { PresetsPanelComponent } from './components/presets-panel/presets-panel.component';
import { TreeSetupComponent } from './components/tree-setup/tree-setup.component';
import { TreeMapperComponent } from './components/tree-mapper/tree-mapper.component';
import { MusicPanelComponent } from './components/music-panel/music-panel.component';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [GlobalControlsComponent, TreePreviewComponent, AnimationGridComponent, ParamEditorComponent, PresetsPanelComponent, TreeSetupComponent, TreeMapperComponent, MusicPanelComponent],
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.scss'],
})
export class AppComponent implements OnInit {
  svc = inject(RgbService);
  private updates = inject(SwUpdate);
  sheetOpen = signal(false);

  peekColors = computed(() => (this.svc.selectedDef()?.preview ?? []).slice(0, 5).map(rgbToHex));

  constructor() {
    // Opening an animation on a phone pops the sheet up
    effect(() => { if (this.svc.lastTap() > 0 && window.innerWidth <= 1180) { this.sheetOpen.set(true); } }, { allowSignalWrites: true });
  }

  ngOnInit(): void {
    void this.svc.load();
    if (this.updates.isEnabled) {
      this.updates.versionUpdates
        .pipe(filter((e): e is VersionReadyEvent => e.type === 'VERSION_READY'))
        .subscribe(() => this.updates.activateUpdate().then(() => document.location.reload()));
    }
  }

  @HostListener('document:visibilitychange')
  onVisibility(): void {
    if (document.visibilityState === 'visible') { void this.svc.refreshState(); }
  }

  retry(): void { void this.svc.load(); }
}
