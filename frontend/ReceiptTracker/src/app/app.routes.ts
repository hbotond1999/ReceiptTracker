import { Routes } from '@angular/router';
import { AuthGuard } from './auth.guard';
import { AdminGuard } from './auth.admin.guard';

export const routes: Routes = [
  {
    path: 'login',
    loadComponent: () => import('./pages/login/login.page').then((m) => m.LoginPage),
  },
  {
    path: 'home',
    loadComponent: () => import('./pages/home/home.page').then((m) => m.HomePage),
    canActivate: [AuthGuard],
  },
  {
    path: 'receipts',
    loadComponent: () => import('./pages/receipts/receipts.page').then((m) => m.ReceiptsPage),
    canActivate: [AuthGuard],
  },
  {
    path: 'stats',
    loadComponent: () => import('./pages/stats/stats.page').then((m) => m.StatsPage),
    canActivate: [AuthGuard],
  },
  {
    path: 'admin',
    loadComponent: () => import('./pages/admin/admin.page').then((m) => m.AdminPage),
    canActivate: [AdminGuard],
  },
  {
    path: '',
    redirectTo: 'login',
    pathMatch: 'full',
  },
];
