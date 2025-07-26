# Audio Cutter - Intelligent Audio Processing System

A Node.js application for intelligently cutting and processing M4A audio files using advanced silence detection and speech analysis.

## 🎯 Key Features

- **🧠 Intelligent Analysis**: Automatically detects speech vs silence using FFmpeg
- **✂️ Smart Cutting**: Removes long silent periods and sparse speech
- **⏱️ Duration Filtering**: Only retains continuous speech segments ≥ 10 seconds
- **🛡️ Safe Padding**: Adds padding around speech to avoid cutting words
- **📊 Detailed Analytics**: Shows compression ratios and processing statistics

## Architecture

The system is built with two main modules:

### 1. AudioProcessor (`src/audioProcessor.js`)
**Responsible for:** Audio file manipulation and processing
- Reading M4A audio files using FFmpeg
- Cutting audio segments based on time ranges
- Concatenating audio segments
- File I/O operations and temporary file management

**Key Methods:**
- `processAudio(inputFile, outputFile, rangesToCut)` - Main processing method
- `getAudioDuration(filePath)` - Get audio file duration
- `extractSegment()` - Extract audio segments
- `concatenateAudioFiles()` - Join audio segments

### 2. AudioAnalyzer (`src/audioAnalyzer.js`)
**Responsible for:** Intelligent audio analysis and decision making
- Advanced silence detection using FFmpeg's silencedetect filter
- Speech segment identification and duration filtering
- Automatic cut range generation based on audio content

**Key Methods:**
- `analyzeAndGetCutRanges(audioFilePath)` - Main intelligent analysis method
- `detectSilence()` - FFmpeg-based silence detection
- `getSpeechSegments()` - Convert silence periods to speech segments
- `generateCutRanges()` - Create cut ranges from analysis results

### 3. Main Orchestrator (`src/index.js`)
**Responsible for:** Coordinating the intelligent workflow
- Orchestrates analysis and processing pipeline
- Command-line interface with custom range support
- Error handling and user feedback

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

## Configuration

### Audio Analysis Parameters
The system uses intelligent defaults optimized for speech processing:

```javascript
this.config = {
    silenceThreshold: -10.0,      // dB - very strict silence detection
    minimumSilenceDuration: 3.0,  // seconds - minimum silence period to detect
    minimumSpeechDuration: 10.0,  // seconds - minimum speech segment to retain
    speechPadding: 0.5,           // seconds - safety padding around speech
};
```

### Parameter Explanation:
- **silenceThreshold (-10.0 dB)**: Only very quiet audio is considered silence
- **minimumSilenceDuration (3.0s)**: Must have 3+ seconds of silence to detect a gap
- **minimumSpeechDuration (10.0s)**: Only speech segments 10+ seconds long are kept
- **speechPadding (0.5s)**: Adds 0.5s buffer around speech to avoid cutting words

### Input/Output Files
Edit the file paths in `src/index.js`:
```javascript
const INPUT_FILE = path.join(__dirname, '..', 'a.m4a');
const OUTPUT_FILE = path.join(__dirname, '..', 'a_cut.m4a');
```

## Usage

### Intelligent Analysis (Recommended)
```bash
npm run cut-audio
# or
node src/index.js
```

The system will:
1. **Analyze** your audio file using silence detection
2. **Identify** continuous speech segments
3. **Filter** segments by minimum duration (10s)
4. **Generate** cut ranges automatically
5. **Process** the audio and create the output file

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

// Configure analysis parameters (optional)
analyzer.updateConfig({
    silenceThreshold: -15.0,
    minimumSpeechDuration: 5.0
});

// Intelligent analysis and processing
const ranges = await analyzer.analyzeAndGetCutRanges('input.m4a');
await processor.processAudio('input.m4a', 'output.m4a', ranges);
```

## Analysis Output Example

```
🎵 Starting audio processing workflow...

📊 Step 1: Analyzing audio file...
Analyzing audio file: /path/to/a.m4a
Silence threshold: -10dB
Minimum silence duration: 3s
Minimum speech duration: 10s
Total audio duration: 180.45s
Detected 8 silence periods
Found 8 silence periods
Identified 5 potential speech segments
Retained 2 speech segments (>= 10s)
Generated 3 cut ranges

📊 Analysis Results:

🎤 Speech segments to KEEP:
  1. 45.2s - 78.6s (33.4s)
  2. 92.1s - 145.8s (53.7s)

✂️ Segments to CUT:
  1. 0.0s - 44.7s (44.7s)
  2. 79.1s - 91.6s (12.5s)
  3. 146.3s - 180.5s (34.2s)

📈 Summary:
  Speech retained: 87.1s
  Audio removed: 93.4s
  Compression ratio: 51.7% reduction

✂️ Step 2: Processing audio file...
Processing audio file: /path/to/a.m4a
Ranges to cut: [[0,44.7],[79.1,91.6],[146.3,180.5]]
...
✅ Audio processing workflow completed successfully!
```

## Range Format
Cut ranges are automatically generated as arrays of `[start, end]` time pairs in seconds:
- `[0, 44.7]` - Remove audio from 0 to 44.7 seconds
- `[79.1, 91.6]` - Remove audio from 79.1 to 91.6 seconds

## What Gets Removed

The intelligent analysis removes:
- **Long silent periods** (3+ seconds of very quiet audio)
- **Brief speech snippets** (speech segments shorter than 10 seconds)
- **Sparse talk** (isolated words/phrases between long silences)
- **Background noise** (audio below -10dB threshold)

## What Gets Retained

The system keeps:
- **Continuous speech segments** lasting 10+ seconds
- **0.5 second padding** around each speech segment
- **Clear, sustained dialogue** above the silence threshold

## Scripts

```bash
npm run cut-audio    # Run intelligent audio processing
npm test            # Run tests (not implemented yet)
```

## Dependencies

- `fluent-ffmpeg`: FFmpeg wrapper for Node.js audio processing
- `light-audio-converter`: Audio format conversion utilities

## File Structure

```
├── src/
│   ├── index.js           # Main orchestrator and CLI
│   ├── audioProcessor.js  # Audio manipulation and FFmpeg operations
│   └── audioAnalyzer.js   # Intelligent silence detection and analysis
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
- Fallback mechanisms for analysis failures

## Tuning Parameters

### For Different Content Types:

**Podcasts/Interviews (Current Settings):**
```javascript
silenceThreshold: -10.0    // Strict silence detection
minimumSilenceDuration: 3.0
minimumSpeechDuration: 10.0
```

**Lectures/Presentations:**
```javascript
silenceThreshold: -15.0    // More lenient for room noise
minimumSilenceDuration: 2.0
minimumSpeechDuration: 15.0 // Longer segments
```

**Casual Conversations:**
```javascript
silenceThreshold: -8.0     // Very strict for overlapping speech
minimumSilenceDuration: 2.0
minimumSpeechDuration: 5.0  // Shorter segments OK
```

## Contributing

To extend the AudioAnalyzer module:
1. Implement new analysis methods in `audioAnalyzer.js`
2. Add detection algorithms using FFmpeg filters
3. Update configuration options for new parameters
4. Test with various audio content types 