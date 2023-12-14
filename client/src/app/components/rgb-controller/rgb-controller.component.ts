import { Component, ElementRef, ViewChild } from '@angular/core';
import { debounceTime, fromEvent } from 'rxjs';
import { RgbService } from 'src/app/services/rgb.service';
import { ActivetState } from 'src/app/interfaces/activeState.interface';

@Component({
  selector: 'app-rgb-controller',
  templateUrl: './rgb-controller.component.html',
  styleUrls: ['./rgb-controller.component.scss', '../shared-styles.scss']
})
export class RgbControllerComponent {
  brightness: number = 10;
  activeState: ActivetState;
  isLoading: boolean = true;
  isOn: boolean = false;
  colors: number[][];
  color: number[];
  speed: number;

  @ViewChild('brightnessInput') brightnessInput: ElementRef<HTMLInputElement>;

  constructor(private rgbService: RgbService) { }

  ngOnInit(): void {
    this.rgbService.getActiveState().subscribe((response: ActivetState) => {
      this.activeState = response;
      this.brightness = this.convertBrightness(this.activeState.brightness);
      this.colors = this.activeState.colors;
      this.color = this.activeState.color;
      this.speed = this.activeState.speed;
      this.rgbService.speed = this.activeState.speed;
      if(this.activeState.animation) {
        this.isOn = true;
      }
      this.isLoading = false;
    });

    this.rgbService.isOn.subscribe(isOn => {
      this.isOn = isOn;
    });

    this.speed = this.rgbService.speed;
  }

  ngAfterViewInit(): void {
      fromEvent(this.brightnessInput.nativeElement, 'input').pipe(
        debounceTime(100)
      ).subscribe(event => {
        const element = event.target as HTMLInputElement;
        this.changeBrightnessLevel(parseInt(element.value));
      })
  }

  convertBrightness(brightness: string) {
    return parseFloat(brightness) * 100;
  }

  changeBrightnessLevel(e: number) {
    this.rgbService.changeBrightness( e / 100).subscribe(_ => {})
  }

  changeSpeed(e: any) {
    this.rgbService.speed = e.target.value;
    this.speed = e.target.value;
  }

  toggleOnOff(event: any): void {
    if(event.target.checked) {
      this.resumeAnimation();
    } else {
      this.shutDown();
    }
  }

  resumeAnimation(): void {
    this.rgbService.resumeAnimation().subscribe(response => {
      this.rgbService.isOn.next(true);
      console.log("RESPONSE: ", response);
    })
  }

  shutDown() {
    this.rgbService.shutDown().subscribe(response => {
      this.rgbService.isOn.next(false);
      console.log("RESPONSE: ", response)
    })
  }
}
