import { Component, OnInit } from '@angular/core';
import { IonApp, IonRouterOutlet } from '@ionic/angular/standalone';
import { Store } from '@ngrx/store';
import { autoLogin } from './store/auth/auth.actions';

@Component({
  selector: 'app-root',
  templateUrl: 'app.component.html',
  imports: [IonApp, IonRouterOutlet],
})
export class AppComponent implements OnInit {
  constructor(private store: Store) {}

  ngOnInit() {
    // Auto-login próbálkozás az alkalmazás indításkor
    this.store.dispatch(autoLogin());
  }
}
