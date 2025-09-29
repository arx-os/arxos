/**
 * Augmented Reality Redux Slice
 * Manages AR session state and spatial anchors
 */

import {createSlice, createAsyncThunk, PayloadAction} from '@reduxjs/toolkit';
import {ARState, SpatialAnchor, ARConfiguration, ARSessionConfig} from '@/types/ar';
import {arService} from '@/services/arService';

// Initial state
const initialState: ARState = {
  isSupported: false,
  permissionGranted: false,
  sessionActive: false,
  trackingState: 'notAvailable',
  detectedAnchors: [],
  selectedAnchor: null,
  cameraPosition: null,
  cameraRotation: null,
  lightingEstimate: null,
  detectedPlanes: [],
};

// Async thunks
export const initializeAR = createAsyncThunk(
  'ar/initialize',
  async (_, {rejectWithValue}) => {
    try {
      const result = await arService.initializeAR();
      return result;
    } catch (error: any) {
      return rejectWithValue(error.message);
    }
  }
);

export const startARSession = createAsyncThunk(
  'ar/startSession',
  async (config: ARSessionConfig, {rejectWithValue}) => {
    try {
      const result = await arService.startSession(config);
      return result;
    } catch (error: any) {
      return rejectWithValue(error.message);
    }
  }
);

export const stopARSession = createAsyncThunk(
  'ar/stopSession',
  async (_, {rejectWithValue}) => {
    try {
      await arService.stopSession();
      return null;
    } catch (error: any) {
      return rejectWithValue(error.message);
    }
  }
);

export const createSpatialAnchor = createAsyncThunk(
  'ar/createAnchor',
  async (data: {equipmentId: string; position: any; rotation: any}, {rejectWithValue}) => {
    try {
      const anchor = await arService.createSpatialAnchor(data);
      return anchor;
    } catch (error: any) {
      return rejectWithValue(error.message);
    }
  }
);

export const loadSpatialAnchors = createAsyncThunk(
  'ar/loadAnchors',
  async (buildingId: string, {rejectWithValue}) => {
    try {
      const anchors = await arService.loadSpatialAnchors(buildingId);
      return anchors;
    } catch (error: any) {
      return rejectWithValue(error.message);
    }
  }
);

export const updateSpatialAnchor = createAsyncThunk(
  'ar/updateAnchor',
  async (data: {anchorId: string; position: any; rotation: any}, {rejectWithValue}) => {
    try {
      const anchor = await arService.updateSpatialAnchor(data);
      return anchor;
    } catch (error: any) {
      return rejectWithValue(error.message);
    }
  }
);

// AR slice
const arSlice = createSlice({
  name: 'ar',
  initialState,
  reducers: {
    setTrackingState: (state, action: PayloadAction<'normal' | 'limited' | 'notAvailable'>) => {
      state.trackingState = action.payload;
    },
    setSelectedAnchor: (state, action: PayloadAction<SpatialAnchor | null>) => {
      state.selectedAnchor = action.payload;
    },
    setCameraPosition: (state, action: PayloadAction<{position: any; rotation: any}>) => {
      state.cameraPosition = action.payload.position;
      state.cameraRotation = action.payload.rotation;
    },
    setLightingEstimate: (state, action: PayloadAction<any>) => {
      state.lightingEstimate = action.payload;
    },
    addDetectedPlane: (state, action: PayloadAction<any>) => {
      state.detectedPlanes.push(action.payload);
    },
    removeDetectedPlane: (state, action: PayloadAction<string>) => {
      state.detectedPlanes = state.detectedPlanes.filter(plane => plane.id !== action.payload);
    },
    clearDetectedPlanes: (state) => {
      state.detectedPlanes = [];
    },
    addDetectedAnchor: (state, action: PayloadAction<SpatialAnchor>) => {
      state.detectedAnchors.push(action.payload);
    },
    removeDetectedAnchor: (state, action: PayloadAction<string>) => {
      state.detectedAnchors = state.detectedAnchors.filter(anchor => anchor.id !== action.payload);
    },
    clearDetectedAnchors: (state) => {
      state.detectedAnchors = [];
    },
  },
  extraReducers: (builder) => {
    // Initialize AR
    builder
      .addCase(initializeAR.fulfilled, (state, action) => {
        state.isSupported = action.payload.isSupported;
        state.permissionGranted = action.payload.permissionGranted;
      });

    // Start AR session
    builder
      .addCase(startARSession.fulfilled, (state) => {
        state.sessionActive = true;
        state.trackingState = 'normal';
      })
      .addCase(startARSession.rejected, (state) => {
        state.sessionActive = false;
        state.trackingState = 'notAvailable';
      });

    // Stop AR session
    builder
      .addCase(stopARSession.fulfilled, (state) => {
        state.sessionActive = false;
        state.trackingState = 'notAvailable';
        state.detectedAnchors = [];
        state.detectedPlanes = [];
        state.selectedAnchor = null;
        state.cameraPosition = null;
        state.cameraRotation = null;
        state.lightingEstimate = null;
      });

    // Create spatial anchor
    builder
      .addCase(createSpatialAnchor.fulfilled, (state, action) => {
        state.detectedAnchors.push(action.payload);
      });

    // Load spatial anchors
    builder
      .addCase(loadSpatialAnchors.fulfilled, (state, action) => {
        state.detectedAnchors = action.payload;
      });

    // Update spatial anchor
    builder
      .addCase(updateSpatialAnchor.fulfilled, (state, action) => {
        const index = state.detectedAnchors.findIndex(anchor => anchor.id === action.payload.id);
        if (index !== -1) {
          state.detectedAnchors[index] = action.payload;
        }
      });
  },
});

export const {
  setTrackingState,
  setSelectedAnchor,
  setCameraPosition,
  setLightingEstimate,
  addDetectedPlane,
  removeDetectedPlane,
  clearDetectedPlanes,
  addDetectedAnchor,
  removeDetectedAnchor,
  clearDetectedAnchors,
} = arSlice.actions;

export default arSlice.reducer;
