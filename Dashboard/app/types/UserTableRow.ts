export interface UserTableRow {
  id: string;
  name: string;
  email: string;
  imageUrl: string;
  status: 'Active' | 'Suspended';
  role: string;
  joined: string;
  company?: string;
  phone?: string;
}
