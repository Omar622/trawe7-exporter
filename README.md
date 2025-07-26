# Audio Cutter - Modular Audio Processing System

A Node.js application for cutting and processing M4A audio files using a modular architecture.

## Architecture

The system is built with two main modules:

### 1. AudioProcessor (`src/audioProcessor.js`)
**Responsible for:** Audio file manipulation and processing
- Reading M4A audio files
- Cutting audio segments based on time ranges
- Concatenating audio segments
- File I/O operations using FFmpeg

**Key Methods:**
- `processAudio(inputFile, outputFile, rangesToCut)` - Main processing method
- `getAudioDuration(filePath)` - Get audio file duration
- `extractSegment()` - Extract audio segments
- `concatenateAudioFiles()` - Join audio segments

### 2. AudioAnalyzer (`src/audioAnalyzer.js`)
**Responsible for:** Deciding which parts of audio to cut
- Audio analysis and pattern detection
- Determining cut ranges automatically
- Manual range configuration

**Key Methods:**
- `analyzeAndGetCutRanges(audioFilePath)` - Main analysis method
- `getManualCutRanges()` - Get predefined cut ranges
- `setManualCutRanges(ranges)` - Set custom ranges
- Future: `detectSilence()`, `analyzeVolume()`, `detectPattern()`

### 3. Main Orchestrator (`src/index.js`)
**Responsible for:** Coordinating between modules
- Workflow orchestration
- Command-line interface
- Module integration

## Installation

1. Install dependencies:
```bash
npm install
```

2. Install FFmpeg (required):
```bash
# macOS
brew install ffmpeg

# Ubuntu/Debian
sudo apt update && sudo apt install ffmpeg

# Windows
# Download from https://ffmpeg.org/download.html
```

## Usage

### Basic Usage (Automatic Analysis)
```bash
npm run cut-audio
# or
node src/index.js
```

### Custom Range Specification
```bash
node src/index.js "[[0,30],[60,90],[120,150]]"
```

### Programmatic Usage
```javascript
const { AudioProcessor, AudioAnalyzer } = require('./src/index.js');

// Initialize modules
const analyzer = new AudioAnalyzer();
const processor = new AudioProcessor();

// Get cut ranges and process audio
const ranges = await analyzer.analyzeAndGetCutRanges('input.m4a');
await processor.processAudio('input.m4a', 'output.m4a', ranges);
```

## Configuration

### Input/Output Files
Edit the file paths in `src/index.js`:
```javascript
const INPUT_FILE = path.join(__dirname, '..', 'a.m4a');
const OUTPUT_FILE = path.join(__dirname, '..', 'a_cut.m4a');
```

### Manual Cut Ranges
Edit ranges in `src/audioAnalyzer.js`:
```javascript
getManualCutRanges() {
    return [
        [0, 30],        // Cut from 0 to 30 seconds
        [60, 90],       // Cut from 60 to 90 seconds
        [120, 150],     // Cut from 120 to 150 seconds
    ];
}
```

## Range Format
Cut ranges are specified as arrays of `[start, end]` time pairs in seconds:
- `[0, 30]` - Remove audio from 0 to 30 seconds
- `[60, 90]` - Remove audio from 60 to 90 seconds

## Future Features (AudioAnalyzer)

The AudioAnalyzer module is designed to support:
- **Silence Detection**: Automatically detect and remove silent segments
- **Volume Analysis**: Remove segments below certain volume thresholds
- **Pattern Detection**: Identify and remove specific audio patterns
- **ML-based Analysis**: Use machine learning for intelligent content detection

## Scripts

```bash
npm run cut-audio    # Run audio processing
npm test            # Run tests (not implemented yet)
```

## Dependencies

- `fluent-ffmpeg`: FFmpeg wrapper for Node.js
- `light-audio-converter`: Audio format conversion utilities

## File Structure

```
├── src/
│   ├── index.js           # Main orchestrator
│   ├── audioProcessor.js  # Audio processing module
│   └── audioAnalyzer.js   # Audio analysis module
├── package.json
├── README.md
└── a.m4a                 # Input audio file
```

## Error Handling

The system includes comprehensive error handling:
- Input file validation
- FFmpeg operation error handling
- Temporary file cleanup
- Graceful failure with informative error messages

## Contributing

To extend the AudioAnalyzer module:
1. Implement analysis methods in `audioAnalyzer.js`
2. Add new detection algorithms
3. Integrate with the main workflow via `analyzeAndGetCutRanges()` 