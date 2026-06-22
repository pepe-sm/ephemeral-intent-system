/**
 * Voice Narration Service
 * Uses Web Speech API for text-to-speech narration
 */

export interface VoiceNarrationOptions {
  rate?: number; // 0.1 to 10, default 1
  pitch?: number; // 0 to 2, default 1
  volume?: number; // 0 to 1, default 1
  voice?: SpeechSynthesisVoice | null;
  lang?: string; // e.g., 'en-US'
}

export class VoiceNarrationService {
  private synthesis: SpeechSynthesis;
  private currentUtterance: SpeechSynthesisUtterance | null = null;
  private isEnabled: boolean = false;
  private isPaused: boolean = false;
  private queue: string[] = [];
  private voices: SpeechSynthesisVoice[] = [];
  private options: Required<VoiceNarrationOptions>;

  constructor(options: VoiceNarrationOptions = {}) {
    this.synthesis = window.speechSynthesis;
    
    // Default options
    this.options = {
      rate: options.rate ?? 1.0,
      pitch: options.pitch ?? 1.0,
      volume: options.volume ?? 0.8,
      voice: options.voice ?? null,
      lang: options.lang ?? 'en-US',
    };

    // Load available voices
    this.loadVoices();
    
    // Handle voice list changes (some browsers load voices asynchronously)
    if (this.synthesis.onvoiceschanged !== undefined) {
      this.synthesis.onvoiceschanged = () => this.loadVoices();
    }
  }

  /**
   * Load available voices
   */
  private loadVoices(): void {
    this.voices = this.synthesis.getVoices();
    
    // Auto-select a good English voice if none selected
    if (!this.options.voice && this.voices.length > 0) {
      // Prefer Google voices or native voices
      const preferredVoice = this.voices.find(
        (voice) =>
          voice.lang.startsWith('en') &&
          (voice.name.includes('Google') || voice.name.includes('Natural'))
      );
      
      this.options.voice = preferredVoice || this.voices.find((v) => v.lang.startsWith('en')) || this.voices[0];
    }
  }

  /**
   * Get available voices
   */
  public getVoices(): SpeechSynthesisVoice[] {
    return this.voices;
  }

  /**
   * Set voice by name or index
   */
  public setVoice(voiceNameOrIndex: string | number): void {
    if (typeof voiceNameOrIndex === 'number') {
      this.options.voice = this.voices[voiceNameOrIndex] || null;
    } else {
      this.options.voice = this.voices.find((v) => v.name === voiceNameOrIndex) || null;
    }
  }

  /**
   * Enable voice narration
   */
  public enable(): void {
    this.isEnabled = true;
    console.log('Voice narration enabled');
  }

  /**
   * Disable voice narration
   */
  public disable(): void {
    this.isEnabled = false;
    this.stop();
    console.log('Voice narration disabled');
  }

  /**
   * Toggle voice narration
   */
  public toggle(): boolean {
    if (this.isEnabled) {
      this.disable();
    } else {
      this.enable();
    }
    return this.isEnabled;
  }

  /**
   * Check if narration is enabled
   */
  public isNarrationEnabled(): boolean {
    return this.isEnabled;
  }

  /**
   * Speak text
   */
  public speak(text: string, options?: Partial<VoiceNarrationOptions>): Promise<void> {
    if (!this.isEnabled) {
      return Promise.resolve();
    }

    return new Promise((resolve, reject) => {
      // Clean text for better speech
      const cleanText = this.cleanTextForSpeech(text);
      
      if (!cleanText.trim()) {
        resolve();
        return;
      }

      const utterance = new SpeechSynthesisUtterance(cleanText);
      
      // Apply options
      utterance.rate = options?.rate ?? this.options.rate;
      utterance.pitch = options?.pitch ?? this.options.pitch;
      utterance.volume = options?.volume ?? this.options.volume;
      utterance.lang = options?.lang ?? this.options.lang;
      
      if (options?.voice || this.options.voice) {
        utterance.voice = options?.voice ?? this.options.voice;
      }

      // Event handlers
      utterance.onend = () => {
        this.currentUtterance = null;
        resolve();
      };

      utterance.onerror = (event) => {
        console.error('Speech synthesis error:', event);
        this.currentUtterance = null;
        reject(event);
      };

      // Cancel current speech and speak new text
      this.synthesis.cancel();
      this.currentUtterance = utterance;
      this.synthesis.speak(utterance);
    });
  }

