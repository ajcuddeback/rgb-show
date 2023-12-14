import { ComponentFixture, TestBed } from '@angular/core/testing';

import { StaticAnimationsComponent } from './static-animations.component';

describe('StaticAnimationsComponent', () => {
  let component: StaticAnimationsComponent;
  let fixture: ComponentFixture<StaticAnimationsComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [StaticAnimationsComponent]
    })
    .compileComponents();
    
    fixture = TestBed.createComponent(StaticAnimationsComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
