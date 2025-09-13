import React from 'react';
import { useRoute, RouteProp } from '@react-navigation/native';
import { MainStackParamList } from '../../navigation/MainNavigator';
import { ARScene } from '../../components/ar/ARScene';

type ARViewRouteProp = RouteProp<MainStackParamList, 'ARView'>;

export const ARViewScreen: React.FC = () => {
  const route = useRoute<ARViewRouteProp>();
  const { floorPlanId } = route.params;

  return <ARScene floorPlanId={floorPlanId} />;
};