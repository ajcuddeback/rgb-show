import { Component, OnInit } from '@angular/core';
import { RgbApiService } from 'src/app/services/rgb-api.service';

@Component({
  selector: 'app-rgb-controller',
  templateUrl: './rgb-controller.component.html',
  styleUrls: ['./rgb-controller.component.scss']
})
export class RgbControllerComponent implements OnInit {

  constructor(private rgbApi: RgbApiService) { }

  ngOnInit(): void {
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

  shutDown() {
    this.rgbApi.shutDown().subscribe(response => {
      console.log("RESPONSE: ", response)
    })
  }
}
