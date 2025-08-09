// Global type declarations for ArxIDE
declare global {
  interface Window {
    CadEngine?: any;
    ConstraintSolver?: any;
    __TAURI__?: {
      invoke: (command: string, args?: any) => Promise<any>;
      event: {
        listen: (event: string, callback: (payload: any) => void) => Promise<void>;
        emit: (event: string, payload?: any) => Promise<void>;
      };
    };
  }

  // Three.js types
  namespace THREE {
    interface Object3D {
      geometry?: BufferGeometry;
      material?: Material | Material[];
    }
  }

  // Monaco Editor types
  namespace monaco {
    namespace editor {
      interface IStandaloneEditorConstructionOptions {
        cursorStyle?: 'line' | 'block' | 'underline' | 'line-thin' | 'block-outline' | 'underline-thin';
      }
    }
  }

  // Socket.io types
  interface Socket {
    connected: boolean;
    id: string;
    emit: (event: string, ...args: any[]) => void;
    on: (event: string, callback: (...args: any[]) => void) => void;
    off: (event: string, callback?: (...args: any[]) => void) => void;
    disconnect: () => void;
  }

  // Y.js types
  interface Y {
    getText: (name: string) => YText;
    getMap: (name: string) => YMap<any>;
    getArray: (name: string) => YArray<any>;
  }

  interface YText {
    insert: (index: number, text: string) => void;
    delete: (index: number, length: number) => void;
    toString: () => string;
  }

  interface YMap<T> {
    set: (key: string, value: T) => void;
    get: (key: string) => T;
    delete: (key: string) => void;
  }

  interface YArray<T> {
    insert: (index: number, content: T[]) => void;
    delete: (index: number, length: number) => void;
    get: (index: number) => T;
    length: number;
  }
}

export {};
