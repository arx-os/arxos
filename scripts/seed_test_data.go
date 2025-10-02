package main

import (
	"fmt"
)

// TODO: This script needs to be updated to use the new architecture
// For now, commenting out the main function to prevent build errors
func main() {
	fmt.Println("⚠️  Seed test data script is temporarily disabled")
	fmt.Println("   This script needs to be updated to use the new architecture")
	return
}

func mainDisabled() {
	/*
		// Connect to database
		ctx := context.Background()
		db, err := infrastructure.NewDatabase(nil) // TODO: Pass proper config
		if err != nil {
			log.Fatal("Failed to connect to database:", err)
		}
		defer db.Close()

		// Create a test floor plan
		floorPlanID := uuid.New().String()
		now := time.Now()
		floorPlan := &models.FloorPlan{
			ID:        floorPlanID,
			Name:      "Test Building - Floor 1",
			Building:  "Test Building",
			Level:     1,
			CreatedAt: &now,
			UpdatedAt: &now,
		}

		if err := db.SaveFloorPlan(ctx, floorPlan); err != nil {
			log.Printf("Failed to create floor plan (may already exist): %v", err)
		} else {
			fmt.Println("Created floor plan:", floorPlanID)
		}

		// Add some rooms
		rooms := []models.Room{
			{
				ID:   uuid.New().String(),
				Name: "Conference Room",
				Bounds: models.Bounds{
					MinX: 10, MinY: 10,
					MaxX: 200, MaxY: 150,
				},
			},
			{
				ID:   uuid.New().String(),
				Name: "Office 101",
				Bounds: models.Bounds{
					MinX: 210, MinY: 10,
					MaxX: 350, MaxY: 150,
				},
			},
			{
				ID:   uuid.New().String(),
				Name: "Server Room",
				Bounds: models.Bounds{
					MinX: 10, MinY: 160,
					MaxX: 150, MaxY: 250,
				},
			},
			{
				ID:   uuid.New().String(),
				Name: "Break Room",
				Bounds: models.Bounds{
					MinX: 160, MinY: 160,
					MaxX: 350, MaxY: 250,
				},
			},
		}

		for _, room := range rooms {
			// Need to save room with floor plan ID
			query := `
				INSERT INTO rooms (id, name, min_x, min_y, max_x, max_y, floor_plan_id)
				VALUES (?, ?, ?, ?, ?, ?, ?)
			`
			_, err := db.Exec(ctx, query, room.ID, room.Name,
				room.Bounds.MinX, room.Bounds.MinY,
				room.Bounds.MaxX, room.Bounds.MaxY, floorPlanID)

			if err != nil {
				log.Printf("Failed to create room %s: %v", room.Name, err)
			} else {
				fmt.Printf("Created room: %s\n", room.Name)
			}
		}

		// Add some equipment
		equipment := []models.Equipment{
			{
				ID:       uuid.New().String(),
				Name:     "Switch-01",
				Type:     "switch",
				Location: &models.Point3D{X: 100, Y: 80, Z: 0},
				Status:   models.StatusNormal,
			},
			{
				ID:       uuid.New().String(),
				Name:     "Outlet-01",
				Type:     "outlet",
				Location: &models.Point3D{X: 280, Y: 80, Z: 0},
				Status:   models.StatusNormal,
			},
			{
				ID:       uuid.New().String(),
				Name:     "Panel-100",
				Type:     "panel",
				Location: &models.Point3D{X: 80, Y: 200, Z: 0},
				Status:   models.StatusOffline,
			},
			{
				ID:       uuid.New().String(),
				Name:     "Outlet-02",
				Type:     "outlet",
				Location: &models.Point3D{X: 250, Y: 200, Z: 0},
				Status:   models.StatusFailed,
			},
		}

		for _, eq := range equipment {
			query := `
				INSERT INTO equipment (id, name, type, location_x, location_y, status, floor_plan_id)
				VALUES (?, ?, ?, ?, ?, ?, ?)
			`
			_, err := db.Exec(ctx, query, eq.ID, eq.Name, eq.Type,
				eq.Location.X, eq.Location.Y, eq.Status, floorPlanID)

			if err != nil {
				log.Printf("Failed to create equipment %s: %v", eq.Name, err)
			} else {
				fmt.Printf("Created equipment: %s\n", eq.Name)
			}
		}

		// Create a test organization
		orgID := uuid.New().String()
		org := &models.Organization{
			ID:           orgID,
			Name:         "Test Organization",
			Slug:         "test-org",
			Plan:         models.PlanFree,
			Status:       "active",
			MaxUsers:     5,
			MaxBuildings: 2,
			CreatedAt:    now,
			UpdatedAt:    now,
		}

		if err := db.CreateOrganization(ctx, org); err != nil {
			log.Printf("Failed to create organization (may already exist): %v", err)
		} else {
			fmt.Println("Created organization:", orgID)

			// Add admin user to organization
			if err := db.AddOrganizationMember(ctx, orgID, "admin", string(models.RoleOwner)); err != nil {
				log.Printf("Failed to add admin to organization: %v", err)
			} else {
				fmt.Println("Added admin user as owner of organization")
			}
		}

		fmt.Println("\nTest data seeded successfully!")
		fmt.Printf("Floor Plan ID: %s\n", floorPlanID)
		fmt.Printf("Organization ID: %s\n", orgID)
	*/
}
