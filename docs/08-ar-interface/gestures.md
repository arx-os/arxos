# AR Gesture Controls

## Interacting with Building Objects

### Tap Gestures

```swift
// Single tap - Select object
@objc func handleTap(_ gesture: UITapGestureRecognizer) {
    let location = gesture.location(in: sceneView)
    let hitResults = sceneView.hitTest(location)
    
    if let node = hitResults.first?.node,
       let arxObject = node.arxObject {
        selectObject(arxObject)
    }
}

// Double tap - Quick action
@objc func handleDoubleTap(_ gesture: UITapGestureRecognizer) {
    if let selected = selectedObject {
        toggleOutlet(selected)  // or other quick action
    }
}
```

### Pinch to Zoom

```swift
// Zoom in/out on building model
@objc func handlePinch(_ gesture: UIPinchGestureRecognizer) {
    let scale = Float(gesture.scale)
    currentZoomLevel = currentZoomLevel * scale
    gesture.scale = 1.0
    
    updateVisualization(zoom: currentZoomLevel)
}
```

### Long Press

```swift
// Long press for context menu
@objc func handleLongPress(_ gesture: UILongPressGestureRecognizer) {
    if gesture.state == .began {
        showContextMenu(at: gesture.location(in: sceneView))
    }
}
```

### Swipe Controls

```swift
// Swipe to navigate floors
@objc func handleSwipe(_ gesture: UISwipeGestureRecognizer) {
    switch gesture.direction {
    case .up:
        moveToFloor(current + 1)
    case .down:
        moveToFloor(current - 1)
    case .left, .right:
        cycleRooms(direction: gesture.direction)
    default:
        break
    }
}
```

### AR-Specific Gestures

```swift
// "Throw" gesture to capture
func detectThrowGesture() {
    // Track hand movement
    // Detect throwing motion
    // Launch capture animation
}

// "Pull" gesture to extract data
func detectPullGesture() {
    // Track pinch and pull
    // Extract object data
    // Show in detail panel
}
```

---

→ Next: [Legacy Documentation](../09-legacy/)