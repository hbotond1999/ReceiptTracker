import { Component, signal } from '@angular/core';
import {
  IonHeader,
  IonToolbar,
  IonTitle,
  IonContent,
  IonList,
  IonItem,
  IonLabel,
  IonInput,
  IonDatetime,
  IonSelect,
  IonSelectOption,
  IonButton,
  IonIcon,
  IonAccordionGroup,
  IonAccordion,
  IonSearchbar,
  IonSpinner,
  IonNote,
  IonRange
} from '@ionic/angular/standalone';
import { ReceiptService } from '../../api/api/receipt.service';
import { MarketOut } from '../../api/model/marketOut';
import { ReceiptOut } from '../../api/model/receiptOut';
import { ReceiptListOut } from '../../api/model/receiptListOut';
import { FormControl, ReactiveFormsModule } from '@angular/forms';
import { chevronDownOutline, chevronUpOutline, searchOutline } from 'ionicons/icons';
import { CommonModule } from '@angular/common';

const MIN_DATE = new Date(2000, 0, 1).getTime();
const now = new Date();
const MAX_DATE = new Date(now.getFullYear(), now.getMonth(), now.getDate(), 23, 59, 59, 999).getTime();

@Component({
  selector: 'app-receipts',
  standalone: true,
  templateUrl: './receipts.page.html',
  styleUrls: ['./receipts.page.scss'],
  imports: [
    IonHeader, IonToolbar, IonTitle, IonContent, IonList, IonItem, IonLabel, IonInput, IonDatetime, IonSelect, IonSelectOption, IonButton, IonIcon, IonAccordionGroup, IonAccordion, IonSearchbar, IonSpinner, IonNote, ReactiveFormsModule, CommonModule, IonRange
  ],
  providers: [ReceiptService]
})
export class ReceiptsPage {
  receipts = signal<ReceiptOut[]>([]);
  total = signal(0);
  skip = signal(0);
  limit = signal(10);
  hasNext = signal(false);
  hasPrevious = signal(false);
  loading = signal(false);

  // Szűrők
  itemName = new FormControl('');
  dateRange = signal<[number, number]>([MIN_DATE, MAX_DATE]);
  marketId = new FormControl<number|null>(null);
  orderBy = new FormControl('date');
  orderDir = new FormControl('desc');

  // Boltok
  markets = signal<MarketOut[]>([]);
  marketLoading = signal(false);

  // Accordion nyitva tartás
  openReceiptId = signal<number|null>(null);

  icons = { chevronDownOutline, chevronUpOutline, searchOutline };

  constructor(private receiptService: ReceiptService) {
    this.loadMarkets();
    this.loadReceipts();
    // Szűrők változására újratölt
    this.itemName.valueChanges.subscribe(() => this.onFilterChange());
    this.marketId.valueChanges.subscribe(() => this.onFilterChange());
    this.orderBy.valueChanges.subscribe(() => this.onFilterChange());
    this.orderDir.valueChanges.subscribe(() => this.onFilterChange());
  }

  onDateRangeChange(ev: CustomEvent) {
    const val = ev.detail.value;
    if (val && typeof val.lower === 'number' && typeof val.upper === 'number') {
      this.dateRange.set([val.lower, val.upper]);
      this.onFilterChange();
    }
  }

  onDateRangeInput(ev: CustomEvent) {
    const val = ev.detail.value;
    if (val && typeof val.lower === 'number' && typeof val.upper === 'number') {
      this.dateRange.set([val.lower, val.upper]);
    }
  }

  onFilterChange() {
    this.skip.set(0); // új szűrésnél mindig első oldal
    this.loadReceipts();
  }

  loadMarkets() {
    this.marketLoading.set(true);
    this.receiptService.getMarketsReceiptMarketsGet(0, 100).subscribe({
      next: (markets) => this.markets.set(markets),
      complete: () => this.marketLoading.set(false)
    });
  }

  loadReceipts() {
    this.loading.set(true);
    const [from, to] = this.dateRange();
    this.receiptService.getReceiptsReceiptGet(
      this.skip(),
      this.limit(),
      undefined, // userId
      this.marketId.value || undefined,
      undefined, // marketName
      this.itemName.value || undefined,
      new Date(from).toISOString(),
      new Date(to).toISOString(),
      this.orderBy.value || undefined,
      this.orderDir.value || undefined,
      'body'
    ).subscribe({
      next: (result: ReceiptListOut) => {
        this.receipts.set(result.receipts);
        this.total.set(result.total);
        this.hasNext.set(result.has_next);
        this.hasPrevious.set(result.has_previous);
      },
      complete: () => this.loading.set(false)
    });
  }

  pageChange(direction: 'next' | 'prev') {
    if (direction === 'next' && this.hasNext()) {
      this.skip.set(this.skip() + this.limit());
      this.loadReceipts();
    } else if (direction === 'prev' && this.hasPrevious()) {
      this.skip.set(Math.max(0, this.skip() - this.limit()));
      this.loadReceipts();
    }
  }

  toggleAccordion(receiptId: number) {
    this.openReceiptId.set(this.openReceiptId() === receiptId ? null : receiptId);
  }

  clearFilters() {
    this.itemName.setValue('');
    this.dateRange.set([MIN_DATE, MAX_DATE]);
    this.marketId.setValue(null);
    this.orderBy.setValue('date');
    this.orderDir.setValue('desc');
  }

  protected readonly Math = Math;
  protected readonly MIN_DATE = MIN_DATE;
  protected readonly MAX_DATE = MAX_DATE;
}
