import { Component, OnInit, OnDestroy, signal, computed, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule, ReactiveFormsModule, FormControl } from '@angular/forms';
import {
  IonHeader,
  IonToolbar,
  IonTitle,
  IonContent,
  IonRange,
  IonSelect,
  IonSelectOption,
  IonButton,
  IonCard,
  IonCardHeader,
  IonCardTitle,
  IonCardContent,
  IonSpinner,
  IonItem,
  IonLabel,
  IonNote,
  IonList
} from '@ionic/angular/standalone';
import { ReceiptService } from '../../api/api/receipt.service';
import { AuthService } from '../../api/api/auth.service';
import { UserOut } from '../../api/model/userOut';
import { AggregationType } from '../../api/model/aggregationType';
import { Observable, BehaviorSubject, switchMap, map, catchError, of, Subscription } from 'rxjs';

// Import chart components
import { ReceiptsChartComponent } from './components/receipts-chart/receipts-chart.component';
import { AmountsChartComponent } from './components/amounts-chart/amounts-chart.component';
import { WordCloudComponent } from './components/wordcloud/wordcloud.component';
import { KpiCardComponent } from './components/kpi-card/kpi-card.component';
import { TopItemsComponent } from './components/top-items/top-items.component';
import { MarketTotalSpentChartComponent } from './components/market-total-spent-chart/market-total-spent-chart.component';
import { MarketTotalReceiptsChartComponent } from './components/market-total-receipts-chart/market-total-receipts-chart.component';
import { MarketAverageSpentChartComponent } from './components/market-average-spent-chart/market-average-spent-chart.component';

@Component({
  selector: 'app-stats',
  standalone: true,
  templateUrl: './stats.page.html',
  styleUrls: ['./stats.page.scss'],
  imports: [
    CommonModule,
    FormsModule,
    ReactiveFormsModule,
    IonHeader,
    IonToolbar,
    IonTitle,
    IonContent,
    IonRange,
    IonSelect,
    IonSelectOption,
    IonButton,
    IonCard,
    IonCardHeader,
    IonCardTitle,
    IonCardContent,
    IonSpinner,
    IonItem,
    IonLabel,
    IonNote,
    IonList,
    ReceiptsChartComponent,
    AmountsChartComponent,
    WordCloudComponent,
    KpiCardComponent,
    TopItemsComponent,
    MarketTotalSpentChartComponent,
    MarketTotalReceiptsChartComponent,
    MarketAverageSpentChartComponent
  ],
})
export class StatsPage implements OnInit, OnDestroy {
  private receiptService = inject(ReceiptService);
  private authService = inject(AuthService);

  // Signals
  currentUser = signal<UserOut | null>(null);
  isAdmin = computed(() => {
    const user = this.currentUser();
    return user?.roles?.some(role => role === 'admin') || false;
  });

  // Date range
  MIN_DATE = new Date('2023-01-01').getTime();
  MAX_DATE = new Date().getTime();
  dateRange = signal<[number, number]>([this.MIN_DATE, this.MAX_DATE]);

  // User filter (admin only) - signal-alapú
  selectedUserId = signal<number | null>(null);
  userId = new FormControl<number | null>(null);

  // Aggregation type - signal-alapú
  selectedAggregationType = signal<AggregationType>(AggregationType.Day);
  aggregationType = new FormControl<AggregationType>(AggregationType.Day);

  // Aggregation type options
  aggregationTypeOptions = [
    { value: AggregationType.Day, label: 'Napi' },
    { value: AggregationType.Month, label: 'Havi' },
    { value: AggregationType.Year, label: 'Éves' }
  ];

  // Filter subjects (megtartva a kompatibilitás miatt)
  private dateRangeSubject = new BehaviorSubject<[number, number]>([this.MIN_DATE, this.MAX_DATE]);
  private userIdSubject = new BehaviorSubject<number | null>(null);
  private aggregationTypeSubject = new BehaviorSubject<AggregationType>(AggregationType.Day);

  // Subscriptions
  private subscriptions: Subscription[] = [];

  // Chart filter params - computed from current filters
  chartDateFrom = computed(() => {
    const [dateFrom] = this.dateRange();
    return new Date(dateFrom).toISOString();
  });

  chartDateTo = computed(() => {
    const [, dateTo] = this.dateRange();
    return new Date(dateTo).toISOString();
  });

  chartUserId = computed(() => {
    return this.isAdmin() ? this.selectedUserId() : null;
  });

  chartAggregationType = computed(() => {
    return this.selectedAggregationType();
  });

  // Observable-k a felhasználókhoz
  currentUser$: Observable<UserOut | null> = this.authService.getMeAuthMeGet().pipe(
    catchError(error => {
      console.error('Error loading current user:', error);
      return of(null);
    })
  );

  users$: Observable<UserOut[]> = this.currentUser$.pipe(
    switchMap(user => {
      if (user?.roles?.some(role => role === 'admin')) {
        return this.authService.listUsersAuthUsersGet(0, 1000).pipe(
          map(response => response?.users || []),
          catchError(error => {
            console.error('Error loading users:', error);
            return of([]);
          })
        );
      }
      return of([]);
    })
  );

  ngOnInit() {
    this.loadCurrentUser();
    this.setupUserFilter();
    this.setupAggregationTypeFilter();
  }

  ngOnDestroy() {
    // Clean up subscriptions
    this.subscriptions.forEach(sub => sub.unsubscribe());
  }

  private async loadCurrentUser() {
    try {
      const user = await this.authService.getMeAuthMeGet().toPromise();
      this.currentUser.set(user || null);
    } catch (error) {
      console.error('Error loading current user:', error);
    }
  }

  private setupUserFilter() {
    const subscription = this.userId.valueChanges.subscribe(userId => {
      this.selectedUserId.set(userId);
      this.userIdSubject.next(userId);
    });
    this.subscriptions.push(subscription);
  }

  private setupAggregationTypeFilter() {
    const subscription = this.aggregationType.valueChanges.subscribe(aggregationType => {
      const type = aggregationType || AggregationType.Day;
      this.selectedAggregationType.set(type);
      this.aggregationTypeSubject.next(type);
    });
    this.subscriptions.push(subscription);
  }

  onDateRangeInput(event: any) {
    const { lower, upper } = event.detail.value;
    this.dateRange.set([lower, upper]);
  }

  onDateRangeChange(event: any) {
    const { lower, upper } = event.detail.value;
    this.dateRange.set([lower, upper]);
    this.dateRangeSubject.next([lower, upper]);
  }

  onUserChange() {
    const userId = this.userId.value;
    this.selectedUserId.set(userId);
    this.userIdSubject.next(userId);
  }

  onAggregationTypeChange() {
    const type = this.aggregationType.value || AggregationType.Day;
    this.selectedAggregationType.set(type);
    this.aggregationTypeSubject.next(type);
  }

  clearFilters() {
    this.dateRange.set([this.MIN_DATE, this.MAX_DATE]);
    this.dateRangeSubject.next([this.MIN_DATE, this.MAX_DATE]);
    this.userId.setValue(null);
    this.selectedUserId.set(null);
    this.userIdSubject.next(null);
    this.aggregationType.setValue(AggregationType.Day);
    this.selectedAggregationType.set(AggregationType.Day);
    this.aggregationTypeSubject.next(AggregationType.Day);
  }
}
