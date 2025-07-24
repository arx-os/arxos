package security

import (
	"fmt"
	"sync"
	"time"
)

// AuditLogger defines the interface for audit logging
type AuditLogger interface {
	LogPolicyEvent(eventType, policyID string, details map[string]interface{})
	LogAccessRequest(request *AccessRequest, decision *AccessDecision)
}

// Policy represents an ABAC policy
type Policy struct {
	ID          string                 `json:"id"`
	Name        string                 `json:"name"`
	Description string                 `json:"description"`
	Effect      string                 `json:"effect"` // allow, deny
	Priority    int                    `json:"priority"`
	Conditions  PolicyConditions       `json:"conditions"`
	CreatedAt   time.Time              `json:"created_at"`
	UpdatedAt   time.Time              `json:"updated_at"`
	IsActive    bool                   `json:"is_active"`
	Metadata    map[string]interface{} `json:"metadata"`
}

// PolicyConditions defines the conditions for a policy
type PolicyConditions struct {
	UserAttributes     map[string]interface{} `json:"user_attributes,omitempty"`
	ResourceAttributes map[string]interface{} `json:"resource_attributes,omitempty"`
	Actions            []string               `json:"actions,omitempty"`
	Context            map[string]interface{} `json:"context,omitempty"`
	TimeConstraints    *TimeConstraints       `json:"time_constraints,omitempty"`
	IPConstraints      *IPConstraints         `json:"ip_constraints,omitempty"`
}

// TimeConstraints defines time-based constraints
type TimeConstraints struct {
	StartTime  *time.Time `json:"start_time,omitempty"`
	EndTime    *time.Time `json:"end_time,omitempty"`
	DaysOfWeek []int      `json:"days_of_week,omitempty"` // 0=Sunday, 1=Monday, etc.
	TimeZone   string     `json:"time_zone,omitempty"`
}

// IPConstraints defines IP-based constraints
type IPConstraints struct {
	AllowedIPs    []string `json:"allowed_ips,omitempty"`
	BlockedIPs    []string `json:"blocked_ips,omitempty"`
	AllowedRanges []string `json:"allowed_ranges,omitempty"`
	BlockedRanges []string `json:"blocked_ranges,omitempty"`
}

// AccessRequest represents an access request
type AccessRequest struct {
	ID          string                 `json:"id"`
	UserID      string                 `json:"user_id"`
	ResourceID  string                 `json:"resource_id"`
	Action      string                 `json:"action"`
	Context     map[string]interface{} `json:"context"`
	RequestedAt time.Time              `json:"requested_at"`
	IPAddress   string                 `json:"ip_address,omitempty"`
	UserAgent   string                 `json:"user_agent,omitempty"`
	SessionID   string                 `json:"session_id,omitempty"`
}

// AccessDecision represents an access control decision
type AccessDecision struct {
	RequestID   string                 `json:"request_id"`
	Granted     bool                   `json:"granted"`
	Reason      string                 `json:"reason"`
	PolicyID    string                 `json:"policy_id,omitempty"`
	EvaluatedAt time.Time              `json:"evaluated_at"`
	Details     map[string]interface{} `json:"details"`
	Constraints []string               `json:"constraints,omitempty"`
}

// AuthzService provides authorization services
type AuthzService struct {
	policies      map[string]*Policy
	policiesMutex sync.RWMutex
	decisionCache map[string]*AccessDecision
	cacheMutex    sync.RWMutex
	cacheExpiry   time.Duration
	auditLogger   AuditLogger
}

// NewAuthzService creates a new authorization service
func NewAuthzService(auditLogger AuditLogger) *AuthzService {
	return &AuthzService{
		policies:      make(map[string]*Policy),
		decisionCache: make(map[string]*AccessDecision),
		cacheExpiry:   5 * time.Minute,
		auditLogger:   auditLogger,
	}
}

