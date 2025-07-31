"""
Voice Processor

AI-powered voice input processing and transcription for the Arxos platform.
"""

import asyncio
import base64
import io
from typing import Dict, Any, Optional
import numpy as np
import librosa
import speech_recognition as sr
import structlog

logger = structlog.get_logger()


class VoiceProcessor:
    """AI-powered voice input processing and transcription"""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the voice processor"""
        self.config = config
        self.logger = structlog.get_logger(__name__)
        
        # Initialize speech recognizer
        self.recognizer = sr.Recognizer()
        
        # Supported languages
        self.supported_languages = {
            "en": "en-US",
            "es": "es-ES", 
            "fr": "fr-FR",
            "de": "de-DE",
            "it": "it-IT",
            "pt": "pt-BR",
            "ru": "ru-RU",
            "ja": "ja-JP",
            "ko": "ko-KR",
            "zh": "zh-CN"
        }
        
        self.logger.info("Voice Processor initialized")
    
    async def process_audio(
        self,
        audio_data: str,
        language: str = "en"
    ) -> Dict[str, Any]:
        """Process audio data and convert to text"""
        try:
            self.logger.info(f"Processing audio with language: {language}")
            
            # Decode base64 audio data
            audio_bytes = base64.b64decode(audio_data)
            
            # Convert to audio format
            audio = await self._bytes_to_audio(audio_bytes)
            
            # Perform transcription
            transcription = await self._transcribe_audio(audio, language)
            
            # Analyze audio characteristics
            analysis = await self._analyze_audio(audio_bytes)
            
            return {
                "success": True,
                "text": transcription["text"],
                "confidence": transcription.get("confidence", 0.0),
                "language": language,
                "analysis": analysis,
                "timestamp": asyncio.get_event_loop().time()
            }
            
        except Exception as e:
            self.logger.error(f"Error processing audio: {e}")
            return {
                "success": False,
                "error": str(e),
                "text": "",
                "confidence": 0.0,
                "language": language
            }
    
    async def _bytes_to_audio(self, audio_bytes: bytes) -> sr.AudioData:
        """Convert bytes to AudioData object"""
        try:
            # Try to load as WAV first
            audio_file = io.BytesIO(audio_bytes)
            
            # Use librosa to load and convert audio
            y, sr_rate = librosa.load(audio_file, sr=None)
            
            # Convert to 16-bit PCM
            y_int16 = (y * 32767).astype(np.int16)
            
            # Create AudioData object
            audio_data = sr.AudioData(
                y_int16.tobytes(),
                sample_rate=sr_rate,
                sample_width=2
            )
            
            return audio_data
            
        except Exception as e:
            self.logger.error(f"Error converting bytes to audio: {e}")
            raise
    
    async def _transcribe_audio(
        self,
        audio: sr.AudioData,
        language: str
    ) -> Dict[str, Any]:
        """Transcribe audio using speech recognition"""
        try:
            # Get language code
            lang_code = self.supported_languages.get(language, "en-US")
            
            # Perform transcription
            text = await asyncio.to_thread(
                self.recognizer.recognize_google,
                audio,
                language=lang_code
            )
            
            return {
                "text": text,
                "confidence": 0.8,  # Google doesn't provide confidence
                "language": language
            }
            
        except sr.UnknownValueError:
            self.logger.warning("Speech recognition could not understand audio")
            return {
                "text": "",
                "confidence": 0.0,
                "language": language,
                "error": "Could not understand audio"
            }
        except sr.RequestError as e:
            self.logger.error(f"Speech recognition service error: {e}")
            return {
                "text": "",
                "confidence": 0.0,
                "language": language,
                "error": f"Service error: {str(e)}"
            }
        except Exception as e:
            self.logger.error(f"Error transcribing audio: {e}")
            return {
                "text": "",
                "confidence": 0.0,
                "language": language,
                "error": str(e)
            }
    
    async def _analyze_audio(self, audio_bytes: bytes) -> Dict[str, Any]:
        """Analyze audio characteristics"""
        try:
            # Load audio with librosa
            audio_file = io.BytesIO(audio_bytes)
            y, sr = librosa.load(audio_file, sr=None)
            
            # Calculate audio features
            duration = librosa.get_duration(y=y, sr=sr)
            rms = np.sqrt(np.mean(y**2))
            spectral_centroids = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
            spectral_rolloff = librosa.feature.spectral_rolloff(y=y, sr=sr)[0]
            
            analysis = {
                "duration": duration,
                "sample_rate": sr,
                "rms_energy": float(rms),
                "spectral_centroid_mean": float(np.mean(spectral_centroids)),
                "spectral_rolloff_mean": float(np.mean(spectral_rolloff)),
                "zero_crossing_rate": float(librosa.feature.zero_crossing_rate(y)[0].mean()),
                "mfcc_features": librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13).tolist()
            }
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"Error analyzing audio: {e}")
            return {
                "error": str(e),
                "duration": 0.0,
                "sample_rate": 0
            }
    
    async def execute_task(self, task: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute voice-related tasks"""
        try:
            if task == "transcribe":
                return await self.process_audio(
                    parameters.get("audio_data", ""),
                    parameters.get("language", "en")
                )
            elif task == "analyze":
                audio_bytes = base64.b64decode(parameters.get("audio_data", ""))
                return {
                    "analysis": await self._analyze_audio(audio_bytes)
                }
            elif task == "detect_language":
                return await self._detect_language(parameters.get("audio_data", ""))
            else:
                return {
                    "error": f"Unknown voice task: {task}",
                    "available_tasks": ["transcribe", "analyze", "detect_language"]
                }
                
        except Exception as e:
            self.logger.error(f"Error executing voice task: {e}")
            return {"error": str(e)}
    
    async def _detect_language(self, audio_data: str) -> Dict[str, Any]:
        """Detect the language of audio input"""
        try:
            # Try multiple languages and compare confidence
            audio_bytes = base64.b64decode(audio_data)
            audio = await self._bytes_to_audio(audio_bytes)
            
            results = {}
            
            for lang_code, google_lang in self.supported_languages.items():
                try:
                    result = await self._transcribe_audio(audio, lang_code)
                    if result["text"]:
                        results[lang_code] = {
                            "text": result["text"],
                            "confidence": result.get("confidence", 0.0)
                        }
                except Exception:
                    continue
            
            # Find the best result
            if results:
                best_lang = max(results.keys(), key=lambda k: len(results[k]["text"]))
                return {
                    "detected_language": best_lang,
                    "text": results[best_lang]["text"],
                    "all_results": results
                }
            else:
                return {
                    "detected_language": "unknown",
                    "text": "",
                    "error": "Could not detect language"
                }
                
        except Exception as e:
            self.logger.error(f"Error detecting language: {e}")
            return {
                "detected_language": "unknown",
                "text": "",
                "error": str(e)
            } 