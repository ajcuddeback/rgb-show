import { Component, ElementRef, ViewChild } from '@angular/core';
import { debounceTime, fromEvent } from 'rxjs';
import { Animations } from 'src/app/interfaces/animations.interface';
import { RgbService } from 'src/app/services/rgb.service';
import { animations } from './animations';
import { ActivetState } from 'src/app/interfaces/activeState.interface';

@Component({
  selector: 'app-rgb-controller',
  templateUrl: './rgb-controller.component.html',
  styleUrls: ['./rgb-controller.component.scss']
})
export class RgbControllerComponent {
  public animations: Animations[] = animations;
  color: number[] = [0,0,0];
  currentAnimation: string = '';
  brightness: number = 0.1;
  activeState: ActivetState;
  isLoading: boolean = true;

  @ViewChild('brightnessInput') brightnessInput: ElementRef<HTMLInputElement>;

  constructor(private rgbService: RgbService) { }

  ngOnInit(): void {
    this.isLoading = true;
    this.rgbService.getActiveState().subscribe((response: ActivetState) => {
      this.activeState = response;
      this.brightness = this.convertBrightness(this.activeState.brightness);
      this.isLoading = false;
      this.setUpBrightnessEventListener();
    })
  }

  setUpBrightnessEventListener(): void {
    fromEvent(this.brightnessInput.nativeElement, 'input').pipe(
      debounceTime(100)
    ).subscribe(event => {
      const element = event.target as HTMLInputElement;
      this.changeBrightnessLevel(parseInt(element.value));
    })
  }

  convertBrightness(brightness: string) {
    return parseInt(brightness) * 100;
  }

  changeBrightnessLevel(e: number) {
    this.brightness = e / 100;
    this.rgbService.changeBrightness(this.brightness).subscribe(_ => {})
  }

  getColor(e: any) {
    const color = e.target.value;
    this.color = this.convertHexToRGB(color);
    // Reset current animation so the initiate method can be ran again...
    this.currentAnimation = '';
  }

  convertHexToRGB(value: string): number[] {
    const r = parseInt(value.substr(1,2), 16)
    const g = parseInt(value.substr(3,2), 16)
    const b = parseInt(value.substr(5,2), 16)
    return [r, g, b];
  }

  rgbToHex(rgb: number[]) {
    return "#" + ((1 << 24) + (rgb[0] << 16) + (rgb[1] << 8) + rgb[2]).toString(16).slice(1);
  }
  

  inititateAnimtion(animationName: string) {
    this.currentAnimation = animationName;
    this.rgbService.startAnimation(animationName, this.color).subscribe(response => {
      console.log("RESPONSE: ", response);
    })
  }

  shutDown() {
    this.rgbService.shutDown().subscribe(response => {
      console.log("RESPONSE: ", response)
    })
  }
}
