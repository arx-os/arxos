"""
Advanced AI Service for SVGX Engine

Provides advanced AI capabilities including:
- Machine learning model training and inference
- Predictive analytics for design optimization
- Automated design generation and optimization
- Pattern recognition and learning
- Quality assessment and improvement suggestions
- Performance prediction and optimization

CTO Directives:
- Enterprise-grade AI/ML implementation
- Performance monitoring and optimization
- Scalable machine learning pipeline
"""

import asyncio
import json
import logging
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
from typing import Dict, List, Optional, Tuple, Any, Union
from uuid import uuid4
import pickle
import joblib
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
import warnings
warnings.filterwarnings('ignore')

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AIModelType(Enum):
    """AI Model Types"""
    SYMBOL_GENERATION = "symbol_generation"
    DESIGN_OPTIMIZATION = "design_optimization"
    QUALITY_ASSESSMENT = "quality_assessment"
    PERFORMANCE_PREDICTION = "performance_prediction"
    PATTERN_RECOGNITION = "pattern_recognition"
    AUTOMATED_DESIGN = "automated_design"

class LearningType(Enum):
    """Learning Types"""
    SUPERVISED = "supervised"
    UNSUPERVISED = "unsupervised"
    REINFORCEMENT = "reinforcement"
    TRANSFER = "transfer"

class OptimizationType(Enum):
    """Optimization Types"""
    STRUCTURAL = "structural"
    THERMAL = "thermal"
    ELECTRICAL = "electrical"
    COST = "cost"
    PERFORMANCE = "performance"
    EFFICIENCY = "efficiency"

@dataclass
class AIModelConfig:
    """AI Model Configuration"""
    model_type: AIModelType
    learning_type: LearningType
    input_features: List[str]
    output_features: List[str]
    hyperparameters: Dict[str, Any]
    training_data_size: int
    validation_split: float = 0.2
    test_split: float = 0.1
    epochs: int = 100
    batch_size: int = 32
    learning_rate: float = 0.001
    early_stopping_patience: int = 10

@dataclass
class TrainingMetrics:
    """Training Metrics"""
    model_id: str
    training_loss: float
    validation_loss: float
    test_loss: float
    r2_score: float
    mse: float
    mae: float
    training_time: float
    inference_time: float
    accuracy: float
    precision: float
    recall: float
    f1_score: float

@dataclass
class PredictionResult:
    """Prediction Result"""
    prediction_id: str
    model_id: str
    input_data: Dict[str, Any]
    predictions: Dict[str, Any]
    confidence: float
    uncertainty: float
    timestamp: datetime
    metadata: Dict[str, Any]

@dataclass
class OptimizationRequest:
    """Optimization Request"""
    optimization_id: str
    optimization_type: OptimizationType
    target_metrics: Dict[str, float]
    constraints: Dict[str, Any]
    design_space: Dict[str, List[float]]
    max_iterations: int = 100
    tolerance: float = 1e-6
    population_size: int = 50

@dataclass
class OptimizationResult:
    """Optimization Result"""
    optimization_id: str
    best_solution: Dict[str, Any]
    best_fitness: float
    convergence_history: List[float]
    iterations: int
    computation_time: float
    pareto_front: List[Dict[str, Any]]
    sensitivity_analysis: Dict[str, float]

