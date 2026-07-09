import { useEffect, useState } from "react";

// Temporary use: the backend is hosted on Render - free tier
// so need to inform the user about the potential slow loading at first launch
export const useSlowLoading = (isLoading: boolean, delayMs = 4000): boolean => {
  const [slow, setSlow] = useState(false);

  useEffect(() => {
    if (!isLoading) {
      setSlow(false);
      return;
    }
    const timer = setTimeout(() => setSlow(true), delayMs);
    return () => clearTimeout(timer);
  }, [isLoading, delayMs]);

  return slow;
};
