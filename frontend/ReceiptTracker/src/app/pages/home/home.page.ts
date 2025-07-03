import { Component } from '@angular/core';
import { IonHeader, IonToolbar, IonTitle, IonContent, IonButton, IonCard, IonCardHeader, IonCardTitle, IonCardContent, IonToast } from '@ionic/angular/standalone';
import { Store } from '@ngrx/store';
import { logout } from '../../store/auth/auth.actions';
import { Router } from '@angular/router';
import { selectUserProfile } from '../../store/auth/auth.selectors';
import { Observable } from 'rxjs';
import { CommonModule } from '@angular/common';
import { ReceiptService } from '../../api/api/receipt.service';
import { Camera, CameraResultType, CameraSource } from '@capacitor/camera';

@Component({
  selector: 'app-home',
  standalone: true,
  templateUrl: './home.page.html',
  styleUrls: ['home.page.scss'],
  imports: [CommonModule, IonHeader, IonToolbar, IonTitle, IonContent, IonButton, IonCard, IonCardHeader, IonCardTitle, IonCardContent, IonToast],
})
export class HomePage {
  userProfile$: Observable<any>;
  loading = false;
  toastMessage = '';
  showToast = false;

  constructor(
    private store: Store,
    private router: Router,
    private receiptService: ReceiptService
  ) {
    this.userProfile$ = this.store.select(selectUserProfile);
  }

  logout() {
    this.store.dispatch(logout());
    this.router.navigate(['login']);
  }

  goTo(path: string) {
    this.router.navigate([path]);
  }

  async quickPhotoUpload() {
    try {
      this.loading = true;
      const image = await Camera.getPhoto({
        quality: 80,
        allowEditing: false,
        resultType: CameraResultType.Base64,
        source: CameraSource.Camera
      });
      if (image && image.base64String) {
        const byteString = atob(image.base64String);
        const arrayBuffer = new ArrayBuffer(byteString.length);
        const intArray = new Uint8Array(arrayBuffer);
        for (let i = 0; i < byteString.length; i++) {
          intArray[i] = byteString.charCodeAt(i);
        }
        const blob = new Blob([intArray], { type: 'image/jpeg' });
        this.uploadReceiptImage(blob);
      } else {
        this.showFeedback('Nem sikerült képet készíteni.');
        this.loading = false;
      }
    } catch (err) {
      this.showFeedback('A kamera használata megszakadt vagy nem engedélyezett.');
      this.loading = false;
    }
  }

  onFileSelected(event: any) {
    const file: File = event.target.files[0];
    if (file) {
      this.loading = true;
      this.uploadReceiptImage(file);
    }
  }

  uploadReceiptImage(file: Blob) {
    this.receiptService.createReceiptReceiptRecognizePost(file).subscribe({
      next: (result) => {
        this.showFeedback('Blokk sikeresen feldolgozva!');
        this.loading = false;
        this.router.navigate(['receipts']);
      },
      error: (err) => {
        this.showFeedback('Hiba a blokk feldolgozásakor!');
        this.loading = false;
      }
    });
  }

  showFeedback(message: string) {
    this.toastMessage = message;
    this.showToast = true;
    setTimeout(() => (this.showToast = false), 3000);
  }
} 