package main

import (
	"context"
	"testing"

	"github.com/arx-os/arxos/internal/app/types"
	"github.com/stretchr/testify/assert"
)

// Test basic command functions
func TestRemoveEquipment(t *testing.T) {
	ctx := context.Background()
	services := &types.Services{} // Empty services for now

	err := removeEquipment(ctx, services, "test-id")
	assert.NoError(t, err)
}

func TestRemoveRoom(t *testing.T) {
	ctx := context.Background()
	services := &types.Services{} // Empty services for now

	err := removeRoom(ctx, services, "test-id")
	assert.NoError(t, err)
}

func TestRemoveFloor(t *testing.T) {
	ctx := context.Background()
	services := &types.Services{} // Empty services for now

	err := removeFloor(ctx, services, "test-id")
	assert.NoError(t, err)
}
