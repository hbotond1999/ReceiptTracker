import {Component, Input, OnInit} from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormArray, FormBuilder, FormControl, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';
import {
  IonModal,
  IonInput,
  IonButton,
  IonList,
  IonItem,
  IonLabel,
  IonIcon,
  IonSelect,
  IonSelectOption,
  IonDatetime,
  IonTextarea,
  IonHeader,
  IonToolbar,
  IonTitle,
  IonContent,
  IonButtons, IonText, IonFooter
} from '@ionic/angular/standalone';
import { ReceiptOut } from '../../api/model/receiptOut';
import { MarketOut } from '../../api/model/marketOut';
import { ModalController } from '@ionic/angular';

@Component({
  selector: 'app-receipt-edit-modal',
  standalone: true,
  templateUrl: './receipt-edit.modal.html',
  styleUrls: ['./receipt-edit.modal.scss'],
  imports: [
    CommonModule, ReactiveFormsModule,
    IonModal, IonInput, IonButton, IonList, IonItem, IonLabel, IonIcon, IonSelect, IonSelectOption, IonDatetime, IonTextarea, IonHeader, IonToolbar, IonTitle, IonContent, IonButtons, IonText, IonFooter
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
        this.items.push(this.fb.group({
          id: [item.id],
          name: [item.name, Validators.required],
          price: [item.price, [Validators.required, Validators.min(0.01)]]
        }));
      });
    }
  }

  get items() {
    return this.form.get('items') as FormArray;
  }

  addItem() {
    this.items.push(this.fb.group({
      id: [null],
      name: ['', Validators.required],
      price: [0, [Validators.required, Validators.min(0.01)]]
    }));
  }

  removeItem(i: number) {
    this.items.removeAt(i);
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
