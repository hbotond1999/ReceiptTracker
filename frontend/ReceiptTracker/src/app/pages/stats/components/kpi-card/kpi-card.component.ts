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
import { TotalSpentKPI } from '../../../../api/model/totalSpentKPI';
import { TotalReceiptsKPI } from '../../../../api/model/totalReceiptsKPI';
import { AverageReceiptValueKPI } from '../../../../api/model/averageReceiptValueKPI';
import { Subscription } from 'rxjs';
import {StatisticService} from "../../../../api";

export type KPIType = 'totalSpent' | 'totalReceipts' | 'averageReceiptValue';

@Component({
  selector: 'app-kpi-card',
  standalone: true,
  imports: [
    CommonModule,
    IonCard,
    IonCardHeader,
    IonCardTitle,
    IonCardContent,
    IonSpinner
  ],
  templateUrl: './kpi-card.component.html',
  styleUrls: ['./kpi-card.component.scss']
})
export class KpiCardComponent implements OnInit, OnChanges, OnDestroy {
  @Input() dateFrom!: string;
  @Input() dateTo!: string;
  @Input() userId?: number | null;
  @Input() kpiType!: KPIType;
  @Input() title!: string;
  @Input() color: string = 'primary';
  @Input() unit?: string;

  private statisticService = inject(StatisticService);
  private subscription?: Subscription;

  value: number | null = null;
  isLoading = false;

  ngOnInit() {
    this.loadData();
  }

  ngOnChanges(changes: SimpleChanges) {
    if (changes['dateFrom'] || changes['dateTo'] || changes['userId'] || changes['kpiType']) {
      this.loadData();
    }
  }

  ngOnDestroy() {
    this.cleanup();
  }

  private loadData() {
    if (!this.dateFrom || !this.dateTo || !this.kpiType) {
      return;
    }

    this.isLoading = true;
    this.value = null;

    // Unsubscribe from previous subscription
    if (this.subscription) {
      this.subscription.unsubscribe();
    }

    switch (this.kpiType) {
      case 'totalSpent':
        this.subscription = this.statisticService.getTotalSpentKpiStatisticKpiTotalSpentGet(
          this.dateFrom,
          this.dateTo,
          this.userId || undefined
        ).subscribe({
          next: (data: TotalSpentKPI) => {
            this.isLoading = false;
            this.value = data.total_spent;
          },
          error: (error) => {
            this.isLoading = false;
            console.error('Error loading total spent KPI:', error);
          }
        });
        break;

      case 'totalReceipts':
        this.subscription = this.statisticService.getTotalReceiptsKpiStatisticKpiTotalReceiptsGet(
          this.dateFrom,
          this.dateTo,
          this.userId || undefined
        ).subscribe({
          next: (data: TotalReceiptsKPI) => {
            this.isLoading = false;
            this.value = data.total_receipts;
          },
          error: (error) => {
            this.isLoading = false;
            console.error('Error loading total receipts KPI:', error);
          }
        });
        break;

      case 'averageReceiptValue':
        this.subscription = this.statisticService.getAverageReceiptValueKpiStatisticKpiAverageReceiptValueGet(
          this.dateFrom,
          this.dateTo,
          this.userId || undefined
        ).subscribe({
          next: (data: AverageReceiptValueKPI) => {
            this.isLoading = false;
            this.value = data.average_receipt_value;
          },
          error: (error) => {
            this.isLoading = false;
            console.error('Error loading average receipt value KPI:', error);
          }
        });
        break;
    }
  }

  private cleanup() {
    if (this.subscription) {
      this.subscription.unsubscribe();
    }
  }
}
