import { isAxiosError } from "axios";
import type { ApiError } from "@/types";

export const getErrorMessage = (err: unknown, fallback: string) =>
  (isAxiosError<ApiError>(err) && err.response?.data?.error) || fallback;

// For routes that look a user up by name: a 404 means "no such user", which
// we don't confirm to the caller. Everything else keeps the server message.
export const getUserLookupErrorMessage = (err: unknown, fallback: string) =>
  isAxiosError<ApiError>(err) && err.response?.status === 404
    ? fallback
    : getErrorMessage(err, fallback);
