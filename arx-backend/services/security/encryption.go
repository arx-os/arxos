package security

import (
	"crypto"
	"crypto/aes"
	"crypto/cipher"
	"crypto/rand"
	"crypto/rsa"
	"crypto/sha256"
	"crypto/x509"
	"encoding/pem"
	"fmt"
	"io"
	"sync"
	"time"
)

// EncryptionAlgorithm represents supported encryption algorithms
type EncryptionAlgorithm string

const (
	AlgorithmAES256  EncryptionAlgorithm = "AES-256-GCM"
	AlgorithmRSA2048 EncryptionAlgorithm = "RSA-2048"
	AlgorithmRSA4096 EncryptionAlgorithm = "RSA-4096"
)

// KeyType represents the type of encryption key
type KeyType string

const (
	KeyTypeSymmetric  KeyType = "symmetric"
	KeyTypeAsymmetric KeyType = "asymmetric"
)

// EncryptionKey represents an encryption key
type EncryptionKey struct {
	ID          string                 `json:"id"`
	Type        KeyType                `json:"type"`
	Algorithm   EncryptionAlgorithm    `json:"algorithm"`
	KeyData     []byte                 `json:"key_data"`
	PublicKey   []byte                 `json:"public_key,omitempty"`
	PrivateKey  []byte                 `json:"private_key,omitempty"`
	CreatedAt   time.Time              `json:"created_at"`
	ExpiresAt   *time.Time             `json:"expires_at,omitempty"`
	IsActive    bool                   `json:"is_active"`
	Description string                 `json:"description"`
	Metadata    map[string]interface{} `json:"metadata"`
}

// EncryptedData represents encrypted data
type EncryptedData struct {
	ID        string                 `json:"id"`
	KeyID     string                 `json:"key_id"`
	Algorithm EncryptionAlgorithm    `json:"algorithm"`
	Data      []byte                 `json:"data"`
	IV        []byte                 `json:"iv,omitempty"`
	Signature []byte                 `json:"signature,omitempty"`
	CreatedAt time.Time              `json:"created_at"`
	Metadata  map[string]interface{} `json:"metadata"`
}

// EncryptionService provides encryption and decryption services
type EncryptionService struct {
	keys                map[string]*EncryptionKey
	keysMutex           sync.RWMutex
	defaultKeyID        string
	keyRotationInterval time.Duration
}

// NewEncryptionService creates a new encryption service
func NewEncryptionService() *EncryptionService {
	return &EncryptionService{
		keys:                make(map[string]*EncryptionKey),
		keyRotationInterval: 30 * 24 * time.Hour, // 30 days
	}
}

// GenerateSymmetricKey generates a new symmetric encryption key
func (es *EncryptionService) GenerateSymmetricKey(algorithm EncryptionAlgorithm, description string) (*EncryptionKey, error) {
	var keySize int
	switch algorithm {
	case AlgorithmAES256:
		keySize = 32 // 256 bits
	default:
		return nil, fmt.Errorf("unsupported algorithm: %s", algorithm)
	}

	keyData := make([]byte, keySize)
	if _, err := io.ReadFull(rand.Reader, keyData); err != nil {
		return nil, fmt.Errorf("failed to generate key: %w", err)
	}

	key := &EncryptionKey{
		ID:          generateKeyID(),
		Type:        KeyTypeSymmetric,
		Algorithm:   algorithm,
		KeyData:     keyData,
		CreatedAt:   time.Now(),
		IsActive:    true,
		Description: description,
		Metadata:    make(map[string]interface{}),
	}

	es.keysMutex.Lock()
	es.keys[key.ID] = key
	if es.defaultKeyID == "" {
		es.defaultKeyID = key.ID
	}
	es.keysMutex.Unlock()

	return key, nil
}

