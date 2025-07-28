const path = require('path');
const AudioProcessor = require('./audioProcessor');
const AudioAnalyzer = require('./audioAnalyzer');
const fileManager = require('./fileManager');

/**
 * Process a single audio file
 * @param {string} inputFilePath - Path to input audio file
 * @param {AudioAnalyzer} analyzer - AudioAnalyzer instance
 * @param {AudioProcessor} processor - AudioProcessor instance
 * @returns {Promise<boolean>} Success status
 */
async function processSingleFile(inputFilePath, analyzer, processor) {
    try {
        const fileName = path.basename(inputFilePath);
        const outputFilePath = fileManager.getOutputFilePath(inputFilePath);
        
        console.log(`\n🎵 Processing: ${fileName}`);
        console.log(`📥 Input: ${inputFilePath}`);
        console.log(`📤 Output: ${outputFilePath}`);
        
        // Step 1: Analyze audio to determine cut ranges
        console.log('📊 Analyzing audio file...');
        const rangesToCut = await analyzer.analyzeAndGetCutRanges(inputFilePath);
        console.log(`Found ${rangesToCut.length} ranges to cut`);

        // Step 2: Process audio with the determined ranges
        console.log('✂️  Processing audio file...');
        await processor.processAudio(inputFilePath, outputFilePath, rangesToCut);

        console.log(`✅ Successfully processed: ${fileName}`);
        return true;
        
    } catch (error) {
        console.error(`❌ Error processing ${path.basename(inputFilePath)}:`, error.message);
        return false;
    }
}

/**
 * Process a single audio file with custom ranges
 * @param {string} inputFilePath - Path to input audio file
 * @param {Array<[number, number]>} customRanges - Custom ranges to cut
 * @param {AudioProcessor} processor - AudioProcessor instance
 * @returns {Promise<boolean>} Success status
 */
async function processSingleFileWithCustomRanges(inputFilePath, customRanges, processor) {
    try {
        const fileName = path.basename(inputFilePath);
        const outputFilePath = fileManager.getOutputFilePath(inputFilePath);
        
        console.log(`\n🎵 Processing with custom ranges: ${fileName}`);
        console.log(`📥 Input: ${inputFilePath}`);
        console.log(`📤 Output: ${outputFilePath}`);
        
        console.log('✂️  Processing audio file with custom ranges...');
        await processor.processAudio(inputFilePath, outputFilePath, customRanges);

        console.log(`✅ Successfully processed: ${fileName}`);
        return true;
        
    } catch (error) {
        console.error(`❌ Error processing ${path.basename(inputFilePath)}:`, error.message);
        return false;
    }
}

/**
 * Main function to process all audio files in input directory
 */
async function main() {
    try {
        console.log('🎵 Starting batch audio processing workflow...\n');

        // Initialize directories
        fileManager.initializeDirectories();

        // Get all audio files from input directory
        const audioFiles = fileManager.getAudioFiles();
        
        if (audioFiles.length === 0) {
            console.log(`📂 No supported audio files found in ${fileManager.INPUT_DIR}`);
            console.log(`Supported formats: ${fileManager.SUPPORTED_EXTENSIONS.join(', ')}`);
            return;
        }

        console.log(`📁 Found ${audioFiles.length} audio file(s) to process:`);
        audioFiles.forEach((file, index) => {
            console.log(`  ${index + 1}. ${path.basename(file)}`);
        });

        // Initialize modules
        const analyzer = new AudioAnalyzer();
        const processor = new AudioProcessor();

        // Process each file
        let successCount = 0;
        let failureCount = 0;

        for (let i = 0; i < audioFiles.length; i++) {
            const inputFile = audioFiles[i];
            console.log(`\n${'='.repeat(60)}`);
            console.log(`📋 Processing file ${i + 1}/${audioFiles.length}`);
            
            const success = await processSingleFile(inputFile, analyzer, processor);
            if (success) {
                successCount++;
            } else {
                failureCount++;
            }
        }

        // Summary
        console.log(`\n${'='.repeat(60)}`);
        console.log('📊 Batch Processing Summary:');
        console.log(`✅ Successfully processed: ${successCount} files`);
        console.log(`❌ Failed to process: ${failureCount} files`);
        console.log(`📁 Output directory: ${fileManager.OUTPUT_DIR}`);
        
        if (successCount > 0) {
            console.log('\n🎉 Batch audio processing workflow completed!');
        }
        
    } catch (error) {
        console.error('\n❌ Error in batch audio processing workflow:', error.message);
        process.exit(1);
    }
}

/**
 * Alternative function for batch processing with custom ranges
 * @param {Array<[number, number]>} customRanges - Custom ranges to cut (applied to all files)
 */
async function batchProcessWithCustomRanges(customRanges) {
    try {
        console.log('🎵 Starting batch audio processing with custom ranges...\n');
        console.log(`Custom ranges: ${JSON.stringify(customRanges)}`);

        // Initialize directories
        fileManager.initializeDirectories();

        // Get all audio files from input directory
        const audioFiles = fileManager.getAudioFiles();
        
        if (audioFiles.length === 0) {
            console.log(`📂 No supported audio files found in ${fileManager.INPUT_DIR}`);
            console.log(`Supported formats: ${fileManager.SUPPORTED_EXTENSIONS.join(', ')}`);
            return;
        }

        console.log(`📁 Found ${audioFiles.length} audio file(s) to process:`);
        audioFiles.forEach((file, index) => {
            console.log(`  ${index + 1}. ${path.basename(file)}`);
        });

        const processor = new AudioProcessor();

        // Process each file
        let successCount = 0;
        let failureCount = 0;

        for (let i = 0; i < audioFiles.length; i++) {
            const inputFile = audioFiles[i];
            console.log(`\n${'='.repeat(60)}`);
            console.log(`📋 Processing file ${i + 1}/${audioFiles.length}`);
            
            const success = await processSingleFileWithCustomRanges(inputFile, customRanges, processor);
            if (success) {
                successCount++;
            } else {
                failureCount++;
            }
        }

        // Summary
        console.log(`\n${'='.repeat(60)}`);
        console.log('📊 Batch Processing Summary:');
        console.log(`✅ Successfully processed: ${successCount} files`);
        console.log(`❌ Failed to process: ${failureCount} files`);
        console.log(`📁 Output directory: ${fileManager.OUTPUT_DIR}`);
        
        if (successCount > 0) {
            console.log('\n🎉 Batch audio processing with custom ranges completed!');
        }
        
    } catch (error) {
        console.error('\n❌ Error in batch audio processing:', error.message);
        process.exit(1);
    }
}

// Run the main workflow if this file is executed directly
if (require.main === module) {
    // Check if custom ranges are provided as command line arguments
    if (process.argv.length > 2) {
        try {
            // Example usage: node src/index.js "[[0,30],[60,90]]"
            const customRanges = JSON.parse(process.argv[2]);
            batchProcessWithCustomRanges(customRanges);
        } catch (parseError) {
            console.error('❌ Invalid custom ranges format. Expected: "[[start1,end1],[start2,end2]]"');
            console.error('Example: node src/index.js "[[0,30],[60,90]]"');
            process.exit(1);
        }
    } else {
        // Run with automatic analysis
        main();
    }
}

// Export functions for use in other modules
module.exports = {
    main,
    batchProcessWithCustomRanges,
    processSingleFile,
    processSingleFileWithCustomRanges,
    AudioProcessor,
    AudioAnalyzer,
    fileManager
};
