const path = require('path');
const AudioProcessor = require('./audioProcessor');
const AudioAnalyzer = require('./audioAnalyzer');

// Input and output file paths
const INPUT_FILE = path.join(__dirname, '..', 'a.m4a');
const OUTPUT_FILE = path.join(__dirname, '..', 'a_cut.m4a');

/**
 * Main function to orchestrate audio analysis and processing
 */
async function main() {
    try {
        console.log('🎵 Starting audio processing workflow...\n');

        // Initialize modules
        const analyzer = new AudioAnalyzer();
        const processor = new AudioProcessor();

        // Step 1: Analyze audio to determine cut ranges
        console.log('📊 Step 1: Analyzing audio file...');
        const rangesToCut = await analyzer.analyzeAndGetCutRanges(INPUT_FILE);
        console.log(`Found ${rangesToCut.length} ranges to cut\n`);

        // Step 2: Process audio with the determined ranges
        console.log('✂️  Step 2: Processing audio file...');
        await processor.processAudio(INPUT_FILE, OUTPUT_FILE, rangesToCut);

        console.log('\n✅ Audio processing workflow completed successfully!');
        
    } catch (error) {
        console.error('\n❌ Error in audio processing workflow:', error.message);
        process.exit(1);
    }
}

/**
 * Alternative function for manual range specification
 * @param {Array<[number, number]>} customRanges - Custom ranges to cut
 */
async function processWithCustomRanges(customRanges) {
    try {
        console.log('🎵 Starting audio processing with custom ranges...\n');

        const processor = new AudioProcessor();
        
        console.log('✂️  Processing audio file with custom ranges...');
        await processor.processAudio(INPUT_FILE, OUTPUT_FILE, customRanges);

        console.log('\n✅ Audio processing completed successfully!');
        
    } catch (error) {
        console.error('\n❌ Error in audio processing:', error.message);
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
            processWithCustomRanges(customRanges);
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
    processWithCustomRanges,
    AudioProcessor,
    AudioAnalyzer
};
