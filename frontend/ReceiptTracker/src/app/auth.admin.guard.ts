import {Injectable} from '@angular/core';
import {CanActivate, Router} from '@angular/router';
import {Store} from '@ngrx/store';
import {selectUserProfile, selectAuthComplete, selectIsAuthenticated} from './store/auth/auth.selectors';
import {Observable} from 'rxjs';
import {map, take, filter, switchMap} from 'rxjs/operators';

@Injectable({ providedIn: 'root' })
export class AdminGuard implements CanActivate {
  constructor(private store: Store, private router: Router) {}

  canActivate(): Observable<boolean> {
    return this.store.select(selectAuthComplete).pipe(
      filter(complete => complete), // Wait until auth process is completely finished
      switchMap(() => this.store.select(selectIsAuthenticated)),
      take(1),
      switchMap(isAuth => {
        if (!isAuth) {
          this.router.navigate(['login']);
          return [false];
        }
        // If authenticated, check admin role
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
      })
    );
  }
}
