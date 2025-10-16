/**
 * Synchronization Redux Slice
 * Manages data synchronization between mobile app and server
 */

import {createSlice, createAsyncThunk, PayloadAction} from '@reduxjs/toolkit';
import {SyncState, SyncQueueItem, SyncResult, SyncSettings} from '@/types/sync';
import {syncService} from '@/services/syncService';
import {storageService} from '@/services/storageService';

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
      // Update last sync timestamp
      await storageService.setSetting('lastSync', new Date().toISOString());
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
      // Update last sync timestamp
      await storageService.setSetting('lastSync', new Date().toISOString());
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

export const loadSyncQueue = createAsyncThunk(
  'sync/loadQueue',
  async (_, {rejectWithValue}) => {
    try {
      const queue = await storageService.getSyncQueue();
      const lastSync = await storageService.getSetting('lastSync');
      
      // Convert SyncQueueRecord to SyncQueueItem
      const syncQueueItems: SyncQueueItem[] = queue.map(item => ({
        id: item.id,
        type: mapTableToSyncType(item.table),
        data: item.data,
        priority: 'medium',
        retryCount: item.retryCount,
        maxRetries: 3,
        createdAt: item.createdAt,
        lastAttempt: item.lastAttempt,
        status: item.retryCount >= 3 ? 'failed' : 'pending',
      }));

      return { queue: syncQueueItems, lastSync };
    } catch (error: any) {
      return rejectWithValue(error.message);
    }
  }
);

// Helper function to map table to sync type
function mapTableToSyncType(table: string): 'equipment_update' | 'spatial_update' | 'photo_upload' | 'status_update' | 'note_update' {
  switch (table) {
    case 'spatial_anchors':
    case 'spatial_data':
      return 'spatial_update';
    case 'equipment':
      return 'equipment_update';
    case 'photos':
      return 'photo_upload';
    case 'equipment_notes':
      return 'note_update';
    default:
      return 'status_update';
  }
}

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

    // Load sync queue
    builder
      .addCase(loadSyncQueue.fulfilled, (state, action) => {
        state.queue = action.payload.queue;
        state.lastSync = action.payload.lastSync;
        state.pendingUpdates = action.payload.queue.length;
      })
      .addCase(loadSyncQueue.rejected, (state, action) => {
        state.syncErrors.push(`Failed to load sync queue: ${action.payload}`);
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
