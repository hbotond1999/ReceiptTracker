import { Component, Input, OnChanges, OnDestroy, OnInit, SimpleChanges, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { 
  IonCard, 
  IonCardHeader, 
  IonCardTitle, 
  IonCardContent, 
  IonSpinner,
  IonList,
  IonItem,
  IonLabel,
  IonNote
} from '@ionic/angular/standalone';
import { ReceiptService } from '../../../../api/api/receipt.service';
import { TopItemsKPI } from '../../../../api/model/topItemsKPI';
import { TopItem } from '../../../../api/model/topItem';
import { Subscription } from 'rxjs';

@Component({
  selector: 'app-top-items',
  standalone: true,
  imports: [
    CommonModule,
    IonCard,
    IonCardHeader,
    IonCardTitle,
    IonCardContent,
    IonSpinner,
    IonList,
    IonItem,
    IonLabel,
    IonNote
  ],
  templateUrl: './top-items.component.html',
  styleUrls: ['./top-items.component.scss']
})
export class TopItemsComponent implements OnInit, OnChanges, OnDestroy {
  @Input() dateFrom!: string;
  @Input() dateTo!: string;
  @Input() userId?: number | null;
  @Input() limit: number = 10;

  private receiptService = inject(ReceiptService);
  private subscription?: Subscription;
  
  topItems: TopItem[] = [];
  isLoading = false;

  ngOnInit() {
    this.loadData();
  }

  ngOnChanges(changes: SimpleChanges) {
    if (changes['dateFrom'] || changes['dateTo'] || changes['userId'] || changes['limit']) {
      this.loadData();
    }
  }

  ngOnDestroy() {
    this.cleanup();
  }

  private loadData() {
    if (!this.dateFrom || !this.dateTo) {
      return;
    }

    this.isLoading = true;
    
    // Unsubscribe from previous subscription
    if (this.subscription) {
      this.subscription.unsubscribe();
    }

    this.subscription = this.receiptService.getTopItemsKpiStatisticKpiTopItemsGet(
      this.dateFrom,
      this.dateTo,
      this.userId || undefined,
      this.limit
    ).subscribe({
      next: (data: TopItemsKPI) => {
        this.isLoading = false;
        this.topItems = data.items || [];
      },
      error: (error) => {
        this.isLoading = false;
        console.error('Error loading top items:', error);
        this.topItems = [];
      }
    });
  }

  private cleanup() {
    if (this.subscription) {
      this.subscription.unsubscribe();
    }
  }
} 