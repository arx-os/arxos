// ARKit/ARCore type declarations for React Native

declare namespace ARKit {
  interface ARSession {
    runWithConfiguration(config: ARConfiguration): void;
    pause(): void;
    addAnchor(anchor: ARAnchor): void;
    removeAnchor(anchor: ARAnchor): void;
  }

  interface ARConfiguration {
    planeDetection: ARPlaneDetection;
    worldAlignment: ARWorldAlignment;
    isLightEstimationEnabled: boolean;
  }

  interface ARAnchor {
    identifier: string;
    transform: ARMatrix4;
  }

  interface ARMatrix4 {
    m11: number; m12: number; m13: number; m14: number;
    m21: number; m22: number; m23: number; m24: number;
    m31: number; m32: number; m33: number; m34: number;
    m41: number; m42: number; m43: number; m44: number;
  }

  interface ARSCNView {
    session: ARSession;
    scene: SCNScene;
    delegate?: ARSCNViewDelegate;
  }

  interface ARSCNViewDelegate {
    renderer(renderer: SCNRenderer, nodeFor: ARAnchor): SCNNode;
    renderer(renderer: SCNRenderer, didAdd: SCNNode, forAnchor: ARAnchor): void;
    renderer(renderer: SCNRenderer, didUpdate: SCNNode, forAnchor: ARAnchor): void;
    renderer(renderer: SCNRenderer, didRemove: SCNNode, forAnchor: ARAnchor): void;
  }

  interface SCNScene {
    rootNode: SCNNode;
  }

  interface SCNNode {
    position: SCNVector3;
    rotation: SCNVector4;
    scale: SCNVector3;
    addChildNode(child: SCNNode): void;
    removeFromParentNode(): void;
  }

  interface SCNVector3 {
    x: number;
    y: number;
    z: number;
  }

  interface SCNVector4 {
    x: number;
    y: number;
    z: number;
    w: number;
  }

  interface SCNRenderer {
    scene: SCNScene;
  }

  enum ARPlaneDetection {
    None = 0,
    Horizontal = 1,
    Vertical = 2,
  }

  enum ARWorldAlignment {
    Gravity = 0,
    GravityAndHeading = 1,
    Camera = 2,
  }
}

declare namespace ARCore {
  interface ARSession {
    start(): void;
    pause(): void;
    addAnchor(anchor: ARAnchor): void;
    removeAnchor(anchor: ARAnchor): void;
  }

  interface ARAnchor {
    id: string;
    pose: ARPose;
  }

  interface ARPose {
    translation: ARVector3;
    rotation: ARQuaternion;
  }

  interface ARVector3 {
    x: number;
    y: number;
    z: number;
  }

  interface ARQuaternion {
    x: number;
    y: number;
    z: number;
    w: number;
  }

  interface ARView {
    session: ARSession;
    scene: ARScene;
  }

  interface ARScene {
    rootNode: ARNode;
  }

  interface ARNode {
    position: ARVector3;
    rotation: ARQuaternion;
    scale: ARVector3;
    addChild(child: ARNode): void;
    removeFromParent(): void;
  }
}

// Global AR types
declare const ARSession: typeof ARKit.ARSession;
declare const ARSCNView: typeof ARKit.ARSCNView;
declare const ARConfiguration: typeof ARKit.ARConfiguration;
declare const ARAnchor: typeof ARKit.ARAnchor;
