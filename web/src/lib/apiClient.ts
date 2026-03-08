/**
 * API クライアント。FastAPI バックエンドとの通信を担当する。
 */

const BASE_URL = '/api';

export class ApiError extends Error {
  constructor(
    public readonly status: number,
    message: string,
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

export async function parseTemplate(file: File) {
  const form = new FormData();
  form.append('file', file);
  const res = await fetch(`${BASE_URL}/templates/parse`, { method: 'POST', body: form });
  if (!res.ok) {
    const body = await res.json();
    throw new ApiError(res.status, body.error ?? 'パースに失敗しました');
  }
  return res.json();
}

export async function validateTemplate(file: File) {
  const form = new FormData();
  form.append('file', file);
  const res = await fetch(`${BASE_URL}/templates/validate`, { method: 'POST', body: form });
  if (!res.ok) {
    const body = await res.json();
    throw new ApiError(res.status, body.error ?? '検証に失敗しました');
  }
  return res.json();
}

export async function extendTemplate(file: File) {
  const form = new FormData();
  form.append('file', file);
  const res = await fetch(`${BASE_URL}/templates/extend`, { method: 'POST', body: form });
  if (!res.ok) {
    const body = await res.json();
    throw new ApiError(res.status, body.error ?? '拡張に失敗しました');
  }
  return res.json();
}
