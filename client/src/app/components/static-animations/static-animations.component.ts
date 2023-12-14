import { Component } from '@angular/core';
import { staticAnimations } from '../rgb-controller/animations';
import { Animations } from 'src/app/interfaces/animations.interface';
import { RgbService } from 'src/app/services/rgb.service';

@Component({
  selector: 'app-static-animations',
  templateUrl: './static-animations.component.html',
  styleUrls: ['./static-animations.component.scss', '../shared-styles.scss']
})
export class StaticAnimationsComponent {
  public animations: Animations[] = staticAnimations;

  constructor(private rgbService: RgbService) { }

  inititateAnimtion(animationName: string): void {
    this.rgbService.startStaticAnimation(animationName).subscribe(response => {
      this.rgbService.isOn.next(true);
      console.log("RESPONSE: ", response);
    });
  }
}