// AddPolicy adds a new policy
func (as *AuthzService) AddPolicy(policy *Policy) error {
	if policy.ID == "" {
		policy.ID = generatePolicyID()
	}

	policy.CreatedAt = time.Now()
	policy.UpdatedAt = time.Now()

	as.policiesMutex.Lock()
	as.policies[policy.ID] = policy
	as.policiesMutex.Unlock()

	// Log policy addition
	as.auditLogger.LogPolicyEvent("policy_added", policy.ID, map[string]interface{}{
		"policy_name": policy.Name,
		"effect":      policy.Effect,
		"priority":    policy.Priority,
	})

	return nil
}

// UpdatePolicy updates an existing policy
func (as *AuthzService) UpdatePolicy(policyID string, updates map[string]interface{}) error {
	as.policiesMutex.Lock()
	policy, exists := as.policies[policyID]
	if !exists {
		as.policiesMutex.Unlock()
		return fmt.Errorf("policy not found: %s", policyID)
	}

	// Update fields
	if name, ok := updates["name"].(string); ok {
		policy.Name = name
	}
	if description, ok := updates["description"].(string); ok {
		policy.Description = description
	}
	if effect, ok := updates["effect"].(string); ok {
		policy.Effect = effect
	}
	if priority, ok := updates["priority"].(int); ok {
		policy.Priority = priority
	}
	if isActive, ok := updates["is_active"].(bool); ok {
		policy.IsActive = isActive
	}
	if conditions, ok := updates["conditions"].(PolicyConditions); ok {
		policy.Conditions = conditions
	}

	policy.UpdatedAt = time.Now()
	as.policiesMutex.Unlock()

	// Clear cache for this policy
	as.clearPolicyCache(policyID)

	// Log policy update
	as.auditLogger.LogPolicyEvent("policy_updated", policyID, updates)

	return nil
}

// RemovePolicy removes a policy
func (as *AuthzService) RemovePolicy(policyID string) error {
	as.policiesMutex.Lock()
	policy, exists := as.policies[policyID]
	if !exists {
		as.policiesMutex.Unlock()
		return fmt.Errorf("policy not found: %s", policyID)
	}

	delete(as.policies, policyID)
	as.policiesMutex.Unlock()

	// Clear cache for this policy
	as.clearPolicyCache(policyID)

	// Log policy removal
	as.auditLogger.LogPolicyEvent("policy_removed", policyID, map[string]interface{}{
		"policy_name": policy.Name,
	})

	return nil
}

// GetPolicy retrieves a policy by ID
func (as *AuthzService) GetPolicy(policyID string) (*Policy, error) {
	as.policiesMutex.RLock()
	defer as.policiesMutex.RUnlock()

	policy, exists := as.policies[policyID]
	if !exists {
		return nil, fmt.Errorf("policy not found: %s", policyID)
	}

	return policy, nil
}

// ListPolicies returns all policies
func (as *AuthzService) ListPolicies() []*Policy {
	as.policiesMutex.RLock()
	defer as.policiesMutex.RUnlock()

	policies := make([]*Policy, 0, len(as.policies))
	for _, policy := range as.policies {
		policies = append(policies, policy)
	}

	return policies
}

// CheckAccess checks if a user has access to a resource
func (as *AuthzService) CheckAccess(user *User, resource *Resource, action string, context map[string]interface{}) (*AccessDecision, error) {
	request := &AccessRequest{
		ID:          generateRequestID(),
		UserID:      user.ID,
		ResourceID:  resource.ID,
		Action:      action,
		Context:     context,
		RequestedAt: time.Now(),
	}

	// Check cache first
	cacheKey := as.generateCacheKey(request)
	if decision := as.getCachedDecision(cacheKey); decision != nil {
		return decision, nil
	}

	// Evaluate policies
	decision := as.evaluatePolicies(user, resource, request)

	// Cache decision
	as.cacheDecision(cacheKey, decision)

	// Log access request
	as.auditLogger.LogAccessRequest(request, decision)

	return decision, nil
}

