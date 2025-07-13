import {Injectable} from '@angular/core';
import {CanActivate, Router} from '@angular/router';
import {Store} from '@ngrx/store';
import {selectAuthComplete, selectIsAuthenticated} from './store/auth/auth.selectors';
import {Observable} from 'rxjs';
import {filter, map, switchMap, take} from 'rxjs/operators';

@Injectable({ providedIn: 'root' })
export class AuthGuard implements CanActivate {
  constructor(private store: Store, private router: Router) {}

  canActivate(): Observable<boolean> {
    return this.store.select(selectAuthComplete).pipe(
      filter(complete => complete), // Wait until auth process is completely finished
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
