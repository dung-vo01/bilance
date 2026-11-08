import { isAxiosError } from "axios";
import type { ApiError } from "@/types";

export const getErrorMessage = (err: unknown, fallback: string) =>
  (isAxiosError<ApiError>(err) && err.response?.data?.error) || fallback;
