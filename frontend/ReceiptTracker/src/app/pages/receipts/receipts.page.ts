import {Component, OnDestroy, OnInit, signal} from '@angular/core';
import {
  IonAccordion,
  IonAccordionGroup,
  IonButton,
  IonCard,
  IonCardContent,
  IonCardHeader,
  IonCardTitle,
  IonContent,
  IonDatetime,
  IonDatetimeButton,
  IonHeader,
  IonIcon,
  IonItem,
  IonLabel,
  IonList,
  IonModal,
  IonNote,
  IonSearchbar,
  IonSelect,
  IonSelectOption,
  IonSpinner,
  IonTitle,
  IonToolbar
} from '@ionic/angular/standalone';
import {MarketOut, ReceiptListOut, ReceiptOut, ReceiptService} from '../../api';
import {FormControl, ReactiveFormsModule} from '@angular/forms';
import {CommonModule} from '@angular/common';
import {AlertController, ModalController, ToastController} from '@ionic/angular';
import {ReceiptEditModalComponent} from './receipt-edit.modal';
import {chevronDownOutline, chevronUpOutline, downloadOutline, searchOutline} from "ionicons/icons";
import {Store} from "@ngrx/store";
import {selectAccessToken} from "../../store/auth/auth.selectors";
import {take, tap} from "rxjs/operators";
import {Subject, takeUntil} from 'rxjs';

const MIN_DATE = new Date(2023, 0, 1).getTime();
const now = new Date();
const MAX_DATE = new Date(now.getFullYear(), now.getMonth(), now.getDate(), 23, 59, 59, 999).getTime();

@Component({
  selector: 'app-receipts',
  standalone: true,
  templateUrl: './receipts.page.html',
  styleUrls: ['./receipts.page.scss'],
  imports: [
    IonHeader, IonToolbar, IonTitle, IonContent, IonList, IonItem, IonLabel, IonDatetime, IonDatetimeButton, IonModal, IonSelect, IonSelectOption, IonAccordionGroup, IonAccordion, IonSearchbar, IonSpinner, IonNote, ReactiveFormsModule, CommonModule,
    IonButton, IonIcon, IonCard, IonCardHeader, IonCardTitle, IonCardContent
  ],
  providers: [ReceiptService]
})
export class ReceiptsPage implements OnInit, OnDestroy {
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

  icons = { chevronDownOutline, chevronUpOutline, searchOutline, downloadOutline };

  // Unsubscribe subject for takeUntil pattern
  private readonly unsub$ = new Subject<void>();

  constructor(
    private receiptService: ReceiptService,
    private alertController: AlertController,
    private modalController: ModalController,
    private toastController: ToastController,
    private store: Store
  ) {}

  ngOnInit() {
    this.loadMarkets();
    this.loadReceipts();
    this.setupFormSubscriptions();
  }

  ngOnDestroy() {
    this.unsub$.next();
    this.unsub$.complete();
  }

  private setupFormSubscriptions() {
    // Szűrők változására újratölt
    this.itemName.valueChanges.pipe(
      takeUntil(this.unsub$)
    ).subscribe(() => this.onFilterChange());

    this.marketId.valueChanges.pipe(
      takeUntil(this.unsub$)
    ).subscribe(() => this.onFilterChange());

    this.orderBy.valueChanges.pipe(
      takeUntil(this.unsub$)
    ).subscribe(() => this.onFilterChange());

    this.orderDir.valueChanges.pipe(
      takeUntil(this.unsub$)
    ).subscribe(() => this.onFilterChange());
  }

  onDateFromChange(ev: CustomEvent) {
    const val = ev.detail.value;
    if (val) {
      const newDate = new Date(val).getTime();
      const [, to] = this.dateRange();
      this.dateRange.set([newDate, to]);
      this.onFilterChange();
    }
  }

  onDateToChange(ev: CustomEvent) {
    const val = ev.detail.value;
    if (val) {
      const newDate = new Date(val).getTime();
      const [from] = this.dateRange();
      this.dateRange.set([from, newDate]);
      this.onFilterChange();
    }
  }

  getDateFromISO(): string {
    return new Date(this.dateRange()[0]).toISOString();
  }

