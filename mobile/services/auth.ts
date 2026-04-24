/** Llamadas al API de autenticación. */

import api from "./api";
import type { AuthSession, User } from "../types";

export async function register(
  email: string,
  emailConfirm: string,
  password: string,
): Promise<void> {
  await api.post("/auth/register", {
    email,
    email_confirm: emailConfirm,
    password,
  });
}

export async function login(email: string, password: string): Promise<AuthSession> {
  const res = await api.post<{ access_token: string; token_type: string; user: User }>(
    "/auth/login",
    { email, password },
  );
  return { token: res.data.access_token, user: res.data.user };
}

export async function me(): Promise<User> {
  const res = await api.get<User>("/auth/me");
  return res.data;
}

export async function resendVerification(email: string): Promise<void> {
  await api.post("/auth/resend-verification", { email });
}

export async function forgotPassword(email: string): Promise<void> {
  await api.post("/auth/forgot-password", { email });
}

export async function resetPassword(
  token: string,
  newPassword: string,
  newPasswordConfirm: string,
): Promise<void> {
  await api.post("/auth/reset-password", {
    token,
    new_password: newPassword,
    new_password_confirm: newPasswordConfirm,
  });
}
