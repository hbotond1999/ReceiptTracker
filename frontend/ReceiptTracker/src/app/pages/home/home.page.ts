import { Component } from '@angular/core';
import { IonHeader, IonToolbar, IonTitle, IonContent, IonButton, IonCard, IonCardHeader, IonCardTitle, IonCardContent, IonToast, IonFab, IonFabButton, IonIcon, IonSpinner, IonLabel, IonItem, IonInput } from '@ionic/angular/standalone';
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
  imports: [CommonModule, IonHeader, IonToolbar, IonTitle, IonContent, IonButton, IonCard, IonCardHeader, IonCardTitle, IonCardContent, IonToast, IonFab, IonFabButton, IonIcon, IonSpinner, IonLabel, IonItem, IonInput],
})
export class HomePage {
  userProfile$: Observable<any>;
  loading = false;
  uploadProgress = 0;
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
      const image = await Camera.getPhoto({
        quality: 80,
        allowEditing: false,
        resultType: CameraResultType.Base64,
        source: CameraSource.Camera
      });

      if (image && image.base64String) {
        this.startUploadProcess(image.base64String);
      } else {
        this.showFeedback('Nem sikerült képet készíteni.');
      }
    } catch (err) {
      if (err && typeof err === 'object' && 'message' in err) {
        console.log('Kamera megszakítva:', err);
      }
    }
  }

  onFileSelected(event: any) {
    const file: File = event.target.files[0];
    if (file) {
      this.startFileUploadProcess(file);
    }
  }

  private startUploadProcess(base64String: string) {
    this.loading = true;
    this.uploadProgress = 0;

    const byteString = atob(base64String);
    const arrayBuffer = new ArrayBuffer(byteString.length);
    const intArray = new Uint8Array(arrayBuffer);
    for (let i = 0; i < byteString.length; i++) {
      intArray[i] = byteString.charCodeAt(i);
    }
    const blob = new Blob([intArray], { type: 'image/jpeg' });
    this.uploadReceiptImage(blob);
  }

  private startFileUploadProcess(file: File) {
    this.loading = true;
    this.uploadProgress = 0;
    this.uploadReceiptImage(file);
  }

  uploadReceiptImage(file: Blob) {
    const progressInterval = setInterval(() => {
      if (this.uploadProgress < 90) {
        this.uploadProgress += Math.random() * 10;
      }
    }, 200);

    this.receiptService.createReceiptReceiptRecognizePost(file).subscribe({
      next: (result) => {
        clearInterval(progressInterval);
        this.uploadProgress = 100;

        setTimeout(() => {
          this.showFeedback('Blokk sikeresen feldolgozva!');
          this.loading = false;
          this.uploadProgress = 0;
          this.router.navigate(['receipts']);
        }, 500);
      },
      error: (err) => {
        clearInterval(progressInterval);
        this.showFeedback('Hiba a blokk feldolgozásakor!');
        this.loading = false;
        this.uploadProgress = 0;
      }
    });
  }

  showFeedback(message: string) {
    this.toastMessage = message;
    this.showToast = true;
    setTimeout(() => (this.showToast = false), 3000);
  }
}
