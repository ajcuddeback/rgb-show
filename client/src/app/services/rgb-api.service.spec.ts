import { TestBed } from '@angular/core/testing';

import { RgbApiService } from './rgb-api.service';

describe('RgbApiService', () => {
  let service: RgbApiService;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(RgbApiService);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });
});
