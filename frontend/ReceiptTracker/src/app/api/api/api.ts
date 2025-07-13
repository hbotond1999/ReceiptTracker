export * from './auth.service';
import { AuthService } from './auth.service';
export * from './receipt.service';
import { ReceiptService } from './receipt.service';
export * from './statistic.service';
import { StatisticService } from './statistic.service';
export const APIS = [AuthService, ReceiptService, StatisticService];
