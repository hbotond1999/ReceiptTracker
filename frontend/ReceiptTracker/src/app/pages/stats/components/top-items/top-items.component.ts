import {Component, inject, Input, OnChanges, OnDestroy, OnInit, SimpleChanges} from '@angular/core';
import {CommonModule} from '@angular/common';
import {
  IonCard,
  IonCardContent,
  IonCardHeader,
  IonCardTitle,
  IonItem,
  IonLabel,
  IonList,
  IonNote,
  IonSpinner
} from '@ionic/angular/standalone';
import {StatisticService, TopItem, TopItemsKPI} from '../../../../api';
import {Subject, takeUntil} from 'rxjs';

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

  private statisticService = inject(StatisticService);
  private readonly unsub$ = new Subject<void>();

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
    this.unsub$.next();
    this.unsub$.complete();
  }

  private loadData() {
    if (!this.dateFrom || !this.dateTo) {
      return;
    }

    this.isLoading = true;

    this.statisticService.getTopItemsKpiStatisticKpiTopItemsGet(
      this.dateFrom,
      this.dateTo,
      this.userId || undefined,
      this.limit
    ).pipe(
      takeUntil(this.unsub$)
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
}
