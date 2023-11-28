import { Component, ElementRef, ViewChild } from '@angular/core';
import { debounceTime, fromEvent } from 'rxjs';
import { RgbApiService } from 'src/app/services/rgb-api.service';

@Component({
  selector: 'app-rgb-controller',
  templateUrl: './rgb-controller.component.html',
  styleUrls: ['./rgb-controller.component.scss']
})
export class RgbControllerComponent {

  color: number[] = [0,0,0];
  currentAnimation: string = '';
  brightness: number = 0.1;

  @ViewChild('brightnessInput') brightnessInput: ElementRef<HTMLInputElement>;

  constructor(private rgbApi: RgbApiService) { }

  ngAfterViewInit(): void {
      fromEvent(this.brightnessInput.nativeElement, 'input').pipe(
        debounceTime(2000)
      ).subscribe(event => {
        const element = event.target as HTMLInputElement;
        console.log("VAL: ", parseInt(element.value))
        this.changeBrightnessLevel(parseInt(element.value));
      })
    
  }

  changeBrightnessLevel(e: number) {
    this.brightness = e / 100;
    this.rgbApi.changeBrightness(this.brightness).subscribe(response => {
      this.rgbApi.startAnimation(this.currentAnimation, this.color).subscribe(response => {
        console.log("RESPONSE: ", response)
      });
    })
  }

  getColor(e: any) {
    const color = e.target.value;
    this.color = this.convertHexToRGB(color);
  }

  convertHexToRGB(value: string): number[] {
    const r = parseInt(value.substr(1,2), 16)
    const g = parseInt(value.substr(3,2), 16)
    const b = parseInt(value.substr(5,2), 16)
    return [r, g, b];
  }
  

  inititateAnimtion(animationName: string) {
    this.currentAnimation = animationName;
    this.rgbApi.startAnimation(animationName, this.color).subscribe(response => {
      console.log("RESPONSE: ", response);
    })
  }

  shutDown() {
    this.rgbApi.shutDown().subscribe(response => {
      console.log("RESPONSE: ", response)
    })
  }
}
