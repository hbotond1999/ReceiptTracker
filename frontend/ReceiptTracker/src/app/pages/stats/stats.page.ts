import { Component, OnInit, OnDestroy, signal, computed, inject, AfterViewInit } from '@angular/core';
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
import { TopItemsKPI } from '../../api/model/topItemsKPI';
import { WordCloudItem } from '../../api/model/wordCloudItem';
import { TotalSpentKPI } from '../../api/model/totalSpentKPI';
import { TotalReceiptsKPI } from '../../api/model/totalReceiptsKPI';
import { AverageReceiptValueKPI } from '../../api/model/averageReceiptValueKPI';
import { TimeSeriesData } from '../../api/model/timeSeriesData';
import { Observable, BehaviorSubject, switchMap, map, catchError, of, Subscription } from 'rxjs';

// amCharts 5 imports
import * as am5 from '@amcharts/amcharts5';
import * as am5xy from '@amcharts/amcharts5/xy';
import am5themes_Animated from '@amcharts/amcharts5/themes/Animated';

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
    IonList
  ],
})
export class StatsPage implements OnInit, OnDestroy, AfterViewInit {
  private receiptService = inject(ReceiptService);
  private authService = inject(AuthService);

  // Signals
  currentUser = signal<UserOut | null>(null);
  isAdmin = computed(() => {
    const user = this.currentUser();
    return user?.roles?.some(role => role === 'admin') || false;
  });

  // Date range
  MIN_DATE = new Date('2020-01-01').getTime();
  MAX_DATE = new Date().getTime();
  dateRange = signal<[number, number]>([this.MIN_DATE, this.MAX_DATE]);

  // User filter (admin only)
  userId = new FormControl<number | null>(null);

  // Filter subjects
  private dateRangeSubject = new BehaviorSubject<[number, number]>([this.MIN_DATE, this.MAX_DATE]);
  private userIdSubject = new BehaviorSubject<number | null>(null);

  // amCharts 5 charts
  private receiptsChart?: am5xy.XYChart;
  private amountsChart?: am5xy.XYChart;
  private root?: am5.Root;
  private root2?: am5.Root;

  // Subscriptions
  private subscriptions: Subscription[] = [];

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

  // KPI adatok Observable-k
  totalSpent$: Observable<TotalSpentKPI> = this.getFilterParams().pipe(
    switchMap(params => this.receiptService.getTotalSpentKpiReceiptStatisticsKpiTotalSpentGet(
      params.dateFrom, params.dateTo, params.userId
    ))
  );

  totalReceipts$: Observable<TotalReceiptsKPI> = this.getFilterParams().pipe(
    switchMap(params => this.receiptService.getTotalReceiptsKpiReceiptStatisticsKpiTotalReceiptsGet(
      params.dateFrom, params.dateTo, params.userId
    ))
  );

  averageReceiptValue$: Observable<AverageReceiptValueKPI> = this.getFilterParams().pipe(
    switchMap(params => this.receiptService.getAverageReceiptValueKpiReceiptStatisticsKpiAverageReceiptValueGet(
      params.dateFrom, params.dateTo, params.userId
    ))
  );

  topItems$: Observable<TopItemsKPI> = this.getFilterParams().pipe(
    switchMap(params => this.receiptService.getTopItemsKpiReceiptStatisticsKpiTopItemsGet(
      params.dateFrom, params.dateTo, params.userId, 10
    ))
  );

  // Chart adatok Observable-k
  receiptsTimeSeries$: Observable<TimeSeriesData[]> = this.getFilterParams().pipe(
    switchMap(params => this.receiptService.getReceiptsTimeseriesReceiptStatisticsTimeseriesReceiptsGet(
      params.dateFrom, params.dateTo, params.userId
    ))
  );

  amountsTimeSeries$: Observable<TimeSeriesData[]> = this.getFilterParams().pipe(
    switchMap(params => this.receiptService.getAmountsTimeseriesReceiptStatisticsTimeseriesAmountsGet(
      params.dateFrom, params.dateTo, params.userId
    ))
  );

  wordcloudData$: Observable<WordCloudItem[]> = this.getFilterParams().pipe(
    switchMap(params => this.receiptService.getWordcloudDataReceiptStatisticsWordcloudGet(
      params.dateFrom, params.dateTo, params.userId, 30
    ))
  );

  ngOnInit() {
    this.loadCurrentUser();
    this.setupUserFilter();
  }

  ngAfterViewInit() {
    // Initialize charts after view is ready
    setTimeout(() => {
      this.initializeCharts();
    }, 100);
  }

  ngOnDestroy() {
    // Clean up subscriptions
    this.subscriptions.forEach(sub => sub.unsubscribe());
    
    // Dispose charts
    if (this.root) {
      this.root.dispose();
    }
    if (this.root2) {
      this.root2.dispose();
    }
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
    this.userId.valueChanges.subscribe(userId => {
      this.userIdSubject.next(userId);
    });
  }

  private getFilterParams(): Observable<{dateFrom: string, dateTo: string, userId: number | undefined}> {
    return new Observable(observer => {
      // Combine both subjects to react to changes in either
      const dateSubscription = this.dateRangeSubject.subscribe(dateRange => {
        const [dateFrom, dateTo] = dateRange;
        const dateFromStr = new Date(dateFrom).toISOString();
        const dateToStr = new Date(dateTo).toISOString();
        
        const params = {
          dateFrom: dateFromStr,
          dateTo: dateToStr,
          userId: this.isAdmin() ? this.userId.value || undefined : undefined
        };
        
        observer.next(params);
      });

      const userSubscription = this.userIdSubject.subscribe(() => {
        const currentDateRange = this.dateRangeSubject.value;
        const [dateFrom, dateTo] = currentDateRange;
        const dateFromStr = new Date(dateFrom).toISOString();
        const dateToStr = new Date(dateTo).toISOString();
        
        const params = {
          dateFrom: dateFromStr,
          dateTo: dateToStr,
          userId: this.isAdmin() ? this.userId.value || undefined : undefined
        };
        
        observer.next(params);
      });

      return () => {
        dateSubscription.unsubscribe();
        userSubscription.unsubscribe();
      };
    });
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
    this.userIdSubject.next(this.userId.value);
  }