class AdvancedAIService:
    """Advanced AI Service for SVGX Engine"""
    
    def __init__(self):
        self.models: Dict[str, Any] = {}
        self.scalers: Dict[str, StandardScaler] = {}
        self.model_configs: Dict[str, AIModelConfig] = {}
        self.training_history: Dict[str, List[TrainingMetrics]] = {}
        self.prediction_cache: Dict[str, PredictionResult] = {}
        self.optimization_results: Dict[str, OptimizationResult] = {}
        
        # Initialize TensorFlow session
        self.session = tf.compat.v1.Session()
        tf.compat.v1.keras.backend.set_session(self.session)
        
        logger.info("Advanced AI Service initialized")

    async def create_model(self, config: AIModelConfig) -> str:
        """Create a new AI model"""
        try:
            model_id = str(uuid4())
            
            if config.model_type == AIModelType.SYMBOL_GENERATION:
                model = self._create_symbol_generation_model(config)
            elif config.model_type == AIModelType.DESIGN_OPTIMIZATION:
                model = self._create_design_optimization_model(config)
            elif config.model_type == AIModelType.QUALITY_ASSESSMENT:
                model = self._create_quality_assessment_model(config)
            elif config.model_type == AIModelType.PERFORMANCE_PREDICTION:
                model = self._create_performance_prediction_model(config)
            elif config.model_type == AIModelType.PATTERN_RECOGNITION:
                model = self._create_pattern_recognition_model(config)
            elif config.model_type == AIModelType.AUTOMATED_DESIGN:
                model = self._create_automated_design_model(config)
            else:
                raise ValueError(f"Unknown model type: {config.model_type}")
            
            self.models[model_id] = model
            self.model_configs[model_id] = config
            self.scalers[model_id] = StandardScaler()
            self.training_history[model_id] = []
            
            logger.info(f"Created AI model: {model_id} ({config.model_type.value})")
            return model_id
            
        except Exception as e:
            logger.error(f"Error creating model: {e}")
            raise

    def _create_symbol_generation_model(self, config: AIModelConfig) -> keras.Model:
        """Create symbol generation model using GAN architecture"""
        generator = keras.Sequential([
            layers.Dense(128, input_shape=(config.input_features,)),
            layers.LeakyReLU(0.2),
            layers.Dropout(0.3),
            layers.Dense(256),
            layers.LeakyReLU(0.2),
            layers.Dropout(0.3),
            layers.Dense(512),
            layers.LeakyReLU(0.2),
            layers.Dropout(0.3),
            layers.Dense(len(config.output_features), activation='tanh')
        ])
        
        discriminator = keras.Sequential([
            layers.Dense(512, input_shape=(len(config.output_features),)),
            layers.LeakyReLU(0.2),
            layers.Dropout(0.3),
            layers.Dense(256),
            layers.LeakyReLU(0.2),
            layers.Dropout(0.3),
            layers.Dense(128),
            layers.LeakyReLU(0.2),
            layers.Dropout(0.3),
            layers.Dense(1, activation='sigmoid')
        ])
        
        return {'generator': generator, 'discriminator': discriminator}

    def _create_design_optimization_model(self, config: AIModelConfig) -> keras.Model:
        """Create design optimization model using deep neural network"""
        model = keras.Sequential([
            layers.Dense(256, input_shape=(len(config.input_features),)),
            layers.BatchNormalization(),
            layers.ReLU(),
            layers.Dropout(0.3),
            layers.Dense(512),
            layers.BatchNormalization(),
            layers.ReLU(),
            layers.Dropout(0.3),
            layers.Dense(256),
            layers.BatchNormalization(),
            layers.ReLU(),
            layers.Dropout(0.3),
            layers.Dense(128),
            layers.BatchNormalization(),
            layers.ReLU(),
            layers.Dropout(0.3),
            layers.Dense(len(config.output_features))
        ])
        
        model.compile(
            optimizer=keras.optimizers.Adam(learning_rate=config.learning_rate),
            loss='mse',
            metrics=['mae', 'mape']
        )
        
        return model

    def _create_quality_assessment_model(self, config: AIModelConfig) -> keras.Model:
        """Create quality assessment model using CNN"""
        model = keras.Sequential([
            layers.Conv1D(64, 3, activation='relu', input_shape=(len(config.input_features), 1)),
            layers.MaxPooling1D(2),
            layers.Conv1D(128, 3, activation='relu'),
            layers.MaxPooling1D(2),
            layers.Conv1D(256, 3, activation='relu'),
            layers.GlobalAveragePooling1D(),
            layers.Dense(128, activation='relu'),
            layers.Dropout(0.5),
            layers.Dense(64, activation='relu'),
            layers.Dropout(0.3),
            layers.Dense(len(config.output_features), activation='softmax')
        ])
        
        model.compile(
            optimizer=keras.optimizers.Adam(learning_rate=config.learning_rate),
            loss='categorical_crossentropy',
            metrics=['accuracy', 'precision', 'recall']
        )
        
        return model

    def _create_performance_prediction_model(self, config: AIModelConfig) -> keras.Model:
        """Create performance prediction model using LSTM"""
        model = keras.Sequential([
            layers.LSTM(128, return_sequences=True, input_shape=(None, len(config.input_features))),
            layers.Dropout(0.2),
            layers.LSTM(64, return_sequences=False),
            layers.Dropout(0.2),
            layers.Dense(32, activation='relu'),
            layers.Dropout(0.2),
            layers.Dense(len(config.output_features))
        ])
        
        model.compile(
            optimizer=keras.optimizers.Adam(learning_rate=config.learning_rate),
            loss='mse',
            metrics=['mae']
        )
        
        return model

    def _create_pattern_recognition_model(self, config: AIModelConfig) -> keras.Model:
        """Create pattern recognition model using autoencoder"""
        # Encoder
        encoder = keras.Sequential([
            layers.Dense(256, activation='relu', input_shape=(len(config.input_features),)),
            layers.Dense(128, activation='relu'),
            layers.Dense(64, activation='relu'),
            layers.Dense(32, activation='relu')
        ])
        
        # Decoder
        decoder = keras.Sequential([
            layers.Dense(64, activation='relu', input_shape=(32,)),
            layers.Dense(128, activation='relu'),
            layers.Dense(256, activation='relu'),
            layers.Dense(len(config.output_features), activation='sigmoid')
        ])
        
        # Autoencoder
        autoencoder = keras.Sequential([encoder, decoder])
        autoencoder.compile(
            optimizer=keras.optimizers.Adam(learning_rate=config.learning_rate),
            loss='binary_crossentropy',
            metrics=['accuracy']
        )
        
        return {'autoencoder': autoencoder, 'encoder': encoder, 'decoder': decoder}

    def _create_automated_design_model(self, config: AIModelConfig) -> keras.Model:
        """Create automated design model using transformer architecture"""
        model = keras.Sequential([
            layers.Dense(512, input_shape=(len(config.input_features),)),
            layers.MultiHeadAttention(num_heads=8, key_dim=64),
            layers.LayerNormalization(),
            layers.Dense(256, activation='relu'),
            layers.Dropout(0.3),
            layers.Dense(128, activation='relu'),
            layers.Dropout(0.3),
            layers.Dense(len(config.output_features))
        ])
        
        model.compile(
            optimizer=keras.optimizers.Adam(learning_rate=config.learning_rate),
            loss='mse',
            metrics=['mae']
        )
        
        return model

    async def train_model(self, model_id: str, training_data: List[Dict[str, Any]], 
                         validation_data: Optional[List[Dict[str, Any]]] = None) -> TrainingMetrics:
        """Train an AI model"""
        try:
            if model_id not in self.models:
                raise ValueError(f"Model {model_id} not found")
            
            config = self.model_configs[model_id]
            model = self.models[model_id]
            
            # Prepare data
            X_train, y_train = self._prepare_training_data(training_data, config)
            X_val, y_val = self._prepare_training_data(validation_data or [], config)
            
            # Scale features
            X_train_scaled = self.scalers[model_id].fit_transform(X_train)
            X_val_scaled = self.scalers[model_id].transform(X_val) if len(X_val) > 0 else X_train_scaled
            
            # Training callbacks
            callbacks = [
                keras.callbacks.EarlyStopping(
                    patience=config.early_stopping_patience,
                    restore_best_weights=True
                ),
                keras.callbacks.ReduceLROnPlateau(
                    factor=0.5,
                    patience=5,
                    min_lr=1e-7
                )
            ]
            
            # Train model
            start_time = datetime.now()
            
            if isinstance(model, dict) and 'generator' in model:
                # GAN training
                history = await self._train_gan(model, X_train_scaled, y_train, config)
            else:
                # Standard training
                history = model.fit(
                    X_train_scaled, y_train,
                    validation_data=(X_val_scaled, y_val) if len(X_val) > 0 else None,
                    epochs=config.epochs,
                    batch_size=config.batch_size,
                    callbacks=callbacks,
                    verbose=1
                )
            
            training_time = (datetime.now() - start_time).total_seconds()
            
            # Evaluate model
            y_pred = model.predict(X_val_scaled) if len(X_val) > 0 else model.predict(X_train_scaled)
            y_true = y_val if len(y_val) > 0 else y_train
            
            # Calculate metrics
            mse = mean_squared_error(y_true, y_pred)
            mae = np.mean(np.abs(y_true - y_pred))
            r2 = r2_score(y_true, y_pred)
            
            # Calculate additional metrics for classification
            accuracy = precision = recall = f1 = 0.0
            if config.model_type == AIModelType.QUALITY_ASSESSMENT:
                y_pred_classes = np.argmax(y_pred, axis=1)
                y_true_classes = np.argmax(y_true, axis=1)
                accuracy = np.mean(y_pred_classes == y_true_classes)
                precision = np.mean(y_pred_classes[y_pred_classes == y_true_classes])
                recall = np.mean(y_true_classes[y_pred_classes == y_true_classes])
                f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
            
            # Create training metrics
            metrics = TrainingMetrics(
                model_id=model_id,
                training_loss=float(history.history['loss'][-1]),
                validation_loss=float(history.history['val_loss'][-1]) if 'val_loss' in history.history else 0.0,
                test_loss=float(mse),
                r2_score=float(r2),
                mse=float(mse),
                mae=float(mae),
                training_time=training_time,
                inference_time=0.0,  # Will be measured during inference
                accuracy=accuracy,
                precision=precision,
                recall=recall,
                f1_score=f1
            )
            
            self.training_history[model_id].append(metrics)
            
            logger.info(f"Model {model_id} trained successfully. R²: {r2:.4f}, MSE: {mse:.4f}")
            return metrics
            
        except Exception as e:
            logger.error(f"Error training model {model_id}: {e}")
            raise

    async def _train_gan(self, model: Dict[str, keras.Model], X_train: np.ndarray, 
                         y_train: np.ndarray, config: AIModelConfig) -> keras.callbacks.History:
        """Train GAN model"""
        generator = model['generator']
        discriminator = model['discriminator']
        
        # Compile discriminator
        discriminator.compile(
            optimizer=keras.optimizers.Adam(learning_rate=config.learning_rate),
            loss='binary_crossentropy',
            metrics=['accuracy']
        )
        
        # Create GAN
        gan_input = keras.Input(shape=(len(config.input_features),))
        gan_output = discriminator(generator(gan_input))
        gan = keras.Model(gan_input, gan_output)
        gan.compile(
            optimizer=keras.optimizers.Adam(learning_rate=config.learning_rate),
            loss='binary_crossentropy'
        )
        
        # Training loop
        batch_size = config.batch_size
        epochs = config.epochs
        
        for epoch in range(epochs):
            # Train discriminator
            idx = np.random.randint(0, X_train.shape[0], batch_size)
            real_samples = y_train[idx]
            noise = np.random.normal(0, 1, (batch_size, len(config.input_features)))
            generated_samples = generator.predict(noise)
            
            d_loss_real = discriminator.train_on_batch(real_samples, np.ones((batch_size, 1)))
            d_loss_fake = discriminator.train_on_batch(generated_samples, np.zeros((batch_size, 1)))
            d_loss = 0.5 * np.add(d_loss_real, d_loss_fake)
            
            # Train generator
            noise = np.random.normal(0, 1, (batch_size, len(config.input_features)))
            g_loss = gan.train_on_batch(noise, np.ones((batch_size, 1)))
            
            if epoch % 10 == 0:
                logger.info(f"Epoch {epoch}: D Loss: {d_loss[0]:.4f}, G Loss: {g_loss:.4f}")
        
        return keras.callbacks.History()

    def _prepare_training_data(self, data: List[Dict[str, Any]], config: AIModelConfig) -> Tuple[np.ndarray, np.ndarray]:
        """Prepare training data"""
        if not data:
            return np.array([]), np.array([])
        
        X = []
        y = []
        
        for item in data:
            # Extract input features
            x_row = []
            for feature in config.input_features:
                x_row.append(item.get(feature, 0.0))
            X.append(x_row)
            
            # Extract output features
            y_row = []
            for feature in config.output_features:
                y_row.append(item.get(feature, 0.0))
            y.append(y_row)
        
        return np.array(X), np.array(y)

    async def predict(self, model_id: str, input_data: Dict[str, Any]) -> PredictionResult:
        """Make predictions using trained model"""
        try:
            if model_id not in self.models:
                raise ValueError(f"Model {model_id} not found")
            
            model = self.models[model_id]
            config = self.model_configs[model_id]
            
            # Prepare input data
            X = []
            for feature in config.input_features:
                X.append(input_data.get(feature, 0.0))
            X = np.array([X])
            
            # Scale input
            X_scaled = self.scalers[model_id].transform(X)
            
            # Make prediction
            start_time = datetime.now()
            
            if isinstance(model, dict) and 'generator' in model:
                # GAN prediction
                predictions = model['generator'].predict(X_scaled)
            elif isinstance(model, dict) and 'autoencoder' in model:
                # Autoencoder prediction
                encoded = model['encoder'].predict(X_scaled)
                predictions = model['decoder'].predict(encoded)
            else:
                # Standard model prediction
                predictions = model.predict(X_scaled)
            
            inference_time = (datetime.now() - start_time).total_seconds()
            
            # Format predictions
            prediction_dict = {}
            for i, feature in enumerate(config.output_features):
                prediction_dict[feature] = float(predictions[0][i])
            
            # Calculate confidence and uncertainty
            confidence = float(np.mean(predictions))
            uncertainty = float(np.std(predictions))
            
            # Create prediction result
            result = PredictionResult(
                prediction_id=str(uuid4()),
                model_id=model_id,
                input_data=input_data,
                predictions=prediction_dict,
                confidence=confidence,
                uncertainty=uncertainty,
                timestamp=datetime.now(),
                metadata={'inference_time': inference_time}
            )
            
            # Cache prediction
            self.prediction_cache[result.prediction_id] = result
            
            logger.info(f"Prediction completed for model {model_id}. Confidence: {confidence:.4f}")
            return result
            
        except Exception as e:
            logger.error(f"Error making prediction with model {model_id}: {e}")
            raise

    async def optimize_design(self, request: OptimizationRequest) -> OptimizationResult:
        """Optimize design using AI models"""
        try:
            start_time = datetime.now()
            
            # Initialize optimization
            best_solution = None
            best_fitness = float('inf')
            convergence_history = []
            pareto_front = []
            
            # Genetic Algorithm optimization
            population = self._initialize_population(request.design_space, request.population_size)
            
            for iteration in range(request.max_iterations):
                # Evaluate population
                fitness_scores = []
                for individual in population:
                    fitness = self._evaluate_fitness(individual, request.target_metrics, request.constraints)
                    fitness_scores.append(fitness)
                
                # Find best solution
                best_idx = np.argmin(fitness_scores)
                if fitness_scores[best_idx] < best_fitness:
                    best_fitness = fitness_scores[best_idx]
                    best_solution = population[best_idx].copy()
                
                convergence_history.append(best_fitness)
                
                # Check convergence
                if len(convergence_history) > 10:
                    recent_improvement = abs(convergence_history[-1] - convergence_history[-10])
                    if recent_improvement < request.tolerance:
                        break
                
                # Generate new population
                population = self._evolve_population(population, fitness_scores)
                
                # Update Pareto front
                pareto_front = self._update_pareto_front(population, fitness_scores)
            
            computation_time = (datetime.now() - start_time).total_seconds()
            
            # Perform sensitivity analysis
            sensitivity = self._perform_sensitivity_analysis(best_solution, request)
            
            result = OptimizationResult(
                optimization_id=request.optimization_id,
                best_solution=best_solution,
                best_fitness=best_fitness,
                convergence_history=convergence_history,
                iterations=len(convergence_history),
                computation_time=computation_time,
                pareto_front=pareto_front,
                sensitivity_analysis=sensitivity
            )
            
            self.optimization_results[request.optimization_id] = result
            
            logger.info(f"Optimization completed: {request.optimization_id}. Best fitness: {best_fitness:.6f}")
            return result
            
        except Exception as e:
            logger.error(f"Error in design optimization: {e}")
            raise

    def _initialize_population(self, design_space: Dict[str, List[float]], population_size: int) -> List[Dict[str, float]]:
        """Initialize population for genetic algorithm"""
        population = []
        for _ in range(population_size):
            individual = {}
            for param, bounds in design_space.items():
                individual[param] = np.random.uniform(bounds[0], bounds[1])
            population.append(individual)
        return population

    def _evaluate_fitness(self, individual: Dict[str, float], target_metrics: Dict[str, float], 
                         constraints: Dict[str, Any]) -> float:
        """Evaluate fitness of an individual"""
        # This is a simplified fitness function
        # In practice, this would call the appropriate AI models for prediction
        fitness = 0.0
        
        # Calculate deviation from target metrics
        for metric, target in target_metrics.items():
            if metric in individual:
                deviation = abs(individual[metric] - target)
                fitness += deviation
        
        # Apply constraints
        for constraint, value in constraints.items():
            if constraint in individual:
                if individual[constraint] > value:
                    fitness += 1000  # Penalty for constraint violation
        
        return fitness

    def _evolve_population(self, population: List[Dict[str, float]], 
                          fitness_scores: List[float]) -> List[Dict[str, float]]:
        """Evolve population using genetic operators"""
        new_population = []
        
        # Elitism: keep best individuals
        elite_size = len(population) // 4
        elite_indices = np.argsort(fitness_scores)[:elite_size]
        for idx in elite_indices:
            new_population.append(population[idx].copy())
        
        # Generate rest of population through crossover and mutation
        while len(new_population) < len(population):
            # Tournament selection
            parent1 = self._tournament_selection(population, fitness_scores)
            parent2 = self._tournament_selection(population, fitness_scores)
            
            # Crossover
            child = self._crossover(parent1, parent2)
            
            # Mutation
            child = self._mutate(child)
            
            new_population.append(child)
        
        return new_population

    def _tournament_selection(self, population: List[Dict[str, float]], 
                             fitness_scores: List[float]) -> Dict[str, float]:
        """Tournament selection"""
        tournament_size = 3
        tournament_indices = np.random.choice(len(population), tournament_size, replace=False)
        tournament_fitness = [fitness_scores[i] for i in tournament_indices]
        winner_idx = tournament_indices[np.argmin(tournament_fitness)]
        return population[winner_idx].copy()

    def _crossover(self, parent1: Dict[str, float], parent2: Dict[str, float]) -> Dict[str, float]:
        """Crossover operation"""
        child = {}
        for param in parent1.keys():
            if np.random.random() < 0.5:
                child[param] = parent1[param]
            else:
                child[param] = parent2[param]
        return child

    def _mutate(self, individual: Dict[str, float]) -> Dict[str, float]:
        """Mutation operation"""
        mutation_rate = 0.1
        for param in individual.keys():
            if np.random.random() < mutation_rate:
                individual[param] += np.random.normal(0, 0.1)
        return individual

    def _update_pareto_front(self, population: List[Dict[str, float]], 
                            fitness_scores: List[float]) -> List[Dict[str, Any]]:
        """Update Pareto front"""
        pareto_front = []
        for i, individual in enumerate(population):
            dominated = False
            for j, other in enumerate(population):
                if i != j and fitness_scores[j] < fitness_scores[i]:
                    dominated = True
                    break
            if not dominated:
                pareto_front.append({
                    'solution': individual,
                    'fitness': fitness_scores[i]
                })
        return pareto_front

    def _perform_sensitivity_analysis(self, solution: Dict[str, float], 
                                    request: OptimizationRequest) -> Dict[str, float]:
        """Perform sensitivity analysis"""
        sensitivity = {}
        base_fitness = self._evaluate_fitness(solution, request.target_metrics, request.constraints)
        
        for param in solution.keys():
            perturbed_solution = solution.copy()
            perturbed_solution[param] *= 1.1  # 10% increase
            perturbed_fitness = self._evaluate_fitness(perturbed_solution, request.target_metrics, request.constraints)
            sensitivity[param] = abs(perturbed_fitness - base_fitness) / base_fitness
        
        return sensitivity

    async def get_model_info(self, model_id: str) -> Dict[str, Any]:
        """Get model information"""
        if model_id not in self.models:
            raise ValueError(f"Model {model_id} not found")
        
        config = self.model_configs[model_id]
        training_history = self.training_history.get(model_id, [])
        
        return {
            'model_id': model_id,
            'model_type': config.model_type.value,
            'learning_type': config.learning_type.value,
            'input_features': config.input_features,
            'output_features': config.output_features,
            'training_history': [asdict(metrics) for metrics in training_history],
            'model_size': self._get_model_size(model_id),
            'last_trained': training_history[-1].timestamp if training_history else None
        }

    def _get_model_size(self, model_id: str) -> int:
        """Get model size in bytes"""
        model = self.models[model_id]
        if isinstance(model, dict):
            total_size = 0
            for submodel in model.values():
                total_size += submodel.count_params() * 4  # 4 bytes per parameter
            return total_size
        else:
            return model.count_params() * 4

    async def delete_model(self, model_id: str) -> bool:
        """Delete a model"""
        try:
            if model_id in self.models:
                del self.models[model_id]
            if model_id in self.scalers:
                del self.scalers[model_id]
            if model_id in self.model_configs:
                del self.model_configs[model_id]
            if model_id in self.training_history:
                del self.training_history[model_id]
            
            logger.info(f"Model {model_id} deleted successfully")
            return True
        except Exception as e:
            logger.error(f"Error deleting model {model_id}: {e}")
            return False

    async def export_model(self, model_id: str, filepath: str) -> bool:
        """Export model to file"""
        try:
            if model_id not in self.models:
                raise ValueError(f"Model {model_id} not found")
            
            model_data = {
                'model': self.models[model_id],
                'scaler': self.scalers[model_id],
                'config': asdict(self.model_configs[model_id]),
                'training_history': [asdict(metrics) for metrics in self.training_history[model_id]]
            }
            
            with open(filepath, 'wb') as f:
                pickle.dump(model_data, f)
            
            logger.info(f"Model {model_id} exported to {filepath}")
            return True
        except Exception as e:
            logger.error(f"Error exporting model {model_id}: {e}")
            return False

    async def import_model(self, filepath: str) -> str:
        """Import model from file"""
        try:
            with open(filepath, 'rb') as f:
                model_data = pickle.load(f)
            
            model_id = str(uuid4())
            self.models[model_id] = model_data['model']
            self.scalers[model_id] = model_data['scaler']
            self.model_configs[model_id] = AIModelConfig(**model_data['config'])
            self.training_history[model_id] = [TrainingMetrics(**metrics) for metrics in model_data['training_history']]
            
            logger.info(f"Model imported successfully as {model_id}")
            return model_id
        except Exception as e:
            logger.error(f"Error importing model: {e}")
            raise

    async def get_ai_analytics(self) -> Dict[str, Any]:
        """Get AI analytics"""
        analytics = {
            'total_models': len(self.models),
            'model_types': {},
            'total_predictions': len(self.prediction_cache),
            'total_optimizations': len(self.optimization_results),
            'average_training_time': 0.0,
            'average_inference_time': 0.0,
            'model_performance': {}
        }
        
        # Calculate model type distribution
        for config in self.model_configs.values():
            model_type = config.model_type.value
            analytics['model_types'][model_type] = analytics['model_types'].get(model_type, 0) + 1
        
        # Calculate average times
        total_training_time = 0.0
        total_inference_time = 0.0
        total_metrics = 0
        
        for history in self.training_history.values():
            for metrics in history:
                total_training_time += metrics.training_time
                total_inference_time += metrics.inference_time
                total_metrics += 1
        
        if total_metrics > 0:
            analytics['average_training_time'] = total_training_time / total_metrics
            analytics['average_inference_time'] = total_inference_time / total_metrics
        
        # Calculate model performance
        for model_id, history in self.training_history.items():
            if history:
                latest_metrics = history[-1]
                analytics['model_performance'][model_id] = {
                    'r2_score': latest_metrics.r2_score,
                    'mse': latest_metrics.mse,
                    'accuracy': latest_metrics.accuracy
                }
        
        return analytics

    async def cleanup_old_predictions(self, max_age_hours: int = 24) -> int:
        """Clean up old predictions"""
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        old_predictions = [
            pred_id for pred_id, result in self.prediction_cache.items()
            if result.timestamp < cutoff_time
        ]
        
        for pred_id in old_predictions:
            del self.prediction_cache[pred_id]
        
        logger.info(f"Cleaned up {len(old_predictions)} old predictions")
        return len(old_predictions)

# Global instance
advanced_ai_service = AdvancedAIService() 