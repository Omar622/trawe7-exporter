const ffmpeg = require('fluent-ffmpeg');
const { spawn } = require('child_process');
const fs = require('fs');

class AudioAnalyzer {
    constructor() {
        // Configuration for analysis parameters
        this.config = {
            silenceThreshold: -10.0,        // dB - threshold for silence detection
            minimumSilenceDuration: 3.0,  // seconds - minimum silence duration to detect
            minimumSpeechDuration: 10.0,   // seconds - minimum speech segment to retain
            speechPadding: 0.5,           // seconds - padding around speech segments
        };
    }

    /**
     * Analyze audio file and determine which segments should be cut
     * @param {string} audioFilePath - Path to the audio file to analyze
     * @returns {Promise<Array<[number, number]>>} Array of [start, end] time ranges to cut (in seconds)
     */
    async analyzeAndGetCutRanges(audioFilePath) {
        try {
            console.log(`Analyzing audio file: ${audioFilePath}`);
            console.log(`Silence threshold: ${this.config.silenceThreshold}dB`);
            console.log(`Minimum silence duration: ${this.config.minimumSilenceDuration}s`);
            console.log(`Minimum speech duration: ${this.config.minimumSpeechDuration}s`);
            
            // Get total audio duration
            const totalDuration = await this.getAudioDuration(audioFilePath);
            console.log(`Total audio duration: ${totalDuration.toFixed(2)}s`);
            
            // Detect silence periods
            const silencePeriods = await this.detectSilence(
                audioFilePath, 
                this.config.silenceThreshold, 
                this.config.minimumSilenceDuration
            );
            
            console.log(`Found ${silencePeriods.length} silence periods`);
            
            // Convert silence periods to speech segments
            const speechSegments = this.getSpeechSegments(silencePeriods, totalDuration);
            console.log(`Identified ${speechSegments.length} potential speech segments`);
            
            // Filter speech segments by minimum duration
            const validSpeechSegments = speechSegments.filter(([start, end]) => {
                const duration = end - start;
                return duration >= this.config.minimumSpeechDuration;
            });
            
            console.log(`Retained ${validSpeechSegments.length} speech segments (>= ${this.config.minimumSpeechDuration}s)`);
            
            // Add padding to speech segments
            const paddedSpeechSegments = this.addPaddingToSegments(validSpeechSegments, totalDuration);
            
            // Generate cut ranges (everything except padded speech segments)
            const cutRanges = this.generateCutRanges(paddedSpeechSegments, totalDuration);
            
            console.log(`Generated ${cutRanges.length} cut ranges`);
            this.logSegmentDetails(validSpeechSegments, cutRanges);
            
            return cutRanges;
            
        } catch (error) {
            console.error('Error analyzing audio:', error.message);
            return error;
        }
    }

    /**
     * Get audio duration using ffprobe
     * @param {string} filePath - Path to the audio file
     * @returns {Promise<number>} Duration in seconds
     */
    async getAudioDuration(filePath) {
        return new Promise((resolve, reject) => {
            ffmpeg.ffprobe(filePath, (err, metadata) => {
                if (err) {
                    reject(err);
                } else {
                    resolve(metadata.format.duration);
                }
            });
        });
    }

    /**
     * Detect silence periods in audio using FFmpeg
     * @param {string} audioFilePath - Path to the audio file
     * @param {number} threshold - Silence threshold in dB (default: -30)
     * @param {number} minDuration - Minimum silence duration in seconds (default: 1.0)
     * @returns {Promise<Array<[number, number]>>} Array of silence ranges
     */
    async detectSilence(audioFilePath, threshold = -30, minDuration = 1.0) {
        return new Promise((resolve, reject) => {
            const silencePeriods = [];
            let currentSilenceStart = null;
            
            // Use FFmpeg silencedetect filter
            const ffmpegProcess = spawn('ffmpeg', [
                '-i', audioFilePath,
                '-af', `silencedetect=noise=${threshold}dB:duration=${minDuration}`,
                '-f', 'null',
                '-'
            ], {
                stdio: ['pipe', 'pipe', 'pipe']
            });

            let stderrData = '';

            ffmpegProcess.stderr.on('data', (data) => {
                stderrData += data.toString();
            });

            ffmpegProcess.on('close', (code) => {
                if (code !== 0) {
                    reject(new Error(`FFmpeg process exited with code ${code}`));
                    return;
                }

                // Parse silence detection output
                const lines = stderrData.split('\n');
                
                for (const line of lines) {
                    // Look for silence start
                    const silenceStartMatch = line.match(/silence_start: ([\d.]+)/);
                    if (silenceStartMatch) {
                        currentSilenceStart = parseFloat(silenceStartMatch[1]);
                    }
                    
                    // Look for silence end
                    const silenceEndMatch = line.match(/silence_end: ([\d.]+)/);
                    if (silenceEndMatch && currentSilenceStart !== null) {
                        const silenceEnd = parseFloat(silenceEndMatch[1]);
                        silencePeriods.push([currentSilenceStart, silenceEnd]);
                        currentSilenceStart = null;
                    }
                }

                console.log(`Detected ${silencePeriods.length} silence periods`);
                resolve(silencePeriods);
            });

            ffmpegProcess.on('error', (error) => {
                reject(error);
            });
        });
    }