  clearFilters() {
    this.dateRange.set([this.MIN_DATE, this.MAX_DATE]);
    this.dateRangeSubject.next([this.MIN_DATE, this.MAX_DATE]);
    this.userId.setValue(null);
    this.userIdSubject.next(null);
  }

  private initializeCharts() {
    this.createReceiptsChart();
    this.createAmountsChart();
  }

  private createReceiptsChart() {
    // Create root element
    this.root = am5.Root.new("receipts-chart");
    
    // Set themes
    this.root.setThemes([
      am5themes_Animated.new(this.root)
    ]);
    
    // Create chart
    this.receiptsChart = this.root.container.children.push(am5xy.XYChart.new(this.root, {
      panX: false,
      panY: false,
      wheelX: "panX",
      wheelY: "zoomX",
      paddingLeft: 0,
      paddingRight: 1
    }));
    
    // Add cursor
    const cursor = this.receiptsChart.set("cursor", am5xy.XYCursor.new(this.root, {}));
    cursor.lineY.set("visible", false);
    
    // Create axes
    const xRenderer = am5xy.AxisRendererX.new(this.root, { 
      minGridDistance: 50,
      minorGridEnabled: true
    });
    
    const xAxis = this.receiptsChart.xAxes.push(am5xy.DateAxis.new(this.root, {
      maxZoomCount: 1000,
      baseInterval: {
        timeUnit: "day",
        count: 1
      },
      renderer: xRenderer,
      tooltip: am5.Tooltip.new(this.root, {})
    }));
    
    const yAxis = this.receiptsChart.yAxes.push(am5xy.ValueAxis.new(this.root, {
      renderer: am5xy.AxisRendererY.new(this.root, {
        strokeDasharray: [1, 5]
      })
    }));
    
    // Create series
    const series = this.receiptsChart.series.push(am5xy.LineSeries.new(this.root, {
      name: "Vásárlások",
      xAxis: xAxis,
      yAxis: yAxis,
      valueYField: "value",
      valueXField: "date",
      tooltip: am5.Tooltip.new(this.root, {
        labelText: "{valueY} vásárlás"
      })
    }));
    
    // Add circle bullet
    series.bullets.push(() => {
      return am5.Bullet.new(this.root!, {
        sprite: am5.Circle.new(this.root!, {
          strokeWidth: 2,
          radius: 5,
          stroke: series.get("stroke"),
          fill: am5.color(0xffffff)
        })
      });
    });
    
    // Subscribe to data changes
    const receiptsSub = this.receiptsTimeSeries$.subscribe(data => {
      if (data) {
        const formattedData = data.map(d => ({
          date: new Date(d.date).getTime(),
          value: d.value
        }));
        series.data.setAll(formattedData);
      }
    });
    
    this.subscriptions.push(receiptsSub);
  }

  private createAmountsChart() {
    // Create root element
    this.root2 = am5.Root.new("amounts-chart");
    
    // Set themes
    this.root2.setThemes([
      am5themes_Animated.new(this.root2)
    ]);
    
    // Create chart
    this.amountsChart = this.root2.container.children.push(am5xy.XYChart.new(this.root2, {
      panX: false,
      panY: false,
      wheelX: "panX",
      wheelY: "zoomX",
      paddingLeft: 0,
      paddingRight: 1
    }));
    
    // Add cursor
    const cursor = this.amountsChart.set("cursor", am5xy.XYCursor.new(this.root2, {}));
    cursor.lineY.set("visible", false);
    
    // Create axes
    const xRenderer = am5xy.AxisRendererX.new(this.root2, { 
      minGridDistance: 50,
      minorGridEnabled: true
    });
    
    const xAxis = this.amountsChart.xAxes.push(am5xy.DateAxis.new(this.root2, {
      maxZoomCount: 1000,
      baseInterval: {
        timeUnit: "day",
        count: 1
      },
      renderer: xRenderer,
      tooltip: am5.Tooltip.new(this.root2, {})
    }));
    
    const yAxis = this.amountsChart.yAxes.push(am5xy.ValueAxis.new(this.root2, {
      renderer: am5xy.AxisRendererY.new(this.root2, {
        strokeDasharray: [1, 5]
      })
    }));
    
    // Create series
    const series = this.amountsChart.series.push(am5xy.LineSeries.new(this.root2, {
      name: "Összeg",
      xAxis: xAxis,
      yAxis: yAxis,
      valueYField: "value",
      valueXField: "date",
      tooltip: am5.Tooltip.new(this.root2, {
        labelText: "{valueY} Ft"
      })
    }));
    
    // Add circle bullet
    series.bullets.push(() => {
      return am5.Bullet.new(this.root2!, {
        sprite: am5.Circle.new(this.root2!, {
          strokeWidth: 2,
          radius: 5,
          stroke: series.get("stroke"),
          fill: am5.color(0xffffff)
        })
      });
    });
    
    // Subscribe to data changes
    const amountsSub = this.amountsTimeSeries$.subscribe(data => {
      if (data) {
        const formattedData = data.map(d => ({
          date: new Date(d.date).getTime(),
          value: d.value
        }));
        series.data.setAll(formattedData);
      }
    });
    
    this.subscriptions.push(amountsSub);
  }
}
