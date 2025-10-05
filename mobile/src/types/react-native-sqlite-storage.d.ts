declare module 'react-native-sqlite-storage' {
  export interface SQLiteDatabase {
    executeSql: (
      sql: string,
      params?: any[],
      success?: (result: any) => void,
      error?: (error: any) => void
    ) => void;
    transaction: (fn: (tx: SQLiteTransaction) => void) => void;
    close: () => void;
  }

  export interface SQLiteTransaction {
    executeSql: (
      sql: string,
      params?: any[],
      success?: (result: any) => void,
      error?: (error: any) => void
    ) => void;
  }

  export interface SQLiteResultSet {
    insertId: number;
    rowsAffected: number;
    rows: {
      length: number;
      item: (index: number) => any;
      raw: () => any[];
    };
  }

  export interface SQLiteParams {
    [key: string]: any;
  }

  export function openDatabase(
    name: string,
    version: string,
    displayName: string,
    size: number,
    successCallback?: () => void,
    errorCallback?: (error: any) => void
  ): SQLiteDatabase;

  export const DEBUG: boolean;
  export const enablePromise: boolean;
}
