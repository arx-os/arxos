package middleware

import (
	"github.com/arxos/arxos/core/backend/models"

	"gorm.io/gorm"
)

// Action: "view", "edit", "assign", "highlight", "comment"
func CheckObjectPermission(db *gorm.DB, user *models.User, objectCategory string, action string, projectID uint) bool {
	switch user.Role {
	case "owner":
		return true
	case "builder":
		// Check UserCategoryPermission for this user, category, and project
		var perm models.UserCategoryPermission
		err := db.Where("user_id = ? AND category_id = (SELECT id FROM categories WHERE name = ?) AND project_id = ?", user.ID, objectCategory, projectID).First(&perm).Error
		if err == nil {
			return action != "delete" // builders can't delete
		}
		return false
	case "inspector":
		return action == "highlight" || action == "view" || action == "comment"
	case "guest":
		return action == "view"
	default:
		return false
	}
}
