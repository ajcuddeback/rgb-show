import { Component, HostListener, OnInit, inject, signal } from '@angular/core';
import { RgbService } from './services/rgb.service';
import { PowerToggleComponent } from './components/power-toggle/power-toggle.component';
import { GlobalControlsComponent } from './components/global-controls/global-controls.component';
import { TreePreviewComponent } from './components/tree-preview/tree-preview.component';
import { AnimationGridComponent } from './components/animation-grid/animation-grid.component';
import { ParamEditorComponent } from './components/param-editor/param-editor.component';
import { PresetsPanelComponent } from './components/presets-panel/presets-panel.component';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [
    PowerToggleComponent, GlobalControlsComponent, TreePreviewComponent,
    AnimationGridComponent, ParamEditorComponent, PresetsPanelComponent,
  ],
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.scss'],
})
export class AppComponent implements OnInit {
  svc = inject(RgbService);
  /** Mobile bottom sheet expanded state. */
  sheetOpen = signal(false);

  ngOnInit(): void {
    void this.svc.load();
  }

  @HostListener('document:visibilitychange')
  onVisibility(): void {
    if (document.visibilityState === 'visible') {
      void this.svc.refreshState();
    }
  }

  openEditor(): void {
    this.sheetOpen.set(true);
  }

  retry(): void {
    void this.svc.load();
  }
}
