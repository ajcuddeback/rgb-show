import { NgModule } from '@angular/core';
import { BrowserModule } from '@angular/platform-browser';
import { HttpClientModule } from '@angular/common/http';
import { FormsModule } from '@angular/forms';
 
import { AppRoutingModule } from './app-routing.module';
import { AppComponent } from './app.component';
import { RgbControllerComponent } from './components/rgb-controller/rgb-controller.component';
import { MultiColorAnimationsComponent } from './components/multi-color-animations/multi-color-animations.component';

@NgModule({
  declarations: [
    AppComponent,
    RgbControllerComponent,
    MultiColorAnimationsComponent
  ],
  imports: [
    BrowserModule,
    AppRoutingModule,
    HttpClientModule,
    FormsModule
  ],
  providers: [],
  bootstrap: [AppComponent]
})
export class AppModule { }
