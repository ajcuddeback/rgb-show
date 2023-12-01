import { TestBed } from '@angular/core/testing';

import { RgbService } from './rgb.service';

describe('RgbService', () => {
  let service: RgbService;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(RgbService);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });
});
