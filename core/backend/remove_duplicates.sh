#!/bin/bash

# Remove duplicate functions from users.go
# This script removes functions that are duplicated in buildings.go

# Find the line numbers for the duplicate functions
echo "Finding duplicate functions..."

# ListBuildings: lines 114-169
# CreateBuilding: lines 170-197
# GetBuilding: lines 198-239
# UpdateBuilding: lines 240-283
# ListFloors: lines 284-433
# HTMXListBuildingsSidebar: lines 474-502
# itoa: lines 503-507
# DeleteMarkup: lines 508-520

# Create a temporary file without the duplicate functions
sed '114,169d; 170,197d; 198,239d; 240,283d; 284,433d; 474,502d; 503,507d; 508,520d' handlers/users.go > handlers/users_temp.go

# Replace the original file
mv handlers/users_temp.go handlers/users.go

echo "Duplicate functions removed from users.go"