  /**
   * Speak text with adjustable rate based on cognitive load
   */
  public speakAdaptive(
    text: string,
    cognitiveLoad: 'low' | 'medium' | 'high' = 'medium'
  ): Promise<void> {
    // Adjust speech rate based on cognitive load
    const rateMap = {
      low: 1.2, // Faster for low cognitive load
      medium: 1.0, // Normal speed
      high: 0.8, // Slower for high cognitive load
    };

    return this.speak(text, { rate: rateMap[cognitiveLoad] });
  }

  /**
   * Pause current narration
   */
  public pause(): void {
    if (this.synthesis.speaking && !this.synthesis.paused) {
      this.synthesis.pause();
      this.isPaused = true;
    }
  }

  /**
   * Resume paused narration
   */
  public resume(): void {
    if (this.synthesis.paused) {
      this.synthesis.resume();
      this.isPaused = false;
    }
  }

  /**
   * Stop current narration
   */
  public stop(): void {
    this.synthesis.cancel();
    this.currentUtterance = null;
    this.isPaused = false;
    this.queue = [];
  }

  /**
   * Check if currently speaking
   */
  public isSpeaking(): boolean {
    return this.synthesis.speaking;
  }

  /**
   * Check if paused
   */
  public isPausedState(): boolean {
    return this.isPaused;
  }

  /**
   * Update narration options
   */
  public updateOptions(options: Partial<VoiceNarrationOptions>): void {
    this.options = {
      ...this.options,
      ...options,
    };
  }

  /**
   * Clean text for better speech synthesis
   */
  private cleanTextForSpeech(text: string): string {
    return text
      // Remove markdown formatting
      .replace(/[#*_`]/g, '')
      // Remove code blocks
      .replace(/```[\s\S]*?```/g, '')
      // Remove inline code
      .replace(/`[^`]+`/g, '')
      // Remove URLs
      .replace(/https?:\/\/[^\s]+/g, 'link')
      // Remove HTML tags
      .replace(/<[^>]+>/g, '')
      // Replace bullet points
      .replace(/^[•\-*]\s+/gm, '')
      // Replace multiple newlines with period
      .replace(/\n{2,}/g, '. ')
      // Replace single newlines with space
      .replace(/\n/g, ' ')
      // Remove extra spaces
      .replace(/\s+/g, ' ')
      // Trim
      .trim();
  }

  /**
   * Speak module content with pauses
   */
  public async speakModule(
    title: string,
    content: string,
    cognitiveLoad: 'low' | 'medium' | 'high' = 'medium'
  ): Promise<void> {
    if (!this.isEnabled) return;

    try {
      // Speak title
      await this.speakAdaptive(`${title}.`, cognitiveLoad);
      
      // Small pause
      await this.delay(500);
      
      // Split content into sentences for better pacing
      const sentences = this.splitIntoSentences(content);
      
      for (const sentence of sentences) {
        if (!this.isEnabled) break;
        
        await this.speakAdaptive(sentence, cognitiveLoad);
        
        // Pause between sentences
        await this.delay(300);
      }
    } catch (error) {
      console.error('Error speaking module:', error);
    }
  }

  /**
   * Split text into sentences
   */
  private splitIntoSentences(text: string): string[] {
    const cleaned = this.cleanTextForSpeech(text);
    
    // Split on sentence boundaries
    return cleaned
      .split(/[.!?]+/)
      .map((s) => s.trim())
      .filter((s) => s.length > 0);
  }

  /**
   * Delay helper
   */
  private delay(ms: number): Promise<void> {
    return new Promise((resolve) => setTimeout(resolve, ms));
  }

  /**
   * Get current speech rate
   */
  public getRate(): number {
    return this.options.rate;
  }

  /**
   * Set speech rate
   */
  public setRate(rate: number): void {
    this.options.rate = Math.max(0.1, Math.min(10, rate));
  }

  /**
   * Get current pitch
   */
  public getPitch(): number {
    return this.options.pitch;
  }

  /**
   * Set pitch
   */
  public setPitch(pitch: number): void {
    this.options.pitch = Math.max(0, Math.min(2, pitch));
  }

  /**
   * Get current volume
   */
  public getVolume(): number {
    return this.options.volume;
  }

  /**
   * Set volume
   */
  public setVolume(volume: number): void {
    this.options.volume = Math.max(0, Math.min(1, volume));
  }
}

// Create singleton instance
export const voiceNarration = new VoiceNarrationService();

// Export for use in components
export default voiceNarration;

// Made with Bob
