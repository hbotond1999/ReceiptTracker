import { Component, Input, OnChanges, OnDestroy, OnInit, SimpleChanges, inject, ElementRef, ViewChild } from '@angular/core';
import { CommonModule } from '@angular/common';
import {
  IonCard,
  IonCardHeader,
  IonCardTitle,
  IonCardContent,
  IonSpinner
} from '@ionic/angular/standalone';
import { ReceiptService } from '../../../../api/api/receipt.service';
import { TimeSeriesData } from '../../../../api/model/timeSeriesData';
import { AggregationType } from '../../../../api/model/aggregationType';
import { Subscription } from 'rxjs';
import { DarkModeService } from '../../../../services/dark-mode.service';

// amCharts 5 imports
import * as am5 from '@amcharts/amcharts5';
import * as am5xy from '@amcharts/amcharts5/xy';
import am5themes_Animated from '@amcharts/amcharts5/themes/Animated';
import am5themes_Dark from '@amcharts/amcharts5/themes/Dark';

@Component({
  selector: 'app-receipts-chart',
  standalone: true,
  imports: [
    CommonModule,
    IonCard,
    IonCardHeader,
    IonCardTitle,
    IonCardContent,
    IonSpinner
  ],
  templateUrl: './receipts-chart.component.html',
  styleUrls: ['./receipts-chart.component.scss']
})
export class ReceiptsChartComponent implements OnInit, OnChanges, OnDestroy {
  @Input() dateFrom!: string;
  @Input() dateTo!: string;
  @Input() userId?: number | null;
  @Input() aggregationType?: AggregationType;

  @ViewChild('chartContainer', { static: false }) chartContainer!: ElementRef;

  private receiptService = inject(ReceiptService);
  private darkModeService = inject(DarkModeService);
  private root?: am5.Root;
  private chart?: am5xy.XYChart;
  private subscription?: Subscription;
  private darkModeSubscription?: Subscription;

  chartId = Math.random().toString(36).substr(2, 9);
  isLoading = false;

  ngOnInit() {
    // Initialize chart after a short delay to ensure DOM is ready
    setTimeout(() => {
      this.initializeChart();
      this.loadData();
    }, 100);

    // Subscribe to dark mode changes
    this.darkModeSubscription = this.darkModeService.isDarkMode$.subscribe(() => {
      if (this.chart) {
        // Reinitialize chart with new theme
        this.initializeChart();
        this.loadData();
      }
    });
  }

  ngOnChanges(changes: SimpleChanges) {
    if (changes['dateFrom'] || changes['dateTo'] || changes['userId'] || changes['aggregationType']) {
      // Only reload data if chart is already initialized
      if (this.chart) {
        this.loadData();
      }
    }
  }

  ngOnDestroy() {
    this.cleanup();
  }

  private getBaseInterval() {
    switch (this.aggregationType) {
      case AggregationType.Month:
        return { timeUnit: "month" as any, count: 1 };
      case AggregationType.Year:
        return { timeUnit: "year" as any, count: 1 };
      default:
        return { timeUnit: "day" as any, count: 1 };
    }
  }

  private formatDateForChart(dateValue: any): number {
    if (typeof dateValue === 'string') {
      // For day aggregation, it's a date string
      return new Date(dateValue).getTime();
    } else if (typeof dateValue === 'number') {
      // For month/year aggregation, it's a numeric value
      if (this.aggregationType === AggregationType.Year) {
        // Year format: YYYY -> create date for Jan 1st of that year
        return new Date(dateValue, 0, 1).getTime();
      } else if (this.aggregationType === AggregationType.Month) {
        // Month format: YYYYMM -> create date for 1st of that month
        const year = Math.floor(dateValue / 100);
        const month = dateValue % 100;
        return new Date(year, month - 1, 1).getTime();
      }
    }
    // Fallback
    return new Date(dateValue).getTime();
  }

  private initializeChart() {
    if (this.root) {
      this.root.dispose();
    }

    // Create root element
    this.root = am5.Root.new(`receipts-chart-${this.chartId}`);

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

    const xAxis = this.chart.xAxes.push(am5xy.DateAxis.new(this.root, {
      maxZoomCount: 1000,
      baseInterval: this.getBaseInterval(),
      renderer: xRenderer,
      tooltip: am5.Tooltip.new(this.root, {})
    }));

    const yAxis = this.chart.yAxes.push(am5xy.ValueAxis.new(this.root, {
      renderer: am5xy.AxisRendererY.new(this.root, {
        strokeDasharray: [1, 5]
      })
    }));

    // Create series
    const series = this.chart.series.push(am5xy.LineSeries.new(this.root, {
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

    this.subscription = this.receiptService.getReceiptsTimeseriesStatisticTimeseriesReceiptsGet(
      this.dateFrom,
      this.dateTo,
      this.userId || undefined,
      this.aggregationType || AggregationType.Day
    ).subscribe({
      next: (data: TimeSeriesData[]) => {
        this.isLoading = false;
        if (data && this.chart) {
          const formattedData = data.map(d => ({
            date: this.formatDateForChart(d.date),
            value: d.value
          }));

          const series = this.chart.series.getIndex(0) as am5xy.LineSeries;
          if (series) {
            series.data.setAll(formattedData);
          }
        }
      },
      error: (error) => {
        this.isLoading = false;
        console.error('Error loading receipts time series data:', error);
      }
    });
  }

  private cleanup() {
    if (this.subscription) {
      this.subscription.unsubscribe();
    }

    if (this.darkModeSubscription) {
      this.darkModeSubscription.unsubscribe();
    }

    if (this.root) {
      this.root.dispose();
    }
  }
}
