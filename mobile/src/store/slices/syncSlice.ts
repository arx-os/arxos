/**
 * Synchronization Redux Slice
 * Manages data synchronization between mobile app and server
 */

import {createSlice, createAsyncThunk, PayloadAction} from '@reduxjs/toolkit';
import {SyncState, SyncQueueItem, SyncResult, SyncSettings} from '@/types/sync';
import {syncService} from '@/services/syncService';

// Initial state
const initialState: SyncState = {
  isOnline: true,
  lastSync: null,
  pendingUpdates: 0,
  syncInProgress: false,
  syncErrors: [],
  queue: [],
};

// Async thunks
export const syncData = createAsyncThunk(
  'sync/syncData',
  async (_, {rejectWithValue}) => {
    try {
      const result = await syncService.syncAllData();
      return result;
    } catch (error: any) {
      return rejectWithValue(error.message);
    }
  }
);

export const syncQueue = createAsyncThunk(
  'sync/syncQueue',
  async (_, {rejectWithValue}) => {
    try {
      const result = await syncService.syncQueue();
      return result;
    } catch (error: any) {
      return rejectWithValue(error.message);
    }
  }
);

export const retryFailedSync = createAsyncThunk(
  'sync/retryFailed',
  async (itemId: string, {rejectWithValue}) => {
    try {
      const result = await syncService.retrySyncItem(itemId);
      return result;
    } catch (error: any) {
      return rejectWithValue(error.message);
    }
  }
);

export const clearSyncErrors = createAsyncThunk(
  'sync/clearErrors',
  async (_, {rejectWithValue}) => {
    try {
      await syncService.clearSyncErrors();
      return null;
    } catch (error: any) {
      return rejectWithValue(error.message);
    }
  }
);

// Sync slice
const syncSlice = createSlice({
  name: 'sync',
  initialState,
  reducers: {
    setOnlineStatus: (state, action: PayloadAction<boolean>) => {
      state.isOnline = action.payload;
    },
    addToQueue: (state, action: PayloadAction<SyncQueueItem>) => {
      state.queue.push(action.payload);
      state.pendingUpdates = state.queue.length;
    },
    removeFromQueue: (state, action: PayloadAction<string>) => {
      state.queue = state.queue.filter(item => item.id !== action.payload);
      state.pendingUpdates = state.queue.length;
    },
    updateQueueItem: (state, action: PayloadAction<{id: string; updates: Partial<SyncQueueItem>}>) => {
      const index = state.queue.findIndex(item => item.id === action.payload.id);
      if (index !== -1) {
        state.queue[index] = {...state.queue[index], ...action.payload.updates};
      }
    },
    setSyncInProgress: (state, action: PayloadAction<boolean>) => {
      state.syncInProgress = action.payload;
    },
    addSyncError: (state, action: PayloadAction<string>) => {
      state.syncErrors.push(action.payload);
    },
    clearSyncErrors: (state) => {
      state.syncErrors = [];
    },
    updateLastSync: (state, action: PayloadAction<string>) => {
      state.lastSync = action.payload;
    },
  },
  extraReducers: (builder) => {
    // Sync data
    builder
      .addCase(syncData.pending, (state) => {
        state.syncInProgress = true;
        state.syncErrors = [];
      })
      .addCase(syncData.fulfilled, (state, action) => {
        state.syncInProgress = false;
        state.lastSync = new Date().toISOString();
        state.pendingUpdates = action.payload.failed;
        state.syncErrors = action.payload.errors;
      })
      .addCase(syncData.rejected, (state, action) => {
        state.syncInProgress = false;
        state.syncErrors.push(action.payload as string);
      });

    // Sync queue
    builder
      .addCase(syncQueue.pending, (state) => {
        state.syncInProgress = true;
      })
      .addCase(syncQueue.fulfilled, (state, action) => {
        state.syncInProgress = false;
        state.lastSync = new Date().toISOString();
        // Remove completed items from queue
        state.queue = state.queue.filter(item => 
          !action.payload.syncedItems.includes(item.id)
        );
        state.pendingUpdates = state.queue.length;
        state.syncErrors = action.payload.errors;
      })
      .addCase(syncQueue.rejected, (state, action) => {
        state.syncInProgress = false;
        state.syncErrors.push(action.payload as string);
      });

    // Retry failed sync
    builder
      .addCase(retryFailedSync.fulfilled, (state, action) => {
        const index = state.queue.findIndex(item => item.id === action.payload.id);
        if (index !== -1) {
          state.queue[index] = action.payload;
        }
      });

    // Clear sync errors
    builder
      .addCase(clearSyncErrors.fulfilled, (state) => {
        state.syncErrors = [];
      });
  },
});

export const {
  setOnlineStatus,
  addToQueue,
  removeFromQueue,
  updateQueueItem,
  setSyncInProgress,
  addSyncError,
  clearSyncErrors,
  updateLastSync,
} = syncSlice.actions;

export default syncSlice.reducer;
