import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class RgbApiService {

  constructor(private http: HttpClient) { }

  startAnimation(animationName: string, color: number[]): Observable<any> {
    return this.http.post<any>(`/start_animation/${animationName}`, {color: color});
  }

  shutDown(): Observable<any> {
    return this.http.post<any>('/stop_animation', {});
  }
}
