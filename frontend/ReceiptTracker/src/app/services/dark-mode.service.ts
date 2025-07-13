import {Injectable, signal} from '@angular/core';
import {BehaviorSubject, fromEvent} from 'rxjs';
import {map, tap} from "rxjs/operators";

@Injectable({
  providedIn: 'root'
})
export class DarkModeService {
  private darkModeQuery = window.matchMedia('(prefers-color-scheme: dark)');
  private darkModeSubject = new BehaviorSubject<boolean>(this.getDarkModeState());

  // Observable for components to subscribe to
  public isDarkMode$ = this.darkModeSubject.asObservable().pipe(
    tap((isDark) => console.log("Dark mode changed:", isDark))
  );

  // Signal for template usage
  public isDarkMode = signal(this.getDarkModeState());

  constructor() {
    console.log("DarkModeService initialized, current dark mode:", this.getDarkModeState());

    // Listen for dark mode changes using fromEvent for better RxJS integration
    fromEvent(this.darkModeQuery, 'change').pipe(
      map((event: any) => event.matches),
      tap((isDark) => console.log("System dark mode preference changed:", isDark))
    ).subscribe((isDark) => {
      this.darkModeSubject.next(isDark);
      this.isDarkMode.set(isDark);
    });

    // Also set up the traditional event listener as fallback
    this.darkModeQuery.addEventListener('change', (e) => {
      console.log("Traditional listener - dark mode changed:", e.matches);
      this.darkModeSubject.next(e.matches);
      this.isDarkMode.set(e.matches);
    });
  }

  /**
   * Get current dark mode state
   */
  getCurrentDarkMode(): boolean {
    return this.getDarkModeState();
  }

  /**
   * Get the current system dark mode preference
   */
  private getDarkModeState(): boolean {
    return this.darkModeQuery.matches;
  }

  /**
   * Manually trigger a dark mode check (useful for testing)
   */
  checkDarkMode(): void {
    const currentState = this.getDarkModeState();
    console.log("Manual dark mode check:", currentState);
    this.darkModeSubject.next(currentState);
    this.isDarkMode.set(currentState);
  }
}
