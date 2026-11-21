export type Role = 'user' | 'admin'

export interface Profile {
  display_name: string
  avatar_url: string | null
  country: string | null
}

export interface User {
  id: number
  email: string
  role: Role
  created_at: string
  profile: Profile
}

export interface ProfileUpdate {
  display_name?: string
  avatar_url?: string | null
  country?: string | null
}
