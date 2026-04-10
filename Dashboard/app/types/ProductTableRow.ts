export interface ProductTableRow {
  id: number;
  name: string;
  sku: string;
  price: number;
  status: string;
  category: string;
  stock: number;
  imageUrl?: string;
  updatedAt?: string;
}

export interface ProductStockData {
  date: string
  stock: number
}
