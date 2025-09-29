/**
 * Equipment Redux Slice
 * Manages equipment data and operations
 */

import {createSlice, createAsyncThunk, PayloadAction} from '@reduxjs/toolkit';
import {Equipment, EquipmentSearchRequest, EquipmentSearchResponse, EquipmentStatusUpdate} from '@/types/equipment';
import {equipmentService} from '@/services/equipmentService';

// Initial state
interface EquipmentState {
  equipment: Equipment[];
  selectedEquipment: Equipment | null;
  searchResults: Equipment[];
  searchQuery: string;
  isLoading: boolean;
  isSearching: boolean;
  error: string | null;
  lastSync: string | null;
  pendingUpdates: EquipmentStatusUpdate[];
}

const initialState: EquipmentState = {
  equipment: [],
  selectedEquipment: null,
  searchResults: [],
  searchQuery: '',
  isLoading: false,
  isSearching: false,
  error: null,
  lastSync: null,
  pendingUpdates: [],
};

// Async thunks
export const fetchEquipment = createAsyncThunk(
  'equipment/fetchEquipment',
  async (buildingId: string, {rejectWithValue}) => {
    try {
      const response = await equipmentService.getEquipmentByBuilding(buildingId);
      return response;
    } catch (error: any) {
      return rejectWithValue(error.message);
    }
  }
);

export const searchEquipment = createAsyncThunk(
  'equipment/searchEquipment',
  async (request: EquipmentSearchRequest, {rejectWithValue}) => {
    try {
      const response = await equipmentService.searchEquipment(request);
      return response;
    } catch (error: any) {
      return rejectWithValue(error.message);
    }
  }
);

export const updateEquipmentStatus = createAsyncThunk(
  'equipment/updateStatus',
  async (update: EquipmentStatusUpdate, {rejectWithValue}) => {
    try {
      const response = await equipmentService.updateEquipmentStatus(update);
      return response;
    } catch (error: any) {
      return rejectWithValue(error.message);
    }
  }
);

export const syncEquipmentData = createAsyncThunk(
  'equipment/syncData',
  async (_, {rejectWithValue}) => {
    try {
      const response = await equipmentService.syncEquipmentData();
      return response;
    } catch (error: any) {
      return rejectWithValue(error.message);
    }
  }
);

// Equipment slice
const equipmentSlice = createSlice({
  name: 'equipment',
  initialState,
  reducers: {
    setSelectedEquipment: (state, action: PayloadAction<Equipment | null>) => {
      state.selectedEquipment = action.payload;
    },
    setSearchQuery: (state, action: PayloadAction<string>) => {
      state.searchQuery = action.payload;
    },
    clearSearchResults: (state) => {
      state.searchResults = [];
      state.searchQuery = '';
    },
    addPendingUpdate: (state, action: PayloadAction<EquipmentStatusUpdate>) => {
      state.pendingUpdates.push(action.payload);
    },
    removePendingUpdate: (state, action: PayloadAction<string>) => {
      state.pendingUpdates = state.pendingUpdates.filter(
        update => update.id !== action.payload
      );
    },
    clearError: (state) => {
      state.error = null;
    },
    updateEquipmentInList: (state, action: PayloadAction<Equipment>) => {
      const index = state.equipment.findIndex(eq => eq.id === action.payload.id);
      if (index !== -1) {
        state.equipment[index] = action.payload;
      }
    },
  },
  extraReducers: (builder) => {
    // Fetch equipment
    builder
      .addCase(fetchEquipment.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(fetchEquipment.fulfilled, (state, action) => {
        state.isLoading = false;
        state.equipment = action.payload;
        state.lastSync = new Date().toISOString();
        state.error = null;
      })
      .addCase(fetchEquipment.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.payload as string;
      });

    // Search equipment
    builder
      .addCase(searchEquipment.pending, (state) => {
        state.isSearching = true;
        state.error = null;
      })
      .addCase(searchEquipment.fulfilled, (state, action) => {
        state.isSearching = false;
        state.searchResults = action.payload.equipment;
        state.error = null;
      })
      .addCase(searchEquipment.rejected, (state, action) => {
        state.isSearching = false;
        state.error = action.payload as string;
      });

    // Update equipment status
    builder
      .addCase(updateEquipmentStatus.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(updateEquipmentStatus.fulfilled, (state, action) => {
        state.isLoading = false;
        // Update equipment in list
        const index = state.equipment.findIndex(eq => eq.id === action.payload.equipmentId);
        if (index !== -1) {
          state.equipment[index].status = action.payload.status;
          state.equipment[index].lastUpdated = action.payload.timestamp;
        }
        // Remove from pending updates
        state.pendingUpdates = state.pendingUpdates.filter(
          update => update.id !== action.payload.id
        );
        state.error = null;
      })
      .addCase(updateEquipmentStatus.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.payload as string;
      });

    // Sync equipment data
    builder
      .addCase(syncEquipmentData.fulfilled, (state, action) => {
        state.lastSync = new Date().toISOString();
        state.pendingUpdates = [];
      });
  },
});

export const {
  setSelectedEquipment,
  setSearchQuery,
  clearSearchResults,
  addPendingUpdate,
  removePendingUpdate,
  clearError,
  updateEquipmentInList,
} = equipmentSlice.actions;

export default equipmentSlice.reducer;
