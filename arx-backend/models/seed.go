package models

import (
	"log"

	"gorm.io/gorm"
)

func SeedCategories(db *gorm.DB) {
	categories := []string{
		"Electrical",
		"Plumbing",
		"HVAC",
		"Fire Alarm",
		"Security",
		"Low Voltage",
		"Networking",
		"Mechanical",
		"Telecommunications",
	}
	for _, name := range categories {
		var existing Category
		if err := db.Where("name = ?", name).First(&existing).Error; err == gorm.ErrRecordNotFound {
			newCategory := Category{Name: name}
			if err := db.Create(&newCategory).Error; err != nil {
				log.Printf("Failed to seed category '%s': %v", name, err)
			} else {
				log.Printf("Seeded category: %s", name)
			}
		}
	}
}
