import { Component, OnInit, OnDestroy, signal, computed, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule, ReactiveFormsModule, FormControl } from '@angular/forms';
import {
  IonHeader,
  IonToolbar,
  IonTitle,
  IonContent,
  IonSelect,
  IonSelectOption,
  IonButton,
  IonCard,
  IonCardHeader,
  IonCardTitle,
  IonCardContent,
  IonLabel,
  IonDatetimeButton,
  IonDatetime,
  IonModal
} from '@ionic/angular/standalone';

import { ReceiptService } from '../../api/api/receipt.service';
import { AuthService } from '../../api/api/auth.service';
import { UserOut } from '../../api/model/userOut';
import { AggregationType } from '../../api/model/aggregationType';
import { Observable, switchMap, map, catchError, of, Subscription } from 'rxjs';

// Chart components
import { ReceiptsChartComponent } from './components/receipts-chart/receipts-chart.component';
import { AmountsChartComponent } from './components/amounts-chart/amounts-chart.component';
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
    IonSelect,
    IonSelectOption,
    IonButton,
    IonCard,
    IonCardHeader,
    IonCardTitle,
    IonCardContent,
    IonLabel,
    ReceiptsChartComponent,
    AmountsChartComponent,
    KpiCardComponent,
    TopItemsComponent,
    MarketTotalSpentChartComponent,
    MarketTotalReceiptsChartComponent,
    MarketAverageSpentChartComponent,
    IonDatetimeButton,
    IonModal,
    IonDatetime
  ],
})
export class StatsPage implements OnInit, OnDestroy {
  // Services
  private readonly receiptService = inject(ReceiptService);
  private readonly authService = inject(AuthService);

  // Constants
  private readonly DEFAULT_DATE_RANGE: [string, string] = [new Date(new Date().getFullYear(), 0, 1).toISOString().split('T')[0], new Date().toISOString().split('T')[0]];

  // Aggregation type options
  readonly aggregationTypeOptions = [
    { value: AggregationType.Day, label: 'Napi' },
    { value: AggregationType.Month, label: 'Havi' },
    { value: AggregationType.Year, label: 'Éves' }
  ];

  // User state
  currentUser = signal<UserOut | null>(null);
  isAdmin = computed(() =>
    this.currentUser()?.roles?.some(role => role === 'admin') || false
  );

  // Filter state
  dateRange = signal<[string, string]>(this.DEFAULT_DATE_RANGE);
  selectedUserId = signal<number | null>(null);
  selectedAggregationType = signal<AggregationType>(AggregationType.Month);

  // Form controls
  userId = new FormControl<number | null>(null);
  aggregationType = new FormControl<AggregationType>(AggregationType.Month);

  // Chart computed properties
  chartParams = computed(() => ({
    dateFrom: this.dateRange()[0] + 'T00:00:00.000Z',
    dateTo: this.dateRange()[1] + 'T23:59:59.999Z',
    userId: this.isAdmin() ? this.selectedUserId() : null,
    aggregationType: this.selectedAggregationType()
  }));

  // Data observables
  private currentUser$: Observable<UserOut | null> = this.authService.getMeAuthMeGet().pipe(
    catchError(this.handleError('Error loading current user', null))
  );

  users$: Observable<UserOut[]> = this.currentUser$.pipe(
    switchMap(user => this.isUserAdmin(user) ? this.loadUsers() : of([]))
  );

  private subscriptions: Subscription[] = [];

  ngOnInit(): void {
    this.initializeComponent();
  }

  ngOnDestroy(): void {
    this.subscriptions.forEach(sub => sub.unsubscribe());
  }

  // Event handlers
  onDateFromChange(event: any): void {
    const dateFrom = event.detail.value.split('T')[0];
    this.dateRange.set([dateFrom, this.dateRange()[1]]);
  }

  onDateToChange(event: any): void {
    const dateTo = event.detail.value.split('T')[0];
    this.dateRange.set([this.dateRange()[0], dateTo]);
  }

  onUserChange(): void {
    this.selectedUserId.set(this.userId.value);
  }

  onAggregationTypeChange(): void {
    const type = this.aggregationType.value || AggregationType.Day;
    this.selectedAggregationType.set(type);
  }

  clearFilters(): void {
    this.dateRange.set(this.DEFAULT_DATE_RANGE);
    this.userId.setValue(null);
    this.selectedUserId.set(null);
    this.aggregationType.setValue(AggregationType.Day);
    this.selectedAggregationType.set(AggregationType.Day);
  }

  // Private methods
  private async initializeComponent(): Promise<void> {
    await this.loadCurrentUser();
    this.setupFormSubscriptions();
  }

  private async loadCurrentUser(): Promise<void> {
    try {
      const user = await this.authService.getMeAuthMeGet().toPromise();
      this.currentUser.set(user || null);
    } catch (error) {
      console.error('Error loading current user:', error);
    }
  }

  private setupFormSubscriptions(): void {
    this.subscriptions.push(
      this.userId.valueChanges.subscribe(userId =>
        this.selectedUserId.set(userId)
      ),
      this.aggregationType.valueChanges.subscribe(aggregationType => {
        const type = aggregationType || AggregationType.Day;
        this.selectedAggregationType.set(type);
      })
    );
  }



  private isUserAdmin(user: UserOut | null): boolean {
    return user?.roles?.some(role => role === 'admin') || false;
  }

  private loadUsers(): Observable<UserOut[]> {
    return this.authService.listUsersAuthUsersGet(0, 1000).pipe(
      map(response => response?.users || []),
      catchError(this.handleError('Error loading users', []))
    );
  }

  private handleError<T>(message: string, fallback: T) {
    return (error: any): Observable<T> => {
      console.error(message, error);
      return of(fallback);
    };
  }
}