// evaluatePolicies evaluates all applicable policies
func (as *AuthzService) evaluatePolicies(user *User, resource *Resource, request *AccessRequest) *AccessDecision {
	as.policiesMutex.RLock()
	policies := make([]*Policy, 0, len(as.policies))
	for _, policy := range as.policies {
		if policy.IsActive {
			policies = append(policies, policy)
		}
	}
	as.policiesMutex.RUnlock()

	// Sort policies by priority (highest first)
	sortPoliciesByPriority(policies)

	decision := &AccessDecision{
		RequestID:   request.ID,
		Granted:     false,
		Reason:      "No applicable policies found",
		EvaluatedAt: time.Now(),
		Details:     make(map[string]interface{}),
	}

	for _, policy := range policies {
		if as.evaluatePolicy(policy, user, resource, request) {
			decision.Granted = policy.Effect == "allow"
			decision.PolicyID = policy.ID
			decision.Reason = fmt.Sprintf("Policy '%s' %s access", policy.Name, policy.Effect)
			break
		}
	}

	return decision
}

// evaluatePolicy evaluates a single policy
func (as *AuthzService) evaluatePolicy(policy *Policy, user *User, resource *Resource, request *AccessRequest) bool {
	conditions := policy.Conditions

	// Check user attributes
	if !as.checkUserAttributes(user, conditions.UserAttributes) {
		return false
	}

	// Check resource attributes
	if !as.checkResourceAttributes(resource, conditions.ResourceAttributes) {
		return false
	}

	// Check action
	if !as.checkAction(request.Action, conditions.Actions) {
		return false
	}

	// Check context
	if !as.checkContext(request.Context, conditions.Context) {
		return false
	}

	// Check time constraints
	if conditions.TimeConstraints != nil {
		if !as.checkTimeConstraints(conditions.TimeConstraints) {
			return false
		}
	}

	// Check IP constraints
	if conditions.IPConstraints != nil {
		if !as.checkIPConstraints(request.Context, conditions.IPConstraints) {
			return false
		}
	}

	return true
}

// checkUserAttributes checks if user attributes match policy conditions
func (as *AuthzService) checkUserAttributes(user *User, requiredAttributes map[string]interface{}) bool {
	for key, expectedValue := range requiredAttributes {
		if actualValue, exists := user.Attributes[key]; !exists || actualValue != expectedValue {
			return false
		}
	}
	return true
}

// checkResourceAttributes checks if resource attributes match policy conditions
func (as *AuthzService) checkResourceAttributes(resource *Resource, requiredAttributes map[string]interface{}) bool {
	for key, expectedValue := range requiredAttributes {
		if actualValue, exists := resource.Attributes[key]; !exists || actualValue != expectedValue {
			return false
		}
	}
	return true
}

// checkAction checks if the action is allowed
func (as *AuthzService) checkAction(action string, allowedActions []string) bool {
	if len(allowedActions) == 0 {
		return true // No action constraints
	}

	for _, allowedAction := range allowedActions {
		if action == allowedAction {
			return true
		}
	}
	return false
}

// checkContext checks if context matches policy conditions
func (as *AuthzService) checkContext(context map[string]interface{}, requiredContext map[string]interface{}) bool {
	for key, expectedValue := range requiredContext {
		if actualValue, exists := context[key]; !exists || actualValue != expectedValue {
			return false
		}
	}
	return true
}

// checkTimeConstraints checks if current time meets policy constraints
func (as *AuthzService) checkTimeConstraints(constraints *TimeConstraints) bool {
	now := time.Now()

	if constraints.StartTime != nil && now.Before(*constraints.StartTime) {
		return false
	}

	if constraints.EndTime != nil && now.After(*constraints.EndTime) {
		return false
	}

	if len(constraints.DaysOfWeek) > 0 {
		currentDay := int(now.Weekday())
		dayAllowed := false
		for _, allowedDay := range constraints.DaysOfWeek {
			if currentDay == allowedDay {
				dayAllowed = true
				break
			}
		}
		if !dayAllowed {
			return false
		}
	}

	return true
}

