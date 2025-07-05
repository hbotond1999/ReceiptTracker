import { Component, OnInit } from '@angular/core';
import { IonApp, IonRouterOutlet } from '@ionic/angular/standalone';
import { Store } from '@ngrx/store';
import { autoLogin } from './store/auth/auth.actions';
import {addIcons} from "ionicons";
import {chevronDownOutline, chevronUpOutline, logoIonic, closeOutline, addOutline, trashOutline, createOutline} from "ionicons/icons";

@Component({
  selector: 'app-root',
  templateUrl: 'app.component.html',
  imports: [IonApp, IonRouterOutlet],
})
export class AppComponent implements OnInit {
  constructor(private store: Store) {}

  ngOnInit() {
    this.store.dispatch(autoLogin());
    addIcons({ logoIonic,  chevronUpOutline, chevronDownOutline, trashOutline, createOutline, closeOutline, addOutline });

  }
}
