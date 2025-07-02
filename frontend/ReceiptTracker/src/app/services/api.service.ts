import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { AuthService as GeneratedAuthService } from '../api/api/auth.service';
import { ReceiptService } from '../api/api/receipt.service';
import { UserOut, TokenOut, UserInDB, UserListOut } from '../api/model/models';
import { ReceiptCreateRequest, ReceiptOut, ReceiptListOut } from '../api/model/models';

@Injectable({
  providedIn: 'root'
})
export class ApiService {

  constructor(
    private authService: GeneratedAuthService,
    private receiptService: ReceiptService
  ) { }

  // Auth methods
  login(username: string, password: string): Observable<TokenOut> {
    return this.authService.loginAuthLoginPost(username, password);
  }

  register(username: string, email: string, password: string): Observable<UserOut> {
    return this.authService.registerUserAuthRegisterPost({
      username: username,
      email: email,
      hashed_password: password // Note: This should be hashed on the backend
    });
  }

  getCurrentUser(): Observable<UserListOut> {
    return this.authService.listUsersAuthUsersGet();
  }

  getCurrentUserProfile(): Observable<UserOut> {
    return this.authService.getMeAuthMeGet();
  }

  // Receipt methods
  getReceipts(): Observable<ReceiptListOut> {
    return this.receiptService.getReceiptsReceiptGet();
  }

  // Note: There doesn't seem to be a specific getReceipt by ID method in the generated API
  // You might need to filter the receipts list or add this endpoint to your backend
  getReceipt(receiptId: number): Observable<ReceiptListOut> {
    return this.receiptService.getReceiptsReceiptGet();
  }

  createReceipt(receiptData: ReceiptCreateRequest): Observable<ReceiptOut> {
    return this.receiptService.createReceiptManualReceiptReceiptPost(receiptData);
  }

  updateReceipt(receiptId: number, receiptData: any): Observable<ReceiptOut> {
    return this.receiptService.updateReceiptReceiptReceiptIdPut(receiptId, receiptData);
  }

  deleteReceipt(receiptId: number): Observable<any> {
    return this.receiptService.deleteReceiptReceiptReceiptReceiptIdDelete(receiptId);
  }

  // Token refresh method
  refreshToken(refreshToken: string): Observable<TokenOut> {
    return this.authService.refreshTokenAuthRefreshPost(refreshToken);
  }
}
