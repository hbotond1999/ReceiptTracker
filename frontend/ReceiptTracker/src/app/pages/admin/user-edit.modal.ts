import { Component, Input, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';
import { IonicModule, ModalController } from '@ionic/angular';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';
import { UserOut, UserUpdateRequest, UserInDB, Role } from '../../api/model/models';

@Component({
  selector: 'app-user-edit-modal',
  standalone: true,
  imports: [CommonModule, IonicModule, FormsModule, ReactiveFormsModule],
  templateUrl: './user-edit.modal.html',
  styleUrls: ['./user-edit.modal.scss']
})
export class UserEditModalComponent implements OnInit {
  @Input() user?: UserOut;
  userForm: FormGroup;
  isCreate: boolean = false;
  roles = Object.values(Role); // Assuming Role is an enum with 'admin' and 'user'

  constructor(private fb: FormBuilder, private modalCtrl: ModalController) {
    this.userForm = this.fb.group({
      username: ['', Validators.required],
      email: ['', [Validators.email]],
      fullname: [''],
      password: ['', [Validators.required]],
      disabled: [false],
      roles: [[], Validators.required]
    });
  }

  ngOnInit() {
    this.isCreate = !this.user;
    if (this.user) {
      this.userForm.patchValue({
        username: this.user.username,
        email: this.user.email,
        fullname: this.user.fullname,
        disabled: this.user.disabled,
        roles: this.user.roles
      });
      this.userForm.get('username')?.disable(); // Username not editable
      this.userForm.get('password')?.disable(); // Password not editable here
    } else {
      this.userForm.get('password')?.setValidators(Validators.required);
    }
  }

  save() {
    if (this.userForm.valid) {
      const formValue = this.userForm.value;
      if (this.isCreate) {
        const newUser: UserInDB = {
          username: formValue.username,
          email: formValue.email,
          fullname: formValue.fullname,
          hashed_password: formValue.password, // Note: Backend will hash it
          disabled: formValue.disabled,
          roles: formValue.roles,
          profile_picture: null // Default
        };
        this.modalCtrl.dismiss(newUser, 'create');
      } else {
        const update: UserUpdateRequest = {
          email: formValue.email,
          fullname: formValue.fullname,
          disabled: formValue.disabled,
          roles: formValue.roles,
          profile_picture: this.user?.profile_picture // Keep existing
        };
        this.modalCtrl.dismiss({ id: this.user?.id, update }, 'update');
      }
    } else {
      // Mark all fields as touched to show validation errors
      this.userForm.markAllAsTouched();
    }
  }

  cancel() {
    this.modalCtrl.dismiss(null, 'cancel');
  }
}
