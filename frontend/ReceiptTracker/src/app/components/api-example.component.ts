import { Component, OnInit } from '@angular/core';
import { ApiService } from '../services/api.service';
import { ReceiptListOut, UserListOut } from '../api/model/models';

@Component({
  selector: 'app-api-example',
  template: `
    <ion-content>
      <ion-header>
        <ion-toolbar>
          <ion-title>API Example</ion-title>
        </ion-toolbar>
      </ion-header>

      <ion-list>
        <ion-item>
          <ion-button (click)="loadReceipts()">Load Receipts</ion-button>
        </ion-item>
        
        <ion-item>
          <ion-button (click)="loadUsers()">Load Users</ion-button>
        </ion-item>

        <ion-item *ngIf="receipts">
          <ion-label>
            <h2>Receipts ({{ receipts.total }})</h2>
            <p *ngFor="let receipt of receipts.items">{{ receipt.receipt_number }} - {{ receipt.date }}</p>
          </ion-label>
        </ion-item>

        <ion-item *ngIf="users">
          <ion-label>
            <h2>Users ({{ users.total }})</h2>
            <p *ngFor="let user of users.items">{{ user.username }} - {{ user.email }}</p>
          </ion-label>
        </ion-item>
      </ion-list>
    </ion-content>
  `
})
export class ApiExampleComponent implements OnInit {

  receipts: ReceiptListOut | null = null;
  users: UserListOut | null = null;

  constructor(private apiService: ApiService) { }

  ngOnInit() {
    // Automatically load receipts when component initializes
    this.loadReceipts();
  }

  loadReceipts() {
    this.apiService.getReceipts().subscribe({
      next: (data) => {
        this.receipts = data;
        console.log('Receipts loaded:', data);
      },
      error: (error) => {
        console.error('Error loading receipts:', error);
      }
    });
  }

  loadUsers() {
    this.apiService.getCurrentUser().subscribe({
      next: (data) => {
        this.users = data;
        console.log('Users loaded:', data);
      },
      error: (error) => {
        console.error('Error loading users:', error);
      }
    });
  }
} 