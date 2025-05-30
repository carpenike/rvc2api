// Mock configuration for testing
export const getApiBaseUrl = (): string => {
  return "http://localhost:8000";
};

export const getWebSocketUrl = (): string => {
  return "ws://localhost:8000";
};

export const isDevelopment = (): boolean => {
  return false;
};

export const isProduction = (): boolean => {
  return false;
};

export const getConfig = () => ({
  apiBaseUrl: getApiBaseUrl(),
  wsBaseUrl: getWebSocketUrl(),
  isDev: isDevelopment(),
  isProd: isProduction()
});
