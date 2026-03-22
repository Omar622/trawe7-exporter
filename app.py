
# Entry point for the Tkinter app using refactored structure
from ui.main_window import MainWindow
from controller.app_controller import AppController
from logic.audio_analyzer import get_speech_segments
from logic.audio_processor import generate_cut_ranges
from resources.lang import LANG

if __name__ == '__main__':
    # Instantiate logic modules (could be classes if needed)
    logic_audio_analyzer = type('LogicAudioAnalyzer', (), {'get_speech_segments': staticmethod(get_speech_segments)})
    logic_audio_processor = type('LogicAudioProcessor', (), {'generate_cut_ranges': staticmethod(generate_cut_ranges)})

    # Create main window and controller
    main_window = MainWindow(None, LANG)
    controller = AppController(main_window, logic_audio_analyzer, logic_audio_processor, LANG)
    main_window.controller = controller
    main_window.mainloop()
