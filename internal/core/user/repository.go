package user

import (
	"context"

	"github.com/google/uuid"
)

// Repository defines the interface for user persistence
type Repository interface {
	// User operations
	Create(ctx context.Context, user *User) error
	GetByID(ctx context.Context, id uuid.UUID) (*User, error)
	GetByEmail(ctx context.Context, email string) (*User, error)
	Update(ctx context.Context, user *User) error
	Delete(ctx context.Context, id uuid.UUID) error
	List(ctx context.Context, limit, offset int) ([]*User, error)

	// Session operations
	CreateSession(ctx context.Context, session *UserSession) error
	GetSession(ctx context.Context, token string) (*UserSession, error)
	GetSessionByRefreshToken(ctx context.Context, refreshToken string) (*UserSession, error)
	UpdateSession(ctx context.Context, session *UserSession) error
	DeleteSession(ctx context.Context, id uuid.UUID) error
	DeleteUserSessions(ctx context.Context, userID uuid.UUID) error
	DeleteExpiredSessions(ctx context.Context) error

	// Password reset operations
	CreatePasswordResetToken(ctx context.Context, token *PasswordResetToken) error
	GetPasswordResetToken(ctx context.Context, token string) (*PasswordResetToken, error)
	MarkPasswordResetTokenUsed(ctx context.Context, token string) error
	DeleteExpiredPasswordResetTokens(ctx context.Context) error

	// Organization operations
	CreateOrganization(ctx context.Context, org *Organization) error
	GetOrganization(ctx context.Context, id uuid.UUID) (*Organization, error)
	GetOrganizationsByUser(ctx context.Context, userID uuid.UUID) ([]*Organization, error)
	UpdateOrganization(ctx context.Context, org *Organization) error
	DeleteOrganization(ctx context.Context, id uuid.UUID) error

	// Organization member operations
	AddOrganizationMember(ctx context.Context, orgID, userID uuid.UUID, role string) error
	RemoveOrganizationMember(ctx context.Context, orgID, userID uuid.UUID) error
	UpdateOrganizationMemberRole(ctx context.Context, orgID, userID uuid.UUID, role string) error
	GetOrganizationMembers(ctx context.Context, orgID uuid.UUID) ([]*OrganizationMember, error)
	GetOrganizationMember(ctx context.Context, orgID, userID uuid.UUID) (*OrganizationMember, error)

	// Organization invitation operations
	CreateOrganizationInvitation(ctx context.Context, invitation *OrganizationInvitation) error
	GetOrganizationInvitation(ctx context.Context, id uuid.UUID) (*OrganizationInvitation, error)
	GetOrganizationInvitationByToken(ctx context.Context, token string) (*OrganizationInvitation, error)
	ListOrganizationInvitations(ctx context.Context, orgID uuid.UUID) ([]*OrganizationInvitation, error)
	AcceptOrganizationInvitation(ctx context.Context, token string, userID uuid.UUID) error
	RevokeOrganizationInvitation(ctx context.Context, id uuid.UUID) error
}