/**
 * Navigation-related type definitions
 */

export type RootStackParamList = {
  Home: undefined;
  Equipment: {
    equipmentId?: string;
    searchQuery?: string;
  };
  EquipmentDetail: {
    equipmentId: string;
  };
  AR: {
    equipmentId?: string;
    mode?: 'view' | 'edit' | 'create';
  };
  Camera: {
    equipmentId?: string;
    purpose: 'photo' | 'scan' | 'ar';
  };
  Settings: undefined;
  Login: undefined;
  Profile: undefined;
  Sync: undefined;
  Offline: undefined;
};

export type EquipmentStackParamList = {
  EquipmentList: undefined;
  EquipmentDetail: {
    equipmentId: string;
  };
  EquipmentEdit: {
    equipmentId: string;
  };
  EquipmentSearch: {
    query?: string;
    filters?: EquipmentSearchFilters;
  };
};

export type ARStackParamList = {
  ARView: {
    equipmentId?: string;
    mode?: 'view' | 'edit' | 'create';
  };
  ARCalibration: undefined;
  ARSettings: undefined;
};

export interface EquipmentSearchFilters {
  buildingId?: string;
  floorId?: string;
  roomId?: string;
  type?: string;
  status?: string;
  dateRange?: {
    start: string;
    end: string;
  };
}

export interface NavigationState {
  currentRoute: string;
  previousRoute: string | null;
  params: any;
  canGoBack: boolean;
}

export interface TabBarIconProps {
  focused: boolean;
  color: string;
  size: number;
}

export interface DrawerItemProps {
  label: string;
  icon: string;
  route: keyof RootStackParamList;
  badge?: number;
  disabled?: boolean;
}