// checkIPConstraints checks if IP address meets policy constraints
func (as *AuthzService) checkIPConstraints(context map[string]interface{}, constraints *IPConstraints) bool {
	ipAddress, exists := context["ip_address"].(string)
	if !exists {
		return false
	}

	// Check blocked IPs first
	for _, blockedIP := range constraints.BlockedIPs {
		if ipAddress == blockedIP {
			return false
		}
	}

	// Check allowed IPs
	if len(constraints.AllowedIPs) > 0 {
		ipAllowed := false
		for _, allowedIP := range constraints.AllowedIPs {
			if ipAddress == allowedIP {
				ipAllowed = true
				break
			}
		}
		if !ipAllowed {
			return false
		}
	}

	return true
}

// getCachedDecision retrieves a cached decision
func (as *AuthzService) getCachedDecision(cacheKey string) *AccessDecision {
	as.cacheMutex.RLock()
	defer as.cacheMutex.RUnlock()

	if decision, exists := as.decisionCache[cacheKey]; exists {
		if time.Since(decision.EvaluatedAt) < as.cacheExpiry {
			return decision
		}
		// Remove expired decision
		delete(as.decisionCache, cacheKey)
	}

	return nil
}

// cacheDecision caches an access decision
func (as *AuthzService) cacheDecision(cacheKey string, decision *AccessDecision) {
	as.cacheMutex.Lock()
	as.decisionCache[cacheKey] = decision
	as.cacheMutex.Unlock()
}

// clearPolicyCache clears cached decisions for a policy
func (as *AuthzService) clearPolicyCache(policyID string) {
	as.cacheMutex.Lock()
	// Clear all cached decisions (simplified implementation)
	as.decisionCache = make(map[string]*AccessDecision)
	as.cacheMutex.Unlock()
}

// generateCacheKey generates a cache key for an access request
func (as *AuthzService) generateCacheKey(request *AccessRequest) string {
	// Create a hash of the request parameters
	data := fmt.Sprintf("%s:%s:%s:%s", request.UserID, request.ResourceID, request.Action, request.IPAddress)
	return fmt.Sprintf("%x", hashString(data))
}

// generatePolicyID generates a unique policy ID
func generatePolicyID() string {
	return fmt.Sprintf("policy_%d", time.Now().UnixNano())
}

// generateRequestID generates a unique request ID
func generateRequestID() string {
	return fmt.Sprintf("req_%d", time.Now().UnixNano())
}

// hashString creates a simple hash of a string
func hashString(s string) uint32 {
	h := uint32(0)
	for _, c := range s {
		h = h*31 + uint32(c)
	}
	return h
}

// sortPoliciesByPriority sorts policies by priority (highest first)
func sortPoliciesByPriority(policies []*Policy) {
	// Simple bubble sort for small lists
	for i := 0; i < len(policies)-1; i++ {
		for j := 0; j < len(policies)-i-1; j++ {
			if policies[j].Priority < policies[j+1].Priority {
				policies[j], policies[j+1] = policies[j+1], policies[j]
			}
		}
	}
}

// GetPolicyStats returns policy statistics
func (as *AuthzService) GetPolicyStats() map[string]interface{} {
	as.policiesMutex.RLock()
	defer as.policiesMutex.RUnlock()

	totalPolicies := len(as.policies)
	activePolicies := 0
	allowPolicies := 0
	denyPolicies := 0

	for _, policy := range as.policies {
		if policy.IsActive {
			activePolicies++
		}
		if policy.Effect == "allow" {
			allowPolicies++
		} else if policy.Effect == "deny" {
			denyPolicies++
		}
	}

	return map[string]interface{}{
		"total_policies":    totalPolicies,
		"active_policies":   activePolicies,
		"allow_policies":    allowPolicies,
		"deny_policies":     denyPolicies,
		"inactive_policies": totalPolicies - activePolicies,
	}
}
