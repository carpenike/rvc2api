// Jest setup file
import "@testing-library/jest-dom";
import type { SetupServerApi } from "msw/node";

// Mock react-hot-toast globally
const mockToast = {
  success: jest.fn(),
  error: jest.fn(),
  loading: jest.fn(),
  dismiss: jest.fn()
};

jest.mock("react-hot-toast", () => ({
  __esModule: true,
  default: mockToast,
  toast: mockToast,
  Toaster: () => null
}));

// Setup MSW server for API mocking
let server: SetupServerApi | undefined;

// Temporarily disable MSW to focus on getting basic tests working
// TODO: Re-enable MSW once Jest ESM configuration is fully stable
beforeAll(async () => {
  // MSW setup temporarily disabled
  console.log("MSW setup skipped for now - focusing on basic test functionality");
});

// Reset any request handlers that we may add during the tests,
// so they don't affect other tests
afterEach(() => {
  if (server) {
    server.resetHandlers();
  }
});

// Clean up after the tests are finished
afterAll(() => {
  if (server) {
    server.close();
  }
});

// Mock WebSocket for testing
class MockWebSocket {
  static readonly CONNECTING = 0;
  static readonly OPEN = 1;
  static readonly CLOSING = 2;
  static readonly CLOSED = 3;

  url: string;
  readyState: number;
  onopen: ((event: Event) => void) | null = null;
  onclose: ((event: CloseEvent) => void) | null = null;
  onmessage: ((event: MessageEvent) => void) | null = null;
  onerror: ((event: Event) => void) | null = null;

  constructor(url: string) {
    this.url = url;
    this.readyState = MockWebSocket.CONNECTING;

    // Simulate connection opening
    setTimeout(() => {
      this.readyState = MockWebSocket.OPEN;
      if (this.onopen) {
        this.onopen(new Event("open"));
      }
    }, 0);
  }

  send(data: string) {
    // Echo the data back for testing
    if (this.onmessage && this.readyState === MockWebSocket.OPEN) {
      this.onmessage(new MessageEvent("message", { data }));
    }
  }

  close() {
    this.readyState = MockWebSocket.CLOSED;
    if (this.onclose) {
      this.onclose(new CloseEvent("close"));
    }
  }

  addEventListener(type: string, listener: EventListener) {
    if (type === "open" && this.onopen === null) {
      this.onopen = listener as (event: Event) => void;
    } else if (type === "close" && this.onclose === null) {
      this.onclose = listener as (event: CloseEvent) => void;
    } else if (type === "message" && this.onmessage === null) {
      this.onmessage = listener as (event: MessageEvent) => void;
    } else if (type === "error" && this.onerror === null) {
      this.onerror = listener as (event: Event) => void;
    }
  }

  removeEventListener() {
    // Mock implementation
  }
}

// Replace global WebSocket with mock
// eslint-disable-next-line @typescript-eslint/no-explicit-any
(global as any).WebSocket = MockWebSocket;

// Mock environment variables that might be used in tests
(process.env as Record<string, string>).VITE_API_BASE_URL = "http://localhost:8000";
(process.env as Record<string, string>).VITE_WS_URL = "ws://localhost:8000";
(process.env as Record<string, string>).VITE_APP_VERSION = "test";
(process.env as Record<string, string>).NODE_ENV = "test";

// Also set up global import meta env for fallback (recommended by perplexity)
// eslint-disable-next-line @typescript-eslint/no-explicit-any
(global as any).importMetaEnv = {
  VITE_API_BASE_URL: "http://localhost:8000",
  VITE_WS_URL: "ws://localhost:8000",
  VITE_APP_VERSION: "test",
  MODE: "test",
  BASE_URL: "/",
  PROD: false,
  DEV: false,
  SSR: false,
  NODE_ENV: "test"
};

// Additional global mocks
Object.defineProperty(window, "matchMedia", {
  writable: true,
  value: jest.fn().mockImplementation((query: string) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: jest.fn(), // deprecated
    removeListener: jest.fn(), // deprecated
    addEventListener: jest.fn(),
    removeEventListener: jest.fn(),
    dispatchEvent: jest.fn()
  }))
} as PropertyDescriptor);
