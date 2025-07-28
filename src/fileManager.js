const path = require('path');
const fs = require('fs');

// Input and output directory paths
const INPUT_DIR = path.join(__dirname, '..', 'input');
const OUTPUT_DIR = path.join(__dirname, '..', 'output');

// Supported audio file extensions
const SUPPORTED_EXTENSIONS = ['.m4a'];

/**
 * Ensure directory exists, create if it doesn't
 * @param {string} dirPath - Directory path to ensure
 */
function ensureDirectoryExists(dirPath) {
    if (!fs.existsSync(dirPath)) {
        fs.mkdirSync(dirPath, { recursive: true });
        console.log(`📁 Created directory: ${dirPath}`);
    }
}

/**
 * Get all supported audio files from input directory
 * @returns {string[]} Array of audio file paths
 */
function getAudioFiles() {
    ensureDirectoryExists(INPUT_DIR);
    
    const files = fs.readdirSync(INPUT_DIR);
    const audioFiles = files.filter(file => {
        const ext = path.extname(file).toLowerCase();
        return SUPPORTED_EXTENSIONS.includes(ext);
    });
    
    return audioFiles.map(file => path.join(INPUT_DIR, file));
}

/**
 * Generate output file path for a given input file
 * @param {string} inputFilePath - Path to input audio file
 * @returns {string} Output file path
 */
function getOutputFilePath(inputFilePath) {
    const fileName = path.basename(inputFilePath);
    return path.join(OUTPUT_DIR, fileName);
}

/**
 * Initialize directories (create input and output directories if they don't exist)
 */
function initializeDirectories() {
    ensureDirectoryExists(INPUT_DIR);
    ensureDirectoryExists(OUTPUT_DIR);
}

/**
 * Check if a file exists
 * @param {string} filePath - Path to the file
 * @returns {boolean} True if file exists
 */
function fileExists(filePath) {
    return fs.existsSync(filePath);
}

/**
 * Get file size in bytes
 * @param {string} filePath - Path to the file
 * @returns {number} File size in bytes
 */
function getFileSize(filePath) {
    if (!fileExists(filePath)) {
        return 0;
    }
    const stats = fs.statSync(filePath);
    return stats.size;
}

/**
 * Format file size in human readable format
 * @param {number} bytes - File size in bytes
 * @returns {string} Formatted file size
 */
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

/**
 * Get file statistics for display
 * @param {string} filePath - Path to the file
 * @returns {Object} File statistics object
 */
function getFileStats(filePath) {
    if (!fileExists(filePath)) {
        return {
            exists: false,
            size: 0,
            formattedSize: '0 Bytes'
        };
    }
    
    const size = getFileSize(filePath);
    return {
        exists: true,
        size: size,
        formattedSize: formatFileSize(size)
    };
}

module.exports = {
    // Constants
    INPUT_DIR,
    OUTPUT_DIR,
    SUPPORTED_EXTENSIONS,
    
    // Directory management
    ensureDirectoryExists,
    initializeDirectories,
    
    // File discovery and paths
    getAudioFiles,
    getOutputFilePath,
    
    // File utilities
    fileExists,
    getFileSize,
    formatFileSize,
    getFileStats
}; 