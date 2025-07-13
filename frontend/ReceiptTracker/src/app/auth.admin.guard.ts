import {Injectable} from '@angular/core';
import {CanActivate, Router} from '@angular/router';
import {Store} from '@ngrx/store';
import {selectUserProfile} from './store/auth/auth.selectors';
import {Observable} from 'rxjs';
import {map, take} from 'rxjs/operators';

@Injectable({ providedIn: 'root' })
export class AdminGuard implements CanActivate {
  constructor(private store: Store, private router: Router) {}

  canActivate(): Observable<boolean> {
    return this.store.select(selectUserProfile).pipe(
      take(1),
      map(profile => {
        if (!profile || !profile.roles || !profile.roles.includes('admin')) {
          this.router.navigate(['home']);
          return false;
        }
        return true;
      })
    );
  }
}
