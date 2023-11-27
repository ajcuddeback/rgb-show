import { Component, OnInit } from '@angular/core';
import { RgbApiService } from 'src/app/services/rgb-api.service';

@Component({
  selector: 'app-rgb-controller',
  templateUrl: './rgb-controller.component.html',
  styleUrls: ['./rgb-controller.component.scss']
})
export class RgbControllerComponent {

  constructor(private rgbApi: RgbApiService) { }

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

  shutDown() {
    this.rgbApi.shutDown().subscribe(response => {
      console.log("RESPONSE: ", response)
    })
  }
}