    /**
     * Convert silence periods to speech segments
     * @param {Array<[number, number]>} silencePeriods - Array of silence periods
     * @param {number} totalDuration - Total audio duration
     * @returns {Array<[number, number]>} Array of speech segments
     */
    getSpeechSegments(silencePeriods, totalDuration) {
        if (silencePeriods.length === 0) {
            return [[0, totalDuration]];
        }

        const speechSegments = [];
        let currentTime = 0;

        // Sort silence periods by start time
        const sortedSilence = [...silencePeriods].sort((a, b) => a[0] - b[0]);

        for (const [silenceStart, silenceEnd] of sortedSilence) {
            // Add speech segment before this silence
            if (currentTime < silenceStart) {
                speechSegments.push([currentTime, silenceStart]);
            }
            currentTime = Math.max(currentTime, silenceEnd);
        }

        // Add final speech segment after last silence
        if (currentTime < totalDuration) {
            speechSegments.push([currentTime, totalDuration]);
        }

        return speechSegments;
    }

    /**
     * Add padding to speech segments
     * @param {Array<[number, number]>} segments - Speech segments
     * @param {number} totalDuration - Total audio duration
     * @returns {Array<[number, number]>} Padded segments
     */
    addPaddingToSegments(segments, totalDuration) {
        return segments.map(([start, end]) => {
            const paddedStart = Math.max(0, start - this.config.speechPadding);
            const paddedEnd = Math.min(totalDuration, end + this.config.speechPadding);
            return [paddedStart, paddedEnd];
        });
    }

    /**
     * Generate cut ranges (inverse of speech segments)
     * @param {Array<[number, number]>} speechSegments - Speech segments to keep
     * @param {number} totalDuration - Total audio duration
     * @returns {Array<[number, number]>} Cut ranges
     */
    generateCutRanges(speechSegments, totalDuration) {
        if (speechSegments.length === 0) {
            return [[0, totalDuration]]; // Cut everything if no speech
        }

        const cutRanges = [];
        let currentTime = 0;

        // Sort speech segments by start time
        const sortedSegments = [...speechSegments].sort((a, b) => a[0] - b[0]);

        for (const [speechStart, speechEnd] of sortedSegments) {
            // Add cut range before this speech segment
            if (currentTime < speechStart) {
                cutRanges.push([currentTime, speechStart]);
            }
            currentTime = Math.max(currentTime, speechEnd);
        }

        // Add final cut range after last speech segment
        if (currentTime < totalDuration) {
            cutRanges.push([currentTime, totalDuration]);
        }

        return cutRanges.filter(([start, end]) => end > start);
    }

    /**
     * Log detailed information about segments
     * @param {Array<[number, number]>} speechSegments - Speech segments
     * @param {Array<[number, number]>} cutRanges - Cut ranges
     */
    logSegmentDetails(speechSegments, cutRanges) {
        console.log('\n📊 Analysis Results:');
        
        console.log('\n🎤 Speech segments to KEEP:');
        speechSegments.forEach(([start, end], i) => {
            const duration = end - start;
            console.log(`  ${i + 1}. ${start.toFixed(1)}s - ${end.toFixed(1)}s (${duration.toFixed(1)}s)`);
        });
        
        console.log('\n✂️  Segments to CUT:');
        cutRanges.forEach(([start, end], i) => {
            const duration = end - start;
            console.log(`  ${i + 1}. ${start.toFixed(1)}s - ${end.toFixed(1)}s (${duration.toFixed(1)}s)`);
        });

        const totalSpeechDuration = speechSegments.reduce((sum, [start, end]) => sum + (end - start), 0);
        const totalCutDuration = cutRanges.reduce((sum, [start, end]) => sum + (end - start), 0);
        
        console.log(`\n📈 Summary:`);
        console.log(`  Speech retained: ${totalSpeechDuration.toFixed(1)}s`);
        console.log(`  Audio removed: ${totalCutDuration.toFixed(1)}s`);
        console.log(`  Compression ratio: ${((totalCutDuration / (totalSpeechDuration + totalCutDuration)) * 100).toFixed(1)}% reduction`);
    }

    /**
     * Update analysis configuration
     * @param {Object} newConfig - New configuration options
     */
    updateConfig(newConfig) {
        this.config = { ...this.config, ...newConfig };
    }
}

module.exports = AudioAnalyzer; 