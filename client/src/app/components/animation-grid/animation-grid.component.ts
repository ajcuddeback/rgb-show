import { Component, inject } from '@angular/core';
import { RgbService } from '../../services/rgb.service';
import { AnimationDef, rgbToHex } from '../../models';

@Component({
  selector: 'app-animation-grid',
  standalone: true,
  templateUrl: './animation-grid.component.html',
  styleUrls: ['./animation-grid.component.scss'],
})
export class AnimationGridComponent {
  svc = inject(RgbService);

  chip(def: AnimationDef): string {
    const colors = def.preview.length ? def.preview.map(rgbToHex) : ['#444', '#777'];
    if (colors.length === 1) { return colors[0]; }
    return `linear-gradient(135deg, ${colors.join(', ')})`;
  }

  isPlaying(def: AnimationDef): boolean {
    return this.svc.power() && this.svc.current() === def.name;
  }

  isSelected(def: AnimationDef): boolean {
    return this.svc.selected() === def.name;
  }

  play(def: AnimationDef): void {
    void this.svc.start(def.name);
  }
}
