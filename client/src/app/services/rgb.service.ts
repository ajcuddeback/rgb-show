import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { ActivetState } from '../interfaces/activeState.interface';

@Injectable({
  providedIn: 'root'
})
export class RgbService {

  constructor(private http: HttpClient) { }

  startAnimation(animationName: string, color: number[]): Observable<any> {
    return this.http.post<any>(`/start_animation/${animationName}`, {color: color});
  }

  changeBrightness(level: number): Observable<any> {
    return this.http.post<any>('/change_brightness', { brightness: level });
  }

  shutDown(): Observable<any> {
    return this.http.post<any>('/stop_animation', {});
  }

  getActiveState(): Observable<ActivetState> {
    return this.http.get<ActivetState>('/get_active_state');
  }
}
