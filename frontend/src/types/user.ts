import type { PlanCode } from './playback'

export type Role = 'user' | 'admin'

export interface Profile {
  display_name: string
  avatar_url: string | null
  country: string | null
}

export interface Subscription {
  plan_code: PlanCode
  expires_at: string | null
  cancelled: boolean
}

export interface Account {
  id: number
  email: string
  role: Role
  created_at: string
  profile: Profile
}

export interface User extends Account {
  subscription: Subscription
}

export interface ProfileUpdate {
  display_name?: string
  avatar_url?: string | null
  country?: string | null
}
