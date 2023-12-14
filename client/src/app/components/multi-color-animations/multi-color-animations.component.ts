import { Component, ElementRef, Input, QueryList, ViewChildren } from '@angular/core';
import { multiColorAnimations } from '../rgb-controller/animations';
import { Animations } from 'src/app/interfaces/animations.interface';
import { RgbService } from 'src/app/services/rgb.service';


@Component({
  selector: 'app-multi-color-animations',
  templateUrl: './multi-color-animations.component.html',
  styleUrl: './multi-color-animations.component.scss'
})
export class MultiColorAnimationsComponent {
  public animations: Animations[] = multiColorAnimations;
  @Input({ required: true }) defaultColors: number[][] = [];
  colors: string[] = [];

  @ViewChildren('brightnessInput') brightnessInputs: QueryList<ElementRef>;

  constructor(private rgbService: RgbService) { }

  ngOnInit(): void {
    if(this.defaultColors.length > 0) {
      this.defaultColors.forEach(color => {
        this.colors.push(this.rgbService.rgbToHex(color));
      })
    } else {
      this.colors.push('#000000')
    }
  }

  modifyColor(event: any, index: number): void {
   this.colors[index] = event.target.value;
  }

  addColorInput(): void {
    this.colors.push('#000000');
  }

  removeColorInput(): void {
    this.colors.pop();
  }

  inititateAnimtion(animationName: string): void {
    console.log("COLORS: ", this.colors)
    console.log("ANIMATION NAME: ", animationName)
    const rgbColors: number[][] = [];
    this.colors.forEach(color => {
      const rgbColor = this.rgbService.convertHexToRGB(color);
      rgbColors.push(rgbColor);
    });

    this.rgbService.startMultiColorAnimation(animationName, rgbColors).subscribe(response => {
      this.rgbService.isOn.next(true);
      console.log("RESPONSE: ", response);
    });
  }
}
