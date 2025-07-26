const ffmpeg = require('fluent-ffmpeg');
const path = require('path');
const fs = require('fs');

class AudioProcessor {
    constructor() {
        this.tempFiles = [];
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
     * Extract a segment from the audio file
     * @param {string} inputFile - Input file path
     * @param {string} outputFile - Output file path
     * @param {number} startTime - Start time in seconds
     * @param {number} duration - Duration in seconds
     * @returns {Promise<void>}
     */
    extractSegment(inputFile, outputFile, startTime, duration) {
        return new Promise((resolve, reject) => {
            ffmpeg(inputFile)
                .setStartTime(startTime)
                .setDuration(duration)
                .audioCodec('aac')
                .output(outputFile)
                .on('end', () => resolve())
                .on('error', (err) => reject(err))
                .run();
        });
    }

    /**
     * Concatenate multiple audio files
     * @param {string[]} inputFiles - Array of input file paths
     * @param {string} outputFile - Output file path
     * @returns {Promise<void>}
     */
    concatenateAudioFiles(inputFiles, outputFile) {
        return new Promise((resolve, reject) => {
            const command = ffmpeg();
            
            inputFiles.forEach(file => {
                command.input(file);
            });

            command
                .on('end', () => resolve())
                .on('error', (err) => reject(err))
                .mergeToFile(outputFile);
        });
    }

    /**
     * Generate segments to keep (inverse of ranges to cut)
     * @param {Array<[number, number]>} rangesToCut - Array of [start, end] ranges to cut
     * @param {number} totalDuration - Total audio duration
     * @returns {Array<[number, number]>} Array of [start, end] segments to keep
     */
    generateSegmentsToKeep(rangesToCut, totalDuration) {
        if (rangesToCut.length === 0) {
            return [[0, totalDuration]];
        }

        // Sort ranges by start time
        const sortedRanges = [...rangesToCut].sort((a, b) => a[0] - b[0]);
        const segments = [];
        let currentTime = 0;

        for (const [start, end] of sortedRanges) {
            // Add segment before the cut (if any)
            if (currentTime < start) {
                segments.push([currentTime, start]);
            }
            currentTime = Math.max(currentTime, end);
        }

        // Add final segment after the last cut
        if (currentTime < totalDuration) {
            segments.push([currentTime, totalDuration]);
        }

        return segments.filter(([start, end]) => end > start);
    }

    /**
     * Process audio file by cutting specified ranges
     * @param {string} inputFile - Input audio file path
     * @param {string} outputFile - Output audio file path
     * @param {Array<[number, number]>} rangesToCut - Array of [start, end] ranges to cut
     * @returns {Promise<void>}
     */
    async processAudio(inputFile, outputFile, rangesToCut) {
        try {
            // Check if input file exists
            if (!fs.existsSync(inputFile)) {
                throw new Error(`Input file not found: ${inputFile}`);
            }

            console.log(`Processing audio file: ${inputFile}`);
            console.log(`Ranges to cut: ${JSON.stringify(rangesToCut)}`);

            // Get audio duration first
            const duration = await this.getAudioDuration(inputFile);
            console.log(`Original audio duration: ${duration} seconds`);

            // Generate segments to keep (inverse of ranges to cut)
            const segmentsToKeep = this.generateSegmentsToKeep(rangesToCut, duration);
            console.log(`Segments to keep: ${JSON.stringify(segmentsToKeep)}`);

            if (segmentsToKeep.length === 0) {
                throw new Error('No segments to keep after cutting specified ranges');
            }

            // Create temporary files for each segment
            this.tempFiles = [];
            for (let i = 0; i < segmentsToKeep.length; i++) {
                const [start, end] = segmentsToKeep[i];
                const tempFile = path.join(path.dirname(outputFile), `temp_segment_${i}_${Date.now()}.m4a`);
                this.tempFiles.push(tempFile);
                
                await this.extractSegment(inputFile, tempFile, start, end - start);
                console.log(`Extracted segment ${i + 1}/${segmentsToKeep.length}: ${start}s to ${end}s`);
            }

            // Concatenate all segments
            if (this.tempFiles.length === 1) {
                // If only one segment, just rename it
                fs.renameSync(this.tempFiles[0], outputFile);
            } else {
                // Concatenate multiple segments
                await this.concatenateAudioFiles(this.tempFiles, outputFile);
            }

            console.log(`Audio processing complete! Output saved to: ${outputFile}`);

        } catch (error) {
            console.error('Error processing audio:', error.message);
            throw error;
        } finally {
            // Clean up temporary files
            this.cleanupTempFiles();
        }
    }

    /**
     * Clean up temporary files
     */
    cleanupTempFiles() {
        this.tempFiles.forEach(file => {
            if (fs.existsSync(file)) {
                try {
                    fs.unlinkSync(file);
                    console.log(`Cleaned up temp file: ${file}`);
                } catch (err) {
                    console.warn(`Failed to clean up temp file ${file}:`, err.message);
                }
            }
        });
        this.tempFiles = [];
    }
}

module.exports = AudioProcessor; 