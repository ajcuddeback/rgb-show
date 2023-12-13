import { ComponentFixture, TestBed } from '@angular/core/testing';

import { SingleColorAnimationsComponent } from './single-color-animations.component';

describe('SingleColorAnimationsComponent', () => {
  let component: SingleColorAnimationsComponent;
  let fixture: ComponentFixture<SingleColorAnimationsComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [SingleColorAnimationsComponent]
    })
    .compileComponents();
    
    fixture = TestBed.createComponent(SingleColorAnimationsComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
