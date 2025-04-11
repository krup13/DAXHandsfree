import numpy as np
from scipy import signal


class NoiseSuppressionModule:
    def __init__(self):
        """
        Initialize noise suppression module with basic filtering techniques
        suitable for in-vehicle environments
        """
        self.is_initialized = True
        print("Noise Suppression Module initialized")

    def process_audio(self, audio_data, sample_rate=16000):
        """
        Process raw audio input to reduce noise
        - Handles traffic noise
        - Filters engine sounds
        - Reduces impact of rain/wind noise

        Parameters:
        - audio_data: numpy array of audio samples
        - sample_rate: sampling rate of the audio (default: 16kHz)

        Returns:
        - Processed audio with reduced noise
        """
        if audio_data is None or len(audio_data) == 0:
            return audio_data

        try:
            # Convert to numpy array if not already
            audio_np = np.array(audio_data, dtype=float)

            # 1. Apply bandpass filter to focus on speech frequencies (300-3000 Hz)
            b, a = signal.butter(5, [300, 3000], 'bandpass', fs=sample_rate)
            filtered = signal.lfilter(b, a, audio_np)

            # 2. Simple noise gate to reduce background noise
            # Calculate RMS of the signal
            rms = np.sqrt(np.mean(filtered ** 2))
            threshold = 0.1 * rms  # Adjust threshold as needed

            # Apply noise gate
            noise_gate = np.where(np.abs(filtered) < threshold, 0, filtered)

            print(f"Noise suppression applied - Input shape: {audio_np.shape}")
            return noise_gate

        except Exception as e:
            print(f"Error in noise suppression: {str(e)}")
            # Return original audio if processing fails
            return audio_data