import { Injectable } from '@angular/core';
import { CanActivate, Router } from '@angular/router';
import { Store } from '@ngrx/store';
import { selectIsAuthenticated, selectAuthLoading } from './store/auth/auth.selectors';
import { Observable } from 'rxjs';
import { map, take, filter, switchMap } from 'rxjs/operators';

@Injectable({ providedIn: 'root' })
export class AuthGuard implements CanActivate {
  constructor(private store: Store, private router: Router) {}

  canActivate(): Observable<boolean> {
    return this.store.select(selectAuthLoading).pipe(
      filter(loading => !loading), // Várjuk meg, amíg az auto-login befejeződik
      switchMap(() => this.store.select(selectIsAuthenticated)),
      take(1),
      map(isAuth => {
        if (!isAuth) {
          this.router.navigate(['login']);
          return false;
        }
        return true;
      })
    );
  }
} 