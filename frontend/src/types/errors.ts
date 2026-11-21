export interface ApiErrorDetail {
  loc: (string | number)[]
  msg: string
  type: string
}

export interface ApiErrorBody {
  error: {
    code: string
    message: string
    details?: ApiErrorDetail[]
  }
}
