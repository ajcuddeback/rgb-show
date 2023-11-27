import { Component } from '@angular/core';
import { RgbApiService } from 'src/app/services/rgb-api.service';

@Component({
  selector: 'app-rgb-controller',
  templateUrl: './rgb-controller.component.html',
  styleUrls: ['./rgb-controller.component.scss']
})
export class RgbControllerComponent {

  color: number[] = [0,0,0];

  constructor(private rgbApi: RgbApiService) { }

  getColor(e: any) {
    const color = e.target.value;
    this.color = this.convertHexToRGB(color);
    console.log("COLOR: ", this.color)
  }

  convertHexToRGB(value: string): number[] {
    const r = parseInt(value.substr(1,2), 16)
    const g = parseInt(value.substr(3,2), 16)
    const b = parseInt(value.substr(5,2), 16)
    return [r, g, b];
  }
  

  inititateFillUpAnimtion() {
    this.rgbApi.fillUpAnimtion().subscribe(response => {
      console.log("RESPONSE: ", response);
    })
  }

  inititateStaticXmasAnimation() {
    this.rgbApi.staticXmasAnimation().subscribe(response => {
      console.log("RESPONSE: ", response);
    })
  }

  inititateRainbowAnimation() {
    this.rgbApi.rainbowAnimation().subscribe(response => {
      console.log("RESPONSE: ", response);
    })
  }

  initiateSparkleAnimation() {
    this.rgbApi.sparkleAnimation().subscribe(response => {
      console.log("RESPONSE: ", response);
    })
  }

  initiateSingleColor() {
    this.rgbApi.singleColor(this.color).subscribe(response => {
      console.log("RESPONSE: ", response);
    })
  }

  shutDown() {
    this.rgbApi.shutDown().subscribe(response => {
      console.log("RESPONSE: ", response)
    })
  }
}
