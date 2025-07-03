import { Component } from '@angular/core';
import { IonHeader, IonToolbar, IonTitle, IonContent } from '@ionic/angular/standalone';

@Component({
  selector: 'app-receipts',
  standalone: true,
  templateUrl: './receipts.page.html',
  styleUrls: ['./receipts.page.scss'],
  imports: [IonHeader, IonToolbar, IonTitle, IonContent],
})
export class ReceiptsPage {} 