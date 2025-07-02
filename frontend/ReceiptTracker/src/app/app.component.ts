import { Component, OnInit } from '@angular/core';
import { Store } from '@ngrx/store';
import { Storage } from '@ionic/storage-angular';
import * as AuthActions from './store/auth/auth.actions';

@Component({
  selector: 'app-root',
  templateUrl: 'app.component.html',
  styleUrls: ['app.component.scss'],
  standalone: false,
})
export class AppComponent implements OnInit {
  constructor(
    private store: Store,
    private storage: Storage
  ) {}

  async ngOnInit() {
    // Initialize storage before trying to auto login
    await this.storage.create();
    
    // Try auto login on app start
    this.store.dispatch(AuthActions.autoLogin());
  }
}
