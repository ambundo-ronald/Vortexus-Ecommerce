export interface OrderTableRow {
  id: number;
  orderNo: string;
  customerName?: string;
  companyName: string;
  status: string;
  packaged: boolean;
  fulfilled: boolean;
  invoiced: boolean;
  paid: boolean;
  orderTotal: number;
  createdDate: string;
  lastUpdated?: string;
}
