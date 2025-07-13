export * from './auth.service';
import {AuthService} from './auth.service';
import {ReceiptService} from './receipt.service';
import {StatisticService} from './statistic.service';

export * from './receipt.service';
export * from './statistic.service';
export const APIS = [AuthService, ReceiptService, StatisticService];