// GenerateAsymmetricKeyPair generates a new asymmetric key pair
func (es *EncryptionService) GenerateAsymmetricKeyPair(algorithm EncryptionAlgorithm, description string) (*EncryptionKey, error) {
	var keySize int
	switch algorithm {
	case AlgorithmRSA2048:
		keySize = 2048
	case AlgorithmRSA4096:
		keySize = 4096
	default:
		return nil, fmt.Errorf("unsupported algorithm: %s", algorithm)
	}

	privateKey, err := rsa.GenerateKey(rand.Reader, keySize)
	if err != nil {
		return nil, fmt.Errorf("failed to generate key pair: %w", err)
	}

	publicKey := &privateKey.PublicKey

	// Encode private key
	privateKeyPEM := pem.EncodeToMemory(&pem.Block{
		Type:  "RSA PRIVATE KEY",
		Bytes: x509.MarshalPKCS1PrivateKey(privateKey),
	})

	// Encode public key
	publicKeyPEM := pem.EncodeToMemory(&pem.Block{
		Type:  "RSA PUBLIC KEY",
		Bytes: x509.MarshalPKCS1PublicKey(publicKey),
	})

	key := &EncryptionKey{
		ID:          generateKeyID(),
		Type:        KeyTypeAsymmetric,
		Algorithm:   algorithm,
		PrivateKey:  privateKeyPEM,
		PublicKey:   publicKeyPEM,
		CreatedAt:   time.Now(),
		IsActive:    true,
		Description: description,
		Metadata:    make(map[string]interface{}),
	}

	es.keysMutex.Lock()
	es.keys[key.ID] = key
	es.keysMutex.Unlock()

	return key, nil
}

// Encrypt encrypts data using the specified key
func (es *EncryptionService) Encrypt(data []byte, keyID string) (*EncryptedData, error) {
	es.keysMutex.RLock()
	key, exists := es.keys[keyID]
	es.keysMutex.RUnlock()

	if !exists {
		return nil, fmt.Errorf("key not found: %s", keyID)
	}

	if !key.IsActive {
		return nil, fmt.Errorf("key is not active: %s", keyID)
	}

	switch key.Type {
	case KeyTypeSymmetric:
		return es.encryptSymmetric(data, key)
	case KeyTypeAsymmetric:
		return es.encryptAsymmetric(data, key)
	default:
		return nil, fmt.Errorf("unsupported key type: %s", key.Type)
	}
}

// Decrypt decrypts data using the specified key
func (es *EncryptionService) Decrypt(encryptedData *EncryptedData, keyID string) ([]byte, error) {
	es.keysMutex.RLock()
	key, exists := es.keys[keyID]
	es.keysMutex.RUnlock()

	if !exists {
		return nil, fmt.Errorf("key not found: %s", keyID)
	}

	if !key.IsActive {
		return nil, fmt.Errorf("key is not active: %s", keyID)
	}

	switch key.Type {
	case KeyTypeSymmetric:
		return es.decryptSymmetric(encryptedData, key)
	case KeyTypeAsymmetric:
		return es.decryptAsymmetric(encryptedData, key)
	default:
		return nil, fmt.Errorf("unsupported key type: %s", key.Type)
	}
}

// encryptSymmetric encrypts data using symmetric encryption
func (es *EncryptionService) encryptSymmetric(data []byte, key *EncryptionKey) (*EncryptedData, error) {
	block, err := aes.NewCipher(key.KeyData)
	if err != nil {
		return nil, fmt.Errorf("failed to create cipher: %w", err)
	}

	gcm, err := cipher.NewGCM(block)
	if err != nil {
		return nil, fmt.Errorf("failed to create GCM: %w", err)
	}

	nonce := make([]byte, gcm.NonceSize())
	if _, err := io.ReadFull(rand.Reader, nonce); err != nil {
		return nil, fmt.Errorf("failed to generate nonce: %w", err)
	}

	ciphertext := gcm.Seal(nonce, nonce, data, nil)

	return &EncryptedData{
		ID:        generateEncryptedDataID(),
		KeyID:     key.ID,
		Algorithm: key.Algorithm,
		Data:      ciphertext,
		CreatedAt: time.Now(),
		Metadata:  make(map[string]interface{}),
	}, nil
}

// decryptSymmetric decrypts data using symmetric encryption
func (es *EncryptionService) decryptSymmetric(encryptedData *EncryptedData, key *EncryptionKey) ([]byte, error) {
	block, err := aes.NewCipher(key.KeyData)
	if err != nil {
		return nil, fmt.Errorf("failed to create cipher: %w", err)
	}

	gcm, err := cipher.NewGCM(block)
	if err != nil {
		return nil, fmt.Errorf("failed to create GCM: %w", err)
	}

	nonceSize := gcm.NonceSize()
	if len(encryptedData.Data) < nonceSize {
		return nil, fmt.Errorf("ciphertext too short")
	}

	nonce, ciphertext := encryptedData.Data[:nonceSize], encryptedData.Data[nonceSize:]
	plaintext, err := gcm.Open(nil, nonce, ciphertext, nil)
	if err != nil {
		return nil, fmt.Errorf("failed to decrypt: %w", err)
	}

	return plaintext, nil
}

