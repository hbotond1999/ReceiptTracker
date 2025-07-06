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
  IonDatetimeButton,
  IonModal,
  IonSelect,
  IonSelectOption,
  IonButton,
  IonIcon,
  IonAccordionGroup,
  IonAccordion,
  IonSearchbar,
  IonSpinner,
  IonNote,
  IonCard,
  IonCardHeader,
  IonCardTitle,
  IonCardContent
} from '@ionic/angular/standalone';
import { ReceiptService } from '../../api/api/receipt.service';
import { MarketOut } from '../../api/model/marketOut';
import { ReceiptOut } from '../../api/model/receiptOut';
import { ReceiptListOut } from '../../api/model/receiptListOut';
import { FormControl, ReactiveFormsModule } from '@angular/forms';
import { CommonModule } from '@angular/common';
import { AlertController, ModalController, ToastController } from '@ionic/angular';
import { ReceiptEditModalComponent } from './receipt-edit.modal';
import {chevronDownOutline, chevronUpOutline, searchOutline, downloadOutline} from "ionicons/icons";
import {Store} from "@ngrx/store";
import {selectAccessToken} from "../../store/auth/auth.selectors";
import {take, tap} from "rxjs/operators";

const MIN_DATE = new Date(2023, 0, 1).getTime();
const now = new Date();
const MAX_DATE = new Date(now.getFullYear(), now.getMonth(), now.getDate(), 23, 59, 59, 999).getTime();

@Component({
  selector: 'app-receipts',
  standalone: true,
  templateUrl: './receipts.page.html',
  styleUrls: ['./receipts.page.scss'],
  imports: [
    IonHeader, IonToolbar, IonTitle, IonContent, IonList, IonItem, IonLabel, IonInput, IonDatetime, IonDatetimeButton, IonModal, IonSelect, IonSelectOption, IonAccordionGroup, IonAccordion, IonSearchbar, IonSpinner, IonNote, ReactiveFormsModule, CommonModule,
    ReceiptEditModalComponent, IonButton, IonIcon, IonCard, IonCardHeader, IonCardTitle, IonCardContent
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

  icons = { chevronDownOutline, chevronUpOutline, searchOutline, downloadOutline };

  constructor(
    private receiptService: ReceiptService,
    private alertController: AlertController,
    private modalController: ModalController,
    private toastController: ToastController,
    private store: Store
  ) {
    this.loadMarkets();
    this.loadReceipts();
    // Szűrők változására újratölt
    this.itemName.valueChanges.subscribe(() => this.onFilterChange());
    this.marketId.valueChanges.subscribe(() => this.onFilterChange());
    this.orderBy.valueChanges.subscribe(() => this.onFilterChange());
    this.orderDir.valueChanges.subscribe(() => this.onFilterChange());
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
    this.receiptService.deleteReceiptReceiptReceiptReceiptIdDelete(receiptId, 'body').subscribe({
      next: () => this.loadReceipts(),
      error: (err: any) => {
        this.alertController.create({
          header: 'Hiba',
          message: 'A törlés nem sikerült!',
          buttons: ['OK']
        }).then(a => a.present());
      }
    });
  }

  downloadImage(receipt: ReceiptOut) {
    // API endpoint URL összeállítása
    const baseUrl = this.receiptService.configuration.basePath;
    const downloadUrl = `${baseUrl}/receipt/receipt/${receipt.id}/image`;

    // Fájl letöltése
    const link = document.createElement('a');
    link.href = downloadUrl;

    // Fájl kiterjesztés meghatározása
    let defaultFilename = receipt.original_filename;
    link.download = defaultFilename;
    
    // Authorization header hozzáadása
    this.store.select(selectAccessToken).pipe(
      take(1),
      tap((token) => {
        fetch(downloadUrl, {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        })
          .then(response => {
            if (!response.ok) {
              throw new Error('Letöltési hiba');
            }
            return response.blob();
          })
          .then(blob => {
            const url = window.URL.createObjectURL(blob);
            link.href = url;
           
            link.click();
            window.URL.revokeObjectURL(url);
            this.toastController.create({
              message: 'Kép letöltése sikeres!',
              duration: 2000,
              color: 'success'
            }).then(toast => toast.present());
          })
          .catch(error => {
            console.error('Letöltési hiba:', error);
            this.toastController.create({
              message: 'A letöltés nem sikerült!',
              duration: 2000,
              color: 'danger'
            }).then(toast => toast.present());
          });
      })
    ).subscribe()
  }

  async editReceipt(receipt: ReceiptOut) {
    const modal = await this.modalController.create({
      component: ReceiptEditModalComponent,
      componentProps: {
        receipt,
        markets: this.markets()
      },
      breakpoints: [0, 1],
      initialBreakpoint: 1
    });
    modal.onWillDismiss().then((result) => {
      if (result.data && result.data.save) {
        this.updateReceipt(receipt.id, result.data.save);
      }
    });
    await modal.present();
  }

  updateReceipt(receiptId: number, data: any) {
    this.receiptService.updateReceiptReceiptReceiptIdPut(receiptId, data, 'body').subscribe({
      next: () => {
        this.loadReceipts();
        this.toastController.create({
          message: 'Blokk sikeresen frissítve!',
          duration: 2000,
          color: 'success'
        }).then(t => t.present());
      },
      error: () => {
        this.toastController.create({
          message: 'A frissítés nem sikerült!',
          duration: 2000,
          color: 'danger'
        }).then(t => t.present());
      }
    });
  }

  protected readonly Math = Math;
  protected readonly MIN_DATE = MIN_DATE;
  protected readonly MAX_DATE = MAX_DATE;
}
