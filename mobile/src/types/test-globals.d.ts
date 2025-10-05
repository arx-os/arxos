declare global {
  var mockAsyncStorage: {
    getItem: jest.MockedFunction<(key: string) => Promise<string | null>>;
    setItem: jest.MockedFunction<(key: string, value: string) => Promise<void>>;
    removeItem: jest.MockedFunction<(key: string) => Promise<void>>;
    clear: jest.MockedFunction<() => Promise<void>>;
  };

  var mockKeychain: {
    setInternetCredentials: jest.MockedFunction<(server: string, username: string, password: string) => Promise<void>>;
    getInternetCredentials: jest.MockedFunction<(server: string) => Promise<{ username: string; password: string } | false>>;
    resetInternetCredentials: jest.MockedFunction<(server: string) => Promise<void>>;
  };

  var mockNetInfo: {
    fetch: jest.MockedFunction<() => Promise<any>>;
    addEventListener: jest.MockedFunction<(listener: (state: any) => void) => () => void>;
  };

  var mockDeviceInfo: {
    getModel: jest.MockedFunction<() => Promise<string>>;
    getSystemVersion: jest.MockedFunction<() => Promise<string>>;
    getApplicationName: jest.MockedFunction<() => Promise<string>>;
    getVersion: jest.MockedFunction<() => Promise<string>>;
    getBuildNumber: jest.MockedFunction<() => Promise<string>>;
  };

  var mockApiService: {
    get: jest.MockedFunction<(url: string) => Promise<any>>;
    post: jest.MockedFunction<(url: string, data?: any) => Promise<any>>;
    put: jest.MockedFunction<(url: string, data?: any) => Promise<any>>;
    delete: jest.MockedFunction<(url: string) => Promise<any>>;
    uploadFile: jest.MockedFunction<(url: string, file: any) => Promise<any>>;
  };
}

export {};
