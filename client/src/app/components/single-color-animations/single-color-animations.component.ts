import { Component, ElementRef, Input, ViewChild } from '@angular/core';
import { Animations } from 'src/app/interfaces/animations.interface';
import { singleColorAnimations } from '../rgb-controller/animations';
import { RgbService } from 'src/app/services/rgb.service';

@Component({
  selector: 'app-single-color-animations',
  templateUrl: './single-color-animations.component.html',
  styleUrls: ['./single-color-animations.component.scss', '../shared-styles.scss']
})
export class SingleColorAnimationsComponent {

  public animations: Animations[] = singleColorAnimations;
  @Input({ required: true }) defaultColor: number[] = [];
  color: string = '#000000';

  constructor(private rgbService: RgbService) { }

  ngOnInit(): void {
    if(this.defaultColor?.length > 0) {
      this.color = this.rgbService.rgbToHex(this.defaultColor);
    }
  }

  modifyColor(event: any): void {
   this.color = event.target.value;
  }

  inititateAnimtion(animationName: string): void {
    const rgbColor: number[] = this.rgbService.convertHexToRGB(this.color);

    this.rgbService.startSingleColorAnimation(animationName, rgbColor).subscribe(response => {
      this.rgbService.isOn.next(true);
      console.log("RESPONSE: ", response);
    });
  }

}