// encryptAsymmetric encrypts data using asymmetric encryption
func (es *EncryptionService) encryptAsymmetric(data []byte, key *EncryptionKey) (*EncryptedData, error) {
	block, _ := pem.Decode(key.PublicKey)
	if block == nil {
		return nil, fmt.Errorf("failed to decode public key")
	}

	publicKey, err := x509.ParsePKCS1PublicKey(block.Bytes)
	if err != nil {
		return nil, fmt.Errorf("failed to parse public key: %w", err)
	}

	// For large data, we'll use hybrid encryption (encrypt data with AES, then encrypt AES key with RSA)
	// For simplicity, we'll encrypt the data directly with RSA (limited to key size - padding)
	maxSize := publicKey.Size() - 42 // RSA padding overhead
	if len(data) > maxSize {
		return nil, fmt.Errorf("data too large for RSA encryption (max %d bytes)", maxSize)
	}

	ciphertext, err := rsa.EncryptOAEP(sha256.New(), rand.Reader, publicKey, data, nil)
	if err != nil {
		return nil, fmt.Errorf("failed to encrypt: %w", err)
	}

	return &EncryptedData{
		ID:        generateEncryptedDataID(),
		KeyID:     key.ID,
		Algorithm: key.Algorithm,
		Data:      ciphertext,
		CreatedAt: time.Now(),
		Metadata:  make(map[string]interface{}),
	}, nil
}

// decryptAsymmetric decrypts data using asymmetric encryption
func (es *EncryptionService) decryptAsymmetric(encryptedData *EncryptedData, key *EncryptionKey) ([]byte, error) {
	block, _ := pem.Decode(key.PrivateKey)
	if block == nil {
		return nil, fmt.Errorf("failed to decode private key")
	}

	privateKey, err := x509.ParsePKCS1PrivateKey(block.Bytes)
	if err != nil {
		return nil, fmt.Errorf("failed to parse private key: %w", err)
	}

	plaintext, err := rsa.DecryptOAEP(sha256.New(), rand.Reader, privateKey, encryptedData.Data, nil)
	if err != nil {
		return nil, fmt.Errorf("failed to decrypt: %w", err)
	}

	return plaintext, nil
}

// SignData signs data using the private key
func (es *EncryptionService) SignData(data []byte, keyID string) ([]byte, error) {
	es.keysMutex.RLock()
	key, exists := es.keys[keyID]
	es.keysMutex.RUnlock()

	if !exists {
		return nil, fmt.Errorf("key not found: %s", keyID)
	}

	if key.Type != KeyTypeAsymmetric {
		return nil, fmt.Errorf("key is not asymmetric: %s", keyID)
	}

	block, _ := pem.Decode(key.PrivateKey)
	if block == nil {
		return nil, fmt.Errorf("failed to decode private key")
	}

	privateKey, err := x509.ParsePKCS1PrivateKey(block.Bytes)
	if err != nil {
		return nil, fmt.Errorf("failed to parse private key: %w", err)
	}

	hash := sha256.Sum256(data)
	signature, err := rsa.SignPKCS1v15(rand.Reader, privateKey, crypto.SHA256, hash[:])
	if err != nil {
		return nil, fmt.Errorf("failed to sign data: %w", err)
	}

	return signature, nil
}

// VerifySignature verifies a signature using the public key
func (es *EncryptionService) VerifySignature(data, signature []byte, keyID string) (bool, error) {
	es.keysMutex.RLock()
	key, exists := es.keys[keyID]
	es.keysMutex.RUnlock()

	if !exists {
		return false, fmt.Errorf("key not found: %s", keyID)
	}

	if key.Type != KeyTypeAsymmetric {
		return false, fmt.Errorf("key is not asymmetric: %s", keyID)
	}

	block, _ := pem.Decode(key.PublicKey)
	if block == nil {
		return false, fmt.Errorf("failed to decode public key")
	}

	publicKey, err := x509.ParsePKCS1PublicKey(block.Bytes)
	if err != nil {
		return false, fmt.Errorf("failed to parse public key: %w", err)
	}

	hash := sha256.Sum256(data)
	err = rsa.VerifyPKCS1v15(publicKey, crypto.SHA256, hash[:], signature)
	if err != nil {
		return false, nil
	}

	return true, nil
}

