import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { ActivetState } from '../interfaces/activeState.interface';

@Injectable({
  providedIn: 'root'
})
export class RgbService {

  constructor(private http: HttpClient) { }

  startMultiColorAnimation(animationName: string, colors: number[][], speed: number): Observable<any> {
    return this.http.post<any>(`/start_multi_color_animation/${animationName}`, {colors, speed});
  }

  startSingleColorAnimation(animationName: string, color: number[], speed: number): Observable<any> {
    return this.http.post<any>(`/start_single_color_animation/${animationName}`, {color, speed});
  }

  startStaticAnimation(animationName: string, speed: number): Observable<any> {
    return this.http.post<any>(`/start_static_animation/${animationName}`, {speed});
  }

  changeBrightness(level: number): Observable<any> {
    return this.http.post<any>('/change_brightness', { brightness: level });
  }

  shutDown(): Observable<any> {
    return this.http.post<any>('/stop_animation', {});
  }

  resumeAnimation(): Observable<any> {
    return this.http.post<any>('/resume_animation', {});
  }

  getActiveState(): Observable<ActivetState> {
    return this.http.get<ActivetState>('/get_active_state');
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
}
