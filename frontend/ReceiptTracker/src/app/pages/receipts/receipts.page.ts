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
import { CommonModule } from '@angular/common';
import { AlertController, ModalController, ToastController } from '@ionic/angular';
import { ReceiptEditModalComponent } from './receipt-edit.modal';
import {chevronDownOutline, chevronUpOutline, searchOutline, downloadOutline} from "ionicons/icons";

const MIN_DATE = new Date(2000, 0, 1).getTime();
const now = new Date();
const MAX_DATE = new Date(now.getFullYear(), now.getMonth(), now.getDate(), 23, 59, 59, 999).getTime();

@Component({
  selector: 'app-receipts',
  standalone: true,
  templateUrl: './receipts.page.html',
  styleUrls: ['./receipts.page.scss'],
  imports: [
    IonHeader, IonToolbar, IonTitle, IonContent, IonList, IonItem, IonLabel, IonInput, IonDatetime, IonSelect, IonSelectOption, IonAccordionGroup, IonAccordion, IonSearchbar, IonSpinner, IonNote, ReactiveFormsModule, CommonModule, IonRange,
    ReceiptEditModalComponent, IonButton, IonIcon
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
  dateFrom = new FormControl<string>('');
  dateTo = new FormControl<string>('');
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
    private toastController: ToastController
  ) {
    this.loadMarkets();
    this.loadReceipts();
    // Initialize date inputs with current date range
    this.dateFrom.setValue(new Date(this.dateRange()[0]).toISOString().split('T')[0]);
    this.dateTo.setValue(new Date(this.dateRange()[1]).toISOString().split('T')[0]);
    // Szűrők változására újratölt
    this.itemName.valueChanges.subscribe(() => this.onFilterChange());
    this.marketId.valueChanges.subscribe(() => this.onFilterChange());
    this.orderBy.valueChanges.subscribe(() => this.onFilterChange());
    this.orderDir.valueChanges.subscribe(() => this.onFilterChange());
    // Dátum inputok figyelése
    this.dateFrom.valueChanges.subscribe(val => {
      if (val) {
        const dateFrom = new Date(val).getTime();
        const [, dateTo] = this.dateRange();
        this.dateRange.set([dateFrom, dateTo]);
        this.onFilterChange();
      }
    });
    this.dateTo.valueChanges.subscribe(val => {
      if (val) {
        const [dateFrom] = this.dateRange();
        const dateTo = new Date(val).getTime();
        this.dateRange.set([dateFrom, dateTo]);
        this.onFilterChange();
      }
    });
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

  onDateFromInput(event: any) {
    if (event.target.value) {
      const dateFrom = new Date(event.target.value).getTime();
      const [, dateTo] = this.dateRange();
      this.dateRange.set([dateFrom, dateTo]);
      this.onFilterChange();
    }
  }

  onDateToInput(event: any) {
    if (event.target.value) {
      const [dateFrom] = this.dateRange();
      const dateTo = new Date(event.target.value).getTime();
      this.dateRange.set([dateFrom, dateTo]);
      this.onFilterChange();
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
    this.dateFrom.setValue(new Date(MIN_DATE).toISOString().split('T')[0]);
    this.dateTo.setValue(new Date(MAX_DATE).toISOString().split('T')[0]);
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
    
    // Token hozzáadása a kéréshez
    const token = localStorage.getItem('access_token');
    if (!token) {
      this.toastController.create({
        message: 'Nincs érvényes bejelentkezés!',
        duration: 2000,
        color: 'danger'
      }).then(toast => toast.present());
      return;
    }

    // Fájl letöltése
    const link = document.createElement('a');
    link.href = downloadUrl;
    
    // Fájl kiterjesztés meghatározása
    let defaultFilename = `receipt_${receipt.id}`;
    if (receipt.original_filename) {
      // Ha van eredeti fájlnév, használjuk azt
      defaultFilename = receipt.original_filename;
    } else {
      // Ha nincs eredeti fájlnév, próbáljuk meg kitalálni a kiterjesztést az image_path-ből
      if (receipt.image_path) {
        const pathParts = receipt.image_path.split('.');
        if (pathParts.length > 1) {
          const extension = pathParts[pathParts.length - 1].toLowerCase();
          // Csak biztonságos képformátumokat engedélyezünk
          if (['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp'].includes(extension)) {
            defaultFilename += `.${extension}`;
          } else {
            defaultFilename += '.jpg'; // fallback
          }
        } else {
          defaultFilename += '.jpg'; // fallback
        }
      } else {
        defaultFilename += '.jpg'; // fallback
      }
    }
    
    link.download = defaultFilename;
    
    // Authorization header hozzáadása
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