  getDateToISO(): string {
    return new Date(this.dateRange()[1]).toISOString();
  }

  onFilterChange() {
    this.skip.set(0); // új szűrésnél mindig első oldal
    this.loadReceipts();
  }

  loadMarkets() {
    this.marketLoading.set(true);
    this.receiptService.getMarketsReceiptMarketsGet(0, 100).pipe(
      takeUntil(this.unsub$)
    ).subscribe({
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
    ).pipe(
      takeUntil(this.unsub$)
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

  async confirmDelete(receipt: ReceiptOut) {
    const alert = await this.alertController.create({
      header: 'Biztosan törlöd?',
      message: `A(z) <b>${receipt.market.name}</b> #${receipt.receipt_number} blokk véglegesen törlődik!`,
      buttons: [
        {
          text: 'Mégse',
          role: 'cancel'
        },
        {
          text: 'Törlés',
          role: 'destructive',
          handler: () => this.deleteReceipt(receipt.id)
        }
      ]
    });

    await alert.present();
  }

  deleteReceipt(receiptId: number) {
    this.receiptService.deleteReceiptReceiptReceiptReceiptIdDelete(receiptId, 'body').pipe(
      takeUntil(this.unsub$)
    ).subscribe({
      next: () => {
        this.showToast('Blokk sikeresen törölve!', 'success');
        this.loadReceipts(); // Újratöltés
      },
      error: (error: any) => {
        console.error('Error deleting receipt:', error);
        this.showToast('Hiba a törlés során!', 'danger');
      }
    });
  }

  downloadImage(receipt: ReceiptOut) {
    this.store.select(selectAccessToken).pipe(
      take(1),
      tap(token => {
        if (!token) {
          this.showToast('Nincs érvényes hozzáférési token!', 'danger');
          return;
        }

        // API endpoint URL összeállítása
        const baseUrl = 'http://192.168.88.20:8000'; // TODO: environment-ből
        const downloadUrl = `${baseUrl}/receipt/receipt/${receipt.id}/image`;

        // Fetch request a token-nel
        fetch(downloadUrl, {
          method: 'GET',
          headers: {
            'Authorization': `Bearer ${token}`
          }
        })
        .then(response => {
          if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
          }
          return response.blob();
        })
        .then(blob => {
          // Fájl letöltése
          const url = window.URL.createObjectURL(blob);
          const a = document.createElement('a');
          a.style.display = 'none';
          a.href = url;
          a.download = `receipt_${receipt.market.name}_${receipt.receipt_number}.jpg`;
          document.body.appendChild(a);
          a.click();
          window.URL.revokeObjectURL(url);
          document.body.removeChild(a);
          this.showToast('Kép sikeresen letöltve!', 'success');
        })
        .catch(error => {
          console.error('Download error:', error);
          this.showToast('Hiba a letöltés során!', 'danger');
        });
      })
    ).subscribe();
  }

  async editReceipt(receipt: ReceiptOut) {
    const modal = await this.modalController.create({
      component: ReceiptEditModalComponent,
      componentProps: {
        receipt: receipt,
        markets: this.markets(),
      },
      breakpoints: [0, 1],
      initialBreakpoint: 1
    });

    await modal.present();

    const { data } = await modal.onWillDismiss();
    if (data && data.updated) {
      this.updateReceipt(receipt.id, data.receiptData);
    }
  }

  updateReceipt(receiptId: number, data: any) {
    this.receiptService.updateReceiptReceiptReceiptIdPut(receiptId, data, 'body').pipe(
      takeUntil(this.unsub$)
    ).subscribe({
      next: () => {
        this.showToast('Blokk sikeresen frissítve!', 'success');
        this.loadReceipts(); // Újratöltés
      },
      error: (error: any) => {
        console.error('Error updating receipt:', error);
        this.showToast('Hiba a frissítés során!', 'danger');
      }
    });
  }

  private async showToast(message: string, color: 'success' | 'danger') {
    const toast = await this.toastController.create({
      message: message,
      duration: 2000,
      color: color,
      position: 'top'
    });
    await toast.present();
  }

  protected readonly Math = Math;
  protected readonly MIN_DATE = MIN_DATE;
  protected readonly MAX_DATE = MAX_DATE;
}