// GetKey retrieves a key by ID
func (es *EncryptionService) GetKey(keyID string) (*EncryptionKey, error) {
	es.keysMutex.RLock()
	defer es.keysMutex.RUnlock()

	key, exists := es.keys[keyID]
	if !exists {
		return nil, fmt.Errorf("key not found: %s", keyID)
	}

	return key, nil
}

// ListKeys returns all keys
func (es *EncryptionService) ListKeys() []*EncryptionKey {
	es.keysMutex.RLock()
	defer es.keysMutex.RUnlock()

	keys := make([]*EncryptionKey, 0, len(es.keys))
	for _, key := range es.keys {
		keys = append(keys, key)
	}

	return keys
}

// RotateKey rotates a key by creating a new one and marking the old one as inactive
func (es *EncryptionService) RotateKey(keyID string) (*EncryptionKey, error) {
	es.keysMutex.Lock()
	oldKey, exists := es.keys[keyID]
	if !exists {
		es.keysMutex.Unlock()
		return nil, fmt.Errorf("key not found: %s", keyID)
	}

	// Create new key with same algorithm and description
	var newKey *EncryptionKey
	var err error

	if oldKey.Type == KeyTypeSymmetric {
		newKey, err = es.GenerateSymmetricKey(oldKey.Algorithm, oldKey.Description+" (rotated)")
	} else {
		newKey, err = es.GenerateAsymmetricKeyPair(oldKey.Algorithm, oldKey.Description+" (rotated)")
	}

	if err != nil {
		es.keysMutex.Unlock()
		return nil, fmt.Errorf("failed to generate new key: %w", err)
	}

	// Mark old key as inactive
	oldKey.IsActive = false
	es.keysMutex.Unlock()

	return newKey, nil
}

// SetDefaultKey sets the default key for encryption
func (es *EncryptionService) SetDefaultKey(keyID string) error {
	es.keysMutex.RLock()
	_, exists := es.keys[keyID]
	es.keysMutex.RUnlock()

	if !exists {
		return fmt.Errorf("key not found: %s", keyID)
	}

	es.keysMutex.Lock()
	es.defaultKeyID = keyID
	es.keysMutex.Unlock()

	return nil
}

// GetDefaultKey returns the default key
func (es *EncryptionService) GetDefaultKey() (*EncryptionKey, error) {
	es.keysMutex.RLock()
	defer es.keysMutex.RUnlock()

	if es.defaultKeyID == "" {
		return nil, fmt.Errorf("no default key set")
	}

	key, exists := es.keys[es.defaultKeyID]
	if !exists {
		return nil, fmt.Errorf("default key not found: %s", es.defaultKeyID)
	}

	return key, nil
}

// generateKeyID generates a unique key ID
func generateKeyID() string {
	return fmt.Sprintf("key_%d", time.Now().UnixNano())
}

// generateEncryptedDataID generates a unique encrypted data ID
func generateEncryptedDataID() string {
	return fmt.Sprintf("enc_%d", time.Now().UnixNano())
}

// GetKeyStats returns key statistics
func (es *EncryptionService) GetKeyStats() map[string]interface{} {
	es.keysMutex.RLock()
	defer es.keysMutex.RUnlock()

	totalKeys := len(es.keys)
	activeKeys := 0
	symmetricKeys := 0
	asymmetricKeys := 0

	for _, key := range es.keys {
		if key.IsActive {
			activeKeys++
		}
		if key.Type == KeyTypeSymmetric {
			symmetricKeys++
		} else {
			asymmetricKeys++
		}
	}

	return map[string]interface{}{
		"total_keys":      totalKeys,
		"active_keys":     activeKeys,
		"symmetric_keys":  symmetricKeys,
		"asymmetric_keys": asymmetricKeys,
		"default_key_id":  es.defaultKeyID,
	}
}
