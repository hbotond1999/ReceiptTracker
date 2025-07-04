import { Component, Input, OnChanges, OnDestroy, OnInit, SimpleChanges, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { 
  IonCard, 
  IonCardHeader, 
  IonCardTitle, 
  IonCardContent, 
  IonSpinner 
} from '@ionic/angular/standalone';
import { ReceiptService } from '../../../../api/api/receipt.service';
import { WordCloudItem } from '../../../../api/model/wordCloudItem';
import { Subscription } from 'rxjs';

@Component({
  selector: 'app-wordcloud',
  standalone: true,
  imports: [
    CommonModule,
    IonCard,
    IonCardHeader,
    IonCardTitle,
    IonCardContent,
    IonSpinner
  ],
  templateUrl: './wordcloud.component.html',
  styleUrls: ['./wordcloud.component.scss']
})
export class WordCloudComponent implements OnInit, OnChanges, OnDestroy {
  @Input() dateFrom!: string;
  @Input() dateTo!: string;
  @Input() userId?: number | null;
  @Input() limit: number = 30;

  private receiptService = inject(ReceiptService);
  private subscription?: Subscription;
  
  wordCloudData: WordCloudItem[] = [];
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

    this.subscription = this.receiptService.getWordcloudDataStatisticWordcloudGet(
      this.dateFrom,
      this.dateTo,
      this.userId || undefined,
      this.limit
    ).subscribe({
      next: (data: WordCloudItem[]) => {
        this.isLoading = false;
        this.wordCloudData = data || [];
      },
      error: (error) => {
        this.isLoading = false;
        console.error('Error loading wordcloud data:', error);
        this.wordCloudData = [];
      }
    });
  }

  private cleanup() {
    if (this.subscription) {
      this.subscription.unsubscribe();
    }
  }
} 