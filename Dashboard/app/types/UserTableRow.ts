export interface UserTableRow {
  id: string;
  name: string;
  email: string;
  imageUrl: string;
  status: 'Active' | 'Invited' | 'Suspended';
  role: string;
  joined: string;
}
