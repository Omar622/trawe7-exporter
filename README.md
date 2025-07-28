# Audio Cutter - Intelligent Batch Audio Processing System

A Node.js application for intelligently cutting and processing multiple M4A audio files using advanced silence detection and speech analysis. Process entire folders of audio files automatically!

## 📑 Table of Contents

- [🎯 Key Features](#-key-features)
- [📁 Directory Structure](#-directory-structure)
- [🏗️ Architecture](#architecture)
  - [FileManager](#1-filemanager-srcfilemanagerjs)
  - [AudioProcessor](#2-audioprocessor-srcaudioprocessorjs)
  - [AudioAnalyzer](#3-audioanalyzer-srcaudioanalyzerjs)
  - [Main Orchestrator](#4-main-orchestrator-srcindexjs)
- [⚙️ Installation](#installation)
- [📋 Supported Formats](#supported-formats)
- [🚀 Usage](#usage)
  - [Batch Processing with Intelligent Analysis](#batch-processing-with-intelligent-analysis-recommended)
  - [Batch Processing with Custom Ranges](#batch-processing-with-custom-ranges)
  - [Programmatic Usage](#programmatic-usage)
- [🔧 Configuration](#configuration)
  - [Audio Analysis Parameters](#audio-analysis-parameters)
  - [Parameter Explanation](#parameter-explanation)
- [📊 Batch Processing Output Example](#batch-processing-output-example)
- [📝 Range Format](#range-format)
- [❌ What Gets Removed](#what-gets-removed)
- [✅ What Gets Retained](#what-gets-retained)
- [📜 Scripts](#scripts)
- [📦 Dependencies](#dependencies)
- [🛡️ Error Handling](#error-handling)
- [🎛️ Tuning Parameters](#tuning-parameters)
- [🔄 Workflow](#workflow)
- [📂 File Management](#file-management)
- [🤝 Contributing](#contributing)

## 🎯 Key Features

- **🧠 Intelligent Analysis**: Automatically detects speech vs silence using FFmpeg
- **📁 Batch Processing**: Process multiple audio files in one go
- **✂️ Smart Cutting**: Removes long silent periods and sparse speech
- **⏱️ Duration Filtering**: Only retains continuous speech segments ≥ 10 seconds
- **🛡️ Safe Padding**: Adds padding around speech to avoid cutting words
- **📊 Detailed Analytics**: Shows compression ratios and processing statistics
- **🏗️ Modular Architecture**: Clean, maintainable codebase with separated concerns

## 📁 Directory Structure

```
trawe7-exporter/
├── input/                 # Place your M4A files here
│   ├── audio1.m4a
│   ├── audio2.m4a
│   └── ...
├── output/                # Processed files will be saved here
│   ├── audio1.m4a        # (processed versions)
│   ├── audio2.m4a
│   └── ...
├── src/
│   ├── index.js          # Main orchestrator and CLI
│   ├── audioProcessor.js # Audio manipulation and FFmpeg operations
│   ├── audioAnalyzer.js  # Intelligent silence detection and analysis
│   └── fileManager.js    # File and directory management
├── package.json
└── README.md
```

## 🏗️ Architecture

The system is built with a modular architecture for better maintainability:

### 1. FileManager (`src/fileManager.js`)
**Responsible for:** File and directory operations
- Managing input and output directories
- Discovering audio files in the input folder
- Generating output file paths
- File existence and size utilities

**Key Methods:**
- `getAudioFiles()` - Find all supported audio files
- `getOutputFilePath(inputFile)` - Generate output path
- `initializeDirectories()` - Create input/output folders
- `fileExists()`, `getFileStats()` - File utilities

### 2. AudioProcessor (`src/audioProcessor.js`)
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

### 3. AudioAnalyzer (`src/audioAnalyzer.js`)
**Responsible for:** Intelligent audio analysis and decision making
- Advanced silence detection using FFmpeg's silencedetect filter
- Speech segment identification and duration filtering
- Automatic cut range generation based on audio content

**Key Methods:**
- `analyzeAndGetCutRanges(audioFilePath)` - Main intelligent analysis method
- `detectSilence()` - FFmpeg-based silence detection
- `getSpeechSegments()` - Convert silence periods to speech segments
- `generateCutRanges()` - Create cut ranges from analysis results

### 4. Main Orchestrator (`src/index.js`)
**Responsible for:** Coordinating the intelligent batch workflow
- Orchestrates analysis and processing pipeline for multiple files
- Command-line interface with custom range support
- Progress tracking and batch processing statistics
- Error handling and user feedback

## ⚙️ Installation

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

3. Create input directory and add your audio files:
```bash
mkdir input
# Copy your M4A files to the input/ directory
```

## 📋 Supported Formats

Currently supports:
- **M4A** audio files (primary format)

## 🚀 Usage

### Batch Processing with Intelligent Analysis (Recommended)
```bash
npm run cut-audio
# or
node src/index.js
```

The system will:
1. **Scan** the `input/` directory for M4A files
2. **Analyze** each audio file using silence detection
3. **Identify** continuous speech segments in each file
4. **Filter** segments by minimum duration (10s)
5. **Process** each file and save to `output/` directory
6. **Report** batch processing statistics

### Batch Processing with Custom Ranges
Apply the same custom cut ranges to all files:
```bash
node src/index.js "[[0,30],[60,90],[120,150]]"
```

### Programmatic Usage
```javascript
const { main, batchProcessWithCustomRanges, fileManager } = require('./src/index.js');

// Batch process all files with intelligent analysis
await main();

// Batch process with custom ranges
await batchProcessWithCustomRanges([[0, 30], [60, 90]]);

// Process individual files
const { AudioProcessor, AudioAnalyzer } = require('./src/index.js');
const analyzer = new AudioAnalyzer();
const processor = new AudioProcessor();

const ranges = await analyzer.analyzeAndGetCutRanges('input/audio.m4a');
await processor.processAudio('input/audio.m4a', 'output/audio.m4a', ranges);
```

## 🔧 Configuration

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

## 📊 Batch Processing Output Example

```
🎵 Starting batch audio processing workflow...

📁 Found 3 audio file(s) to process:
  1. lecture1.m4a
  2. interview.m4a
  3. presentation.m4a

============================================================
📋 Processing file 1/3

🎵 Processing: lecture1.m4a
📥 Input: /path/to/input/lecture1.m4a
📤 Output: /path/to/output/lecture1.m4a

📊 Analyzing audio file...
[Analysis details...]
✅ Successfully processed: lecture1.m4a

============================================================
📋 Processing file 2/3

🎵 Processing: interview.m4a
[Processing details...]
✅ Successfully processed: interview.m4a

============================================================
📋 Processing file 3/3

🎵 Processing: presentation.m4a
[Processing details...]
✅ Successfully processed: presentation.m4a

============================================================
📊 Batch Processing Summary:
✅ Successfully processed: 3 files
❌ Failed to process: 0 files
📁 Output directory: /path/to/output

🎉 Batch audio processing workflow completed!
```

## 📝 Range Format
Cut ranges are automatically generated as arrays of `[start, end]` time pairs in seconds:
- `[0, 44.7]` - Remove audio from 0 to 44.7 seconds
- `[79.1, 91.6]` - Remove audio from 79.1 to 91.6 seconds

## ❌ What Gets Removed

The intelligent analysis removes:
- **Long silent periods** (3+ seconds of very quiet audio)
- **Brief speech snippets** (speech segments shorter than 10 seconds)
- **Sparse talk** (isolated words/phrases between long silences)
- **Background noise** (audio below -10dB threshold)

## ✅ What Gets Retained

The system keeps:
- **Continuous speech segments** lasting 10+ seconds
- **0.5 second padding** around each speech segment
- **Clear, sustained dialogue** above the silence threshold

## 📜 Scripts

```bash
npm run cut-audio    # Run intelligent batch audio processing
npm test            # Run tests (not implemented yet)
```

## 📦 Dependencies

- `fluent-ffmpeg`: FFmpeg wrapper for Node.js audio processing
- `light-audio-converter`: Audio format conversion utilities

## 🛡️ Error Handling

The system includes comprehensive error handling:
- Input directory validation and creation
- Input file validation for each audio file
- FFmpeg operation error handling per file
- Temporary file cleanup
- Graceful failure with informative error messages
- Individual file error reporting in batch processing
- Batch processing continues even if individual files fail

## 🎛️ Tuning Parameters

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

## 🔄 Workflow

1. **Setup**: Create `input/` directory and copy your M4A files
2. **Run**: Execute `npm run cut-audio` or `node src/index.js`
3. **Monitor**: Watch the progress as each file is processed
4. **Results**: Find processed files in the `output/` directory
5. **Review**: Check the batch processing summary for any failed files

## 📂 File Management

- **Input files**: Original files remain untouched in `input/`
- **Output files**: Processed files are saved to `output/` with the same filenames
- **Temporary files**: Automatically cleaned up during processing
- **Directory creation**: Input and output directories are created automatically if they don't exist

## 🤝 Contributing

To extend the system:
1. **FileManager**: Add new file utilities in `src/fileManager.js`
2. **AudioAnalyzer**: Implement new analysis methods in `src/audioAnalyzer.js`
3. **AudioProcessor**: Add new processing capabilities in `src/audioProcessor.js`
4. **Main workflow**: Enhance batch processing logic in `src/index.js`
5. Test with various audio content types and batch sizes 