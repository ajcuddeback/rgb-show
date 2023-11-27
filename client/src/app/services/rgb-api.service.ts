import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class RgbApiService {

  constructor(private http: HttpClient) { }

  fillUpAnimtion(): Observable<any> {
    return this.http.get<any>('/start_animation/climbanimation');
  }

  staticXmasAnimation(): Observable<any> {
    return this.http.get<any>('/start_animation/staticxmas');
  }

  shutDown(): Observable<any> {
    return this.http.get<any>('/stop_animation');
  }
}
