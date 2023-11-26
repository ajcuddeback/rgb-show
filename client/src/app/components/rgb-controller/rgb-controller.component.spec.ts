import { ComponentFixture, TestBed } from '@angular/core/testing';

import { RgbControllerComponent } from './rgb-controller.component';

describe('RgbControllerComponent', () => {
  let component: RgbControllerComponent;
  let fixture: ComponentFixture<RgbControllerComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ RgbControllerComponent ]
    })
    .compileComponents();

    fixture = TestBed.createComponent(RgbControllerComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
