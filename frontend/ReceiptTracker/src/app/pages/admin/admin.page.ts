import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { IonicModule, ModalController, AlertController } from '@ionic/angular';
import { AuthService } from '../../api/api/auth.service';
import { UserListOut, UserOut } from '../../api/model/models';
import { UserEditModalComponent } from './user-edit.modal';
import { Observable } from 'rxjs';
import { Subject, takeUntil } from 'rxjs';

@Component({
  selector: 'app-admin',
  standalone: true,
  imports: [CommonModule, FormsModule, IonicModule],
  templateUrl: './admin.page.html',
  styleUrls: ['./admin.page.scss']
})
export class AdminPage implements OnInit, OnDestroy {
  users: UserOut[] = [];
  total: number = 0;
  skip: number = 0;
  limit: number = 10;
  searchUsername: string = '';
  readonly unsub$ = new Subject<void>();

  constructor(
    private authService: AuthService,
    private modalCtrl: ModalController,
    private alertCtrl: AlertController
  ) {}

  ngOnInit() {
    this.loadUsers();
  }

  loadUsers() {
    this.authService.listUsersAuthUsersGet(this.searchUsername, this.skip, this.limit).pipe(
      takeUntil(this.unsub$)
    ).subscribe({
      next: (data: UserListOut) => {
        this.users = data.users;
        this.total = data.total;
      },
      error: (err) => console.error('Hiba a felhasználók betöltésekor', err)
    });
  }

  async openEditModal(user?: UserOut) {
    const modal = await this.modalCtrl.create({
      component: UserEditModalComponent,
      componentProps: { user }
    });
    await modal.present();

    const { data, role } = await modal.onWillDismiss();
    if (role === 'create' && data) {
      this.authService.registerUserAdminAuthRegisterPost(data).pipe(takeUntil(this.unsub$)).subscribe({
        next: () => this.loadUsers(),
        error: (err) => console.error('Hiba a felhasználó létrehozásakor', err)
      });
    } else if (role === 'update' && data) {
      this.authService.updateUserAuthUsersUserIdPut(data.id, data.update).pipe(takeUntil(this.unsub$)).subscribe({
        next: () => this.loadUsers(),
        error: (err) => console.error('Hiba a felhasználó frissítésekor', err)
      });
    }
  }

  async deleteUser(userId: number) {
    const alert = await this.alertCtrl.create({
      header: 'Törlés megerősítése',
      message: 'Biztosan törölni szeretnéd ezt a felhasználót?',
      buttons: [
        { text: 'Mégse', role: 'cancel' },
        { text: 'Törlés', handler: () => {
          this.authService.deleteUsersAuthUsersUserIdDelete(userId).pipe(takeUntil(this.unsub$)).subscribe({
            next: () => this.loadUsers(),
            error: (err) => console.error('Hiba a felhasználó törlésekor', err)
          });
        }}
      ]
    });
    await alert.present();
  }

  search() {
    this.skip = 0;
    this.loadUsers();
  }

  changePage(direction: 'next' | 'prev') {
    if (direction === 'next' && this.skip + this.limit < this.total) {
      this.skip += this.limit;
    } else if (direction === 'prev' && this.skip > 0) {
      this.skip -= this.limit;
    }
    this.loadUsers();
  }

  ngOnDestroy(): void {
    this.unsub$.next();
    this.unsub$.complete();
  }

  protected readonly Math = Math;
}
