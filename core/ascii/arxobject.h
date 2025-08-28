#ifndef ARXOBJECT_H
#define ARXOBJECT_H

#include <stdint.h>

// Simple ArxObject structure for ASCII rendering
typedef struct ArxObject {
    uint64_t id;
    char* path;
    char* name;
    float x, y, z;          // Position in meters
    float width, height, depth;  // Dimensions in meters
    float confidence;       // Confidence level 0.0-1.0
} ArxObject;

#endif // ARXOBJECT_H