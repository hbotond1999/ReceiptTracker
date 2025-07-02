export * from './auth.service';
import { AuthService } from './auth.service';
export * from './receipt.service';
import { ReceiptService } from './receipt.service';
export const APIS = [AuthService, ReceiptService];
