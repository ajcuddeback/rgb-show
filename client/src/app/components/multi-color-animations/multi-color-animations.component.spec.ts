import { ComponentFixture, TestBed } from '@angular/core/testing';

import { MultiColorAnimationsComponent } from './multi-color-animations.component';

describe('MultiColorAnimationsComponent', () => {
  let component: MultiColorAnimationsComponent;
  let fixture: ComponentFixture<MultiColorAnimationsComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [MultiColorAnimationsComponent]
    })
    .compileComponents();
    
    fixture = TestBed.createComponent(MultiColorAnimationsComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
