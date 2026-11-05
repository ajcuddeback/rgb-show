import { Component, HostListener, OnInit, inject } from '@angular/core';
import { SwUpdate, VersionReadyEvent } from '@angular/service-worker';
import { filter } from 'rxjs';
import { RgbService } from './services/rgb.service';
import { PowerToggleComponent } from './components/power-toggle/power-toggle.component';
import { GlobalControlsComponent } from './components/global-controls/global-controls.component';
import { TreePreviewComponent } from './components/tree-preview/tree-preview.component';
import { AnimationGridComponent } from './components/animation-grid/animation-grid.component';
import { PresetsPanelComponent } from './components/presets-panel/presets-panel.component';
import { TreeSetupComponent } from './components/tree-setup/tree-setup.component';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [PowerToggleComponent, GlobalControlsComponent, TreePreviewComponent, AnimationGridComponent, PresetsPanelComponent, TreeSetupComponent],
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.scss'],
})
export class AppComponent implements OnInit {
  svc = inject(RgbService);
  private updates = inject(SwUpdate);

  ngOnInit(): void {
    void this.svc.load();
    // Installed-app users get new deploys automatically: when the service
    // worker has fetched a new version, switch to it and reload.
    if (this.updates.isEnabled) {
      this.updates.versionUpdates
        .pipe(filter((e): e is VersionReadyEvent => e.type === 'VERSION_READY'))
        .subscribe(() => this.updates.activateUpdate().then(() => document.location.reload()));
    }
  }

  @HostListener('document:visibilitychange')
  onVisibility(): void {
    if (document.visibilityState === 'visible') {
      void this.svc.refreshState();
    }
  }

  retry(): void {
    void this.svc.load();
  }
}
