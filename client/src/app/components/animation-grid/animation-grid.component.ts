import { Component, inject } from '@angular/core';
import { RgbService } from '../../services/rgb.service';
import { AnimationDef, rgbToHex } from '../../models';
import { ParamEditorComponent } from '../param-editor/param-editor.component';

@Component({
  selector: 'app-animation-grid',
  standalone: true,
  imports: [ParamEditorComponent],
  templateUrl: './animation-grid.component.html',
  styleUrls: ['./animation-grid.component.scss'],
})
export class AnimationGridComponent {
  svc = inject(RgbService);

  previewColors(def: AnimationDef): string[] {
    return (def.preview.length ? def.preview : [[120, 120, 120]]).slice(0, 5).map(rgbToHex);
  }
  isPlaying(def: AnimationDef): boolean { return this.svc.power() && this.svc.current() === def.name; }
  isSelected(def: AnimationDef): boolean { return this.svc.selected() === def.name; }
  play(def: AnimationDef): void { void this.svc.start(def.name); }
}
