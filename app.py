"""Entry point: detect capabilities, build the window, wire the controller."""
from controller.app_controller import AppController
from services.capabilities import detect_capabilities
from ui.main_window import TaraweehCutterApp


def main():
    caps = detect_capabilities()
    window = TaraweehCutterApp()
    controller = AppController(window, caps)
    window.controller = controller
    controller.restore_session()
    window.protocol("WM_DELETE_WINDOW", controller.on_close)
    controller.start_autosave()
    window.mainloop()


if __name__ == "__main__":
    main()
