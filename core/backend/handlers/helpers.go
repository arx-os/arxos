package handlers

import (
	"github.com/arxos/arxos/core/backend/db"
	"github.com/arxos/arxos/core/backend/logic_engine"
	"github.com/arxos/arxos/core/backend/models"
	"github.com/arxos/arxos/core/backend/services"
	"encoding/json"
	"net/http"
	"os"

	"github.com/golang-jwt/jwt/v4"
)

// getUserFromRequest extracts the user from the JWT and fetches the user object from the database.
func GetUserFromRequest(r *http.Request) (*models.User, error) {
	tokenStr := r.Header.Get("Authorization")
	if len(tokenStr) < 8 || tokenStr[:7] != "Bearer " {
		return nil, http.ErrNoCookie
	}
	tokenStr = tokenStr[7:]
	token, _ := jwt.Parse(tokenStr, func(t *jwt.Token) (interface{}, error) {
		return []byte(os.Getenv("JWT_SECRET")), nil
	})
	if claims, ok := token.Claims.(jwt.MapClaims); ok && token.Valid {
		userID := uint(claims["user_id"].(float64))
		var user models.User
		if err := db.DB.First(&user, userID).Error; err != nil {
			return nil, err
		}
		return &user, nil
	}
	return nil, http.ErrNoCookie
}

// GetObjectTypesRegistry returns the full object types registry as JSON.
func GetObjectTypesRegistry(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(logic_engine.ObjectTypesRegistry)
}

// GetBehaviorProfilesRegistry returns the full behavior profiles registry as JSON.
func GetBehaviorProfilesRegistry(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(logic_engine.BehaviorProfilesRegistry)
}

// respondWithJSON sends a JSON response with the given status code and data
func respondWithJSON(w http.ResponseWriter, statusCode int, data interface{}) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(statusCode)
	json.NewEncoder(w).Encode(data)
}

// respondWithError sends a JSON error response with the given status code and message
func respondWithError(w http.ResponseWriter, statusCode int, message string) {
	respondWithJSON(w, statusCode, map[string]string{"error": message})
}
