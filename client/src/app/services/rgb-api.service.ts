import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class RgbApiService {

  constructor(private http: HttpClient) { }

  fillUpAnimtion(): Observable<any> {
    return this.http.post<any>('/start_animation/climbanimation', {});
  }

  staticXmasAnimation(): Observable<any> {
    return this.http.post<any>('/start_animation/staticxmas', {});
  }

  rainbowAnimation(): Observable<any> {
    return this.http.post<any>('/start_animation/rainbowanimation', {});
  }

  sparkleAnimation(): Observable<any> {
    return this.http.post<any>('/start_animation/sparkleanimation', {});
  }

  singleColor(color: number[]): Observable<any> {
    return this.http.post<any>('/start_animation/singlecolor', {color: color});
  }

  shutDown(): Observable<any> {
    return this.http.post<any>('/stop_animation', {});
  }
}
