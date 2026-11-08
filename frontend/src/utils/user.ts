export const displayName = (u?: {
  firstname: string | null;
  username: string;
}) => u?.firstname || u?.username || "Unknown";
