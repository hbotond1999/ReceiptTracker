import {Component, Input, OnInit} from '@angular/core';
import {CommonModule} from '@angular/common';
import {FormArray, FormBuilder, FormGroup, ReactiveFormsModule, Validators} from '@angular/forms';
import {
  IonButton,
  IonButtons,
  IonContent,
  IonDatetime,
  IonFooter,
  IonHeader,
  IonIcon,
  IonInput,
  IonItem,
  IonLabel,
  IonList,
  IonSelect,
  IonSelectOption,
  IonText,
  IonTitle,
  IonToolbar
} from '@ionic/angular/standalone';
import {ReceiptOut} from '../../api/model/receiptOut';
import {MarketOut} from '../../api/model/marketOut';
import {ModalController} from '@ionic/angular';

@Component({
  selector: 'app-receipt-edit-modal',
  standalone: true,
  templateUrl: './receipt-edit.modal.html',
  styleUrls: ['./receipt-edit.modal.scss'],
  imports: [
    CommonModule, ReactiveFormsModule,
    IonInput, IonButton, IonList, IonItem, IonLabel, IonIcon, IonSelect, IonSelectOption, IonDatetime, IonHeader, IonToolbar, IonTitle, IonContent, IonButtons, IonText, IonFooter
  ]
})
export class ReceiptEditModalComponent implements OnInit {
  @Input() receipt!: ReceiptOut;
  @Input() markets: MarketOut[] = [];

  form: FormGroup;

  constructor(private fb: FormBuilder, private modalController: ModalController) {
    this.form = this.fb.group({
      date: ['', Validators.required],
      receipt_number: ['', Validators.required],
      market_id: [null, Validators.required],
      postal_code: ['', Validators.required],
      city: ['', Validators.required],
      street_name: ['', Validators.required],
      street_number: ['', Validators.required],
      items: this.fb.array([])
    });
  }

  ngOnInit() {
    if (this.receipt) {
      this.form.patchValue({
        date: this.receipt.date,
        receipt_number: this.receipt.receipt_number,
        market_id: this.receipt.market.id,
        postal_code: this.receipt.postal_code,
        city: this.receipt.city,
        street_name: this.receipt.street_name,
        street_number: this.receipt.street_number
      });
      this.receipt.items.forEach(item => {
        const itemGroup = this.fb.group({
          id: [item.id],
          name: [item.name, Validators.required],
          unit_price: [item.unit_price, [Validators.required, Validators.min(0.01)]],
          quantity: [item.quantity, [Validators.required, Validators.min(0.01)]],
          unit: [item.unit, Validators.required],
          price: [item.price, [Validators.required, Validators.min(0.01)]]
        });

        // Auto-calculate price when unit_price or quantity changes
        itemGroup.get('unit_price')?.valueChanges.subscribe(() => this.calculatePrice(itemGroup));
        itemGroup.get('quantity')?.valueChanges.subscribe(() => this.calculatePrice(itemGroup));

        this.items.push(itemGroup);
      });
    }
  }

  get items() {
    return this.form.get('items') as FormArray;
  }

  addItem() {
    const newItem = this.fb.group({
      id: [null],
      name: ['', Validators.required],
      unit_price: [0, [Validators.required, Validators.min(0.01)]],
      quantity: [1, [Validators.required, Validators.min(0.01)]],
      unit: ['db', Validators.required],
      price: [0, [Validators.required, Validators.min(0.01)]]
    });

    // Auto-calculate price when unit_price or quantity changes
    newItem.get('unit_price')?.valueChanges.subscribe(() => this.calculatePrice(newItem));
    newItem.get('quantity')?.valueChanges.subscribe(() => this.calculatePrice(newItem));

    this.items.push(newItem);
  }

  removeItem(i: number) {
    this.items.removeAt(i);
  }

  calculatePrice(itemGroup: FormGroup) {
    const unitPrice = itemGroup.get('unit_price')?.value || 0;
    const quantity = itemGroup.get('quantity')?.value || 0;
    const calculatedPrice = unitPrice * quantity;
    itemGroup.get('price')?.setValue(calculatedPrice, { emitEvent: false });
  }

  onSave() {
    if (this.form.valid) {
      this.modalController.dismiss({ save: this.form.value });
    } else {
      this.form.markAllAsTouched();
    }
  }

  onCancel() {
    this.modalController.dismiss();
  }
}
