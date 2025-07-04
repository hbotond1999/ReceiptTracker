// @ts-nocheck
import { Component, Input, OnChanges, OnDestroy, OnInit, SimpleChanges, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import {
  IonCard,
  IonCardHeader,
  IonCardTitle,
  IonCardContent,
  IonSpinner
} from '@ionic/angular/standalone';
import { ReceiptService } from '../../../../api/api/receipt.service';
import { MarketTotalSpentList } from '../../../../api/model/marketTotalSpentList';
import { MarketTotalSpent } from '../../../../api/model/marketTotalSpent';
import { Subscription } from 'rxjs';
import { DarkModeService } from '../../../../services/dark-mode.service';

// amCharts 5 imports
import * as am5 from '@amcharts/amcharts5';
import * as am5xy from '@amcharts/amcharts5/xy';
import am5themes_Animated from '@amcharts/amcharts5/themes/Animated';
import am5themes_Dark from '@amcharts/amcharts5/themes/Dark';

@Component({
  selector: 'app-market-total-spent-chart',
  standalone: true,
  imports: [
    CommonModule,
    IonCard,
    IonCardHeader,
    IonCardTitle,
    IonCardContent,
    IonSpinner
  ],
  templateUrl: './market-total-spent-chart.component.html',
  styleUrls: ['./market-total-spent-chart.component.scss']
})
export class MarketTotalSpentChartComponent implements OnInit, OnChanges, OnDestroy {
  @Input() dateFrom!: string;
  @Input() dateTo!: string;
  @Input() userId?: number | null;

  private receiptService = inject(ReceiptService);
  private darkModeService = inject(DarkModeService);
  private root?: am5.Root;
  private chart?: am5xy.XYChart;
  private subscription?: Subscription;
  private darkModeSubscription?: Subscription;
  
  chartId = Math.random().toString(36).substr(2, 9);
  isLoading = signal(false);

  ngOnInit() {
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
    if (changes['dateFrom'] || changes['dateTo'] || changes['userId']) {
      if (this.chart) {
        this.loadData();
      }
    }
  }

  ngOnDestroy() {
    this.cleanup();
  }

  private initializeChart() {
    if (this.root) {
      this.root.dispose();
    }

    this.root = am5.Root.new(`market-total-spent-chart-${this.chartId}`);
    
    // Set themes based on dark mode
    const themes = [am5themes_Animated.new(this.root)];
    if (this.darkModeService.getCurrentDarkMode()) {
      themes.push(am5themes_Dark.new(this.root));
    }
    this.root.setThemes(themes);

    this.chart = this.root.container.children.push(am5xy.XYChart.new(this.root, {
      panX: false,
      panY: false,
      wheelY: 'zoomX',
      layout: this.root.verticalLayout
    }));

    // Category axis (markets)
    const xAxis = this.chart.xAxes.push(am5xy.CategoryAxis.new(this.root, {
      categoryField: 'category',
      renderer: am5xy.AxisRendererX.new(this.root, {
        minGridDistance: 20,
        cellStartLocation: 0.1,
        cellEndLocation: 0.9
      })
    }));

    xAxis.get("renderer").labels.template.setAll({
      rotation: -45,
      centerY: am5.p50,
      centerX: am5.p100,
      paddingRight: 10
    });

    // Value axis (HUF)
    const yAxis = this.chart.yAxes.push(am5xy.ValueAxis.new(this.root, {
      renderer: am5xy.AxisRendererY.new(this.root, {})
    }));

    // Column series
    const series = this.chart.series.push(am5xy.ColumnSeries.new(this.root, {
      name: 'Összköltés',
      xAxis: xAxis,
      yAxis: yAxis,
      valueYField: 'value',
      categoryXField: 'category',
      tooltip: am5.Tooltip.new(this.root, {
        labelText: '{valueY} Ft'
      })
    }));

    series.columns.template.setAll({
      tooltipText: '{categoryX}: {valueY} Ft',
      width: am5.percent(80)
    });
  }

  private loadData() {
    if (!this.dateFrom || !this.dateTo) return;

    this.isLoading.set(true);

    if (this.subscription) {
      this.subscription.unsubscribe();
    }

    this.subscription = this.receiptService.getMarketTotalSpentStatisticStatisticsMarketTotalSpentGet(
      this.dateFrom,
      this.dateTo,
      this.userId || undefined
    ).subscribe({
      next: (data: MarketTotalSpentList) => {
        this.isLoading.set(false);
        const markets: MarketTotalSpent[] = data.markets || [];
        const chartData = markets.map(m => ({ category: m.market_name, value: m.total_spent }));
        this.updateChartData(chartData);
      },
      error: err => {
        console.error('Error loading market total spent:', err);
        this.isLoading.set(false);
        this.updateChartData([]);
      }
    });
  }

  private updateChartData(data: any[]) {
    if (!this.chart) return;
    const xAxis = this.chart.xAxes.getIndex(0) as am5xy.CategoryAxis;
    const series = this.chart.series.getIndex(0) as am5xy.ColumnSeries;
    xAxis.data.setAll(data);
    series.data.setAll(data);
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
