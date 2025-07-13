import {Component, inject, Input, OnChanges, OnDestroy, OnInit, SimpleChanges} from '@angular/core';
import {CommonModule} from '@angular/common';
import {IonCard, IonCardContent, IonCardHeader, IonCardTitle, IonSpinner} from '@ionic/angular/standalone';
import {MarketTotalReceipts, MarketTotalReceiptsList, StatisticService} from '../../../../api';
import {Subject, takeUntil} from 'rxjs';
import {DarkModeService} from '../../../../services/dark-mode.service';

// amCharts 5 imports
import * as am5 from '@amcharts/amcharts5';
import * as am5xy from '@amcharts/amcharts5/xy';
import am5themes_Animated from '@amcharts/amcharts5/themes/Animated';
import am5themes_Dark from '@amcharts/amcharts5/themes/Dark';

@Component({
  selector: 'app-market-total-receipts-chart',
  standalone: true,
  imports: [
    CommonModule,
    IonCard,
    IonCardHeader,
    IonCardTitle,
    IonCardContent,
    IonSpinner
  ],
  templateUrl: './market-total-receipts-chart.component.html',
  styleUrls: ['./market-total-receipts-chart.component.scss']
})
export class MarketTotalReceiptsChartComponent implements OnInit, OnChanges, OnDestroy {
  @Input() dateFrom!: string;
  @Input() dateTo!: string;
  @Input() userId?: number | null;

  private statisticService = inject(StatisticService);
  private darkModeService = inject(DarkModeService);
  private root?: am5.Root;
  private chart?: am5xy.XYChart;
  private readonly unsub$ = new Subject<void>();

  chartId = Math.random().toString(36).substr(2, 9);
  isLoading = false;

  ngOnInit() {
      this.loadData();

    // Subscribe to dark mode changes
    this.darkModeService.isDarkMode$.pipe(
      takeUntil(this.unsub$)
    ).subscribe(() => {
      if (this.chart) {
        this.loadData();
      }
    });
  }

  ngOnChanges(changes: SimpleChanges) {
    if (changes['dateFrom'] || changes['dateTo'] || changes['userId']) {
      // Only reload data if chart is already initialized
      if (this.chart) {
        this.loadData();
      }
    }
  }

  ngOnDestroy() {
    this.unsub$.next();
    this.unsub$.complete();

    if (this.root) {
      this.root.dispose();
    }
  }

  private initializeChart() {
    if (this.root) {
      this.root.dispose();
    }

    // Create root element
    this.root = am5.Root.new(`market-total-receipts-chart-${this.chartId}`);

    // Set themes based on dark mode
    const themes = [am5themes_Animated.new(this.root)];
    if (this.darkModeService.getCurrentDarkMode()) {
      // @ts-ignore
      themes.push(am5themes_Dark.new(this.root));
    }
    this.root.setThemes(themes);

    // Create chart
    this.chart = this.root.container.children.push(am5xy.XYChart.new(this.root, {
      panX: false,
      panY: false,
      wheelX: "panX",
      wheelY: "zoomX",
      paddingLeft: 0,
      paddingRight: 1
    }));

    // Add cursor
    const cursor = this.chart.set("cursor", am5xy.XYCursor.new(this.root, {}));
    cursor.lineY.set("visible", false);

    // Create axes
    const xRenderer = am5xy.AxisRendererX.new(this.root, {
      minGridDistance: 50,
      minorGridEnabled: true
    });

    const xAxis = this.chart.xAxes.push(am5xy.CategoryAxis.new(this.root, {
      categoryField: "category",
      maxZoomCount: 1000,
      renderer: xRenderer,
      tooltip: am5.Tooltip.new(this.root, {})
    }));

    const yAxis = this.chart.yAxes.push(am5xy.ValueAxis.new(this.root, {
      renderer: am5xy.AxisRendererY.new(this.root, {
        strokeDasharray: [1, 5]
      })
    }));

    // Create series
    const series = this.chart.series.push(am5xy.ColumnSeries.new(this.root, {
      name: "Összes blokk",
      xAxis: xAxis,
      yAxis: yAxis,
      valueYField: "value",
      categoryXField: "category",
      tooltip: am5.Tooltip.new(this.root, {
        labelText: "{valueY} db"
      })
    }));

    // Add bullet
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
  }

  private updateChartData(data: any[]) {
    if (!this.chart) return;

    const xAxis = this.chart.xAxes.getIndex(0) as am5xy.CategoryAxis<am5xy.AxisRenderer>;
    const series = this.chart.series.getIndex(0) as am5xy.ColumnSeries;

    if (xAxis && series) {
      xAxis.data.setAll(data);
      series.data.setAll(data);
    }
  }

  private loadData() {
    if (!this.dateFrom || !this.dateTo) return;
    this.isLoading = true;

    this.statisticService.getMarketTotalReceiptsStatisticMarketTotalReceiptsGet(
      this.dateFrom,
      this.dateTo,
      this.userId || undefined
    ).pipe(
      takeUntil(this.unsub$)
    ).subscribe({
      next: (data: MarketTotalReceiptsList) => {
        this.isLoading = false;
        this.initializeChart();
        const markets: MarketTotalReceipts[] = data.markets || [];
        const chartData = markets.map(m => ({ category: m.market_name, value: m.total_receipts }));
        this.updateChartData(chartData);
      },
      error: err => {
        console.error('Error loading market total receipts:', err);
        this.isLoading = false;
        this.updateChartData([]);
      }
    });
  }
}
