export interface OrderTableRow {
  id: number;
  companyName: string;
  status: 'Paid' | 'Pending' | 'Failed';
  packaged: boolean;
  fulfilled: boolean;
  invoiced: boolean;
  paid: boolean;
  orderTotal: number;
  createdDate: string;
}
