from typing import Dict, Any, Union
import time
import threading
from direct_keys import DIK_W, DIK_S, DIK_SPACE
from window_utils import send_key_to_window


class Macro:
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description

    def update_status(self, message: str, total_steps: int = None, current_step: int = None):
        """
        Update the status message with step information if provided.
        """
        if total_steps is not None and current_step is not None:
            step_info = f"[Step {current_step}/{total_steps}] "
            message = step_info + message
        print(message)
        # The UI will pick up these messages from stdout

    def safe_sleep(self, duration: float, running: threading.Event,
                   current_step: int = None, total_steps: int = None) -> bool:
        """
        Sleep for the specified duration while checking the running state.
        Returns False if interrupted by running state change, True if completed.
        """
        start_time = time.time()
        self.update_status(
            f"Waiting for {duration} seconds...", total_steps, current_step)
        while time.time() - start_time < duration:
            if not running.is_set():
                return False
            time.sleep(0.1)
        return True

    def press_key(self, game_window: Any, key: str, duration: Union[float, None],
                  running: threading.Event, count: int = 1, delay: float = 0,
                  current_step: int = None, total_steps: int = None) -> bool:
        """
        Press a key one or more times with optional duration and delay between presses.
        Returns False if interrupted by running state change, True if completed.
        """
        for i in range(count):
            # Check if still running before pressing
            if not running.is_set():
                return False

            if count > 1:
                action_msg = f"Pressing {key.upper()} ({i+1}/{count})"
            else:
                if duration:
                    action_msg = f"Pressing {key.upper()} for {duration} seconds"
                else:
                    action_msg = f"Pressing {key.upper()}"

            self.update_status(action_msg, total_steps, current_step)
            send_key_to_window(game_window, key, duration, running)

            # Check if still running after key press
            if not running.is_set():
                return False

            self.update_status(
                f"Released {key.upper()}", total_steps, current_step)

            if delay > 0 and i < count - 1:  # Don't delay after last press
                if not self.safe_sleep(delay, running, current_step, total_steps):
                    return False

        return True

    def run(self, game_window: Any, running: threading.Event) -> None:
        """
        Execute the macro's actions.
        Args:
            game_window: The window handle to send inputs to
            running: Threading event that controls macro execution
        """
        raise NotImplementedError("Each macro must implement run()")


class BF6SiegeCairoMacro(Macro):
    def __init__(self):
        super().__init__(
            "Battlefield 6 Siege of Cairo AFK",
            "Siege of Cairo AFK Macro for Battlefield 6 that automates capturing objectives. Portal Code: YVNDS - Tutorial: https://youtu.be/LH_Gj87xodI?si=GJvNM4reqZoQxJ7f&t=161"
        )

    def run(self, game_window: Any, running: threading.Event) -> None:
        total_steps = 12  # Total number of major steps in the cycle

        while running.is_set():
            try:
                self.update_status(
                    "Starting Siege of Cairo cycle...", total_steps, 0)

                # Forward sequence (Step 1-2)
                if not self.press_key(game_window, 'w', 15.70, running, current_step=1, total_steps=total_steps):
                    return
                if not self.safe_sleep(120, running, current_step=2, total_steps=total_steps):
                    return

                # First space press and sleep (Step 3-4)
                if not self.press_key(game_window, 'space', None, running, current_step=3, total_steps=total_steps):
                    return
                if not self.safe_sleep(120, running, current_step=4, total_steps=total_steps):
                    return

                # Second space press and sleep (Step 5-6)
                if not self.press_key(game_window, 'space', None, running, current_step=5, total_steps=total_steps):
                    return
                if not self.safe_sleep(30, running, current_step=6, total_steps=total_steps):
                    return

                # Backward sequence (Step 7-8)
                if not self.press_key(game_window, 's', 16.11, running, current_step=7, total_steps=total_steps):
                    return
                if not self.safe_sleep(120, running, current_step=8, total_steps=total_steps):
                    return

                # First space press and sleep (Step 9-10)
                if not self.press_key(game_window, 'space', None, running, current_step=9, total_steps=total_steps):
                    return
                if not self.safe_sleep(120, running, current_step=10, total_steps=total_steps):
                    return

                # Second space press and sleep (Step 11-12)
                if not self.press_key(game_window, 'space', None, running, current_step=11, total_steps=total_steps):
                    return
                if not self.safe_sleep(30, running, current_step=12, total_steps=total_steps):
                    return

            except Exception as e:
                print(f"Error in BF6SiegeCairoMacro: {e}")
                time.sleep(1)


class BF6LibPeakMacro(Macro):
    def __init__(self):
        super().__init__(
            "Battlefield 6 Liberation Peak AFK",
            "Liberation Peak AFK Macro for Battlefield 6 that automates capturing objectives. Portal Code: YWVXU - Tutorial: https://youtu.be/TTv9BSTzFTg?si=fdGpfcFno4Y9w3cI&t=61"
        )

    def run(self, game_window: Any, running: threading.Event) -> None:
        total_steps = 4  # Total number of major steps in the cycle

        while running.is_set():
            try:
                self.update_status(
                    "Starting Liberation Peak cycle...", total_steps, 0)

                # Forward sequence (Step 1)
                if not self.press_key(game_window, 'w', 7, running, current_step=1, total_steps=total_steps):
                    return

                # Press space 4 times with delays (Step 2)
                if not self.press_key(game_window, 'space', None, running, count=4, delay=30,
                                      current_step=2, total_steps=total_steps):
                    return

                # Backward sequence (Step 3)
                if not self.press_key(game_window, 's', 7, running, current_step=3, total_steps=total_steps):
                    return

                # Press space 4 more times with delays (Step 4)
                if not self.press_key(game_window, 'space', None, running, count=4, delay=30,
                                      current_step=4, total_steps=total_steps):
                    return
            except Exception as e:
                print(f"Error in BF6LibPeakMacro: {e}")
                time.sleep(1)


class BF6SpaceBarMacro(Macro):
    def __init__(self):
        super().__init__(
            "Battlefield 6 Space Bar AFK",
            "Space Bar AFK Macro for Battlefield 6. Portal Code: YRV4A"
        )

    def run(self, game_window: Any, running: threading.Event) -> None:
        total_steps = 1  # Single step that repeats

        while running.is_set():
            try:
                self.update_status(
                    "Starting Space Bar cycle...", total_steps, 0)

                # Press space repeatedly with delays
                if not self.press_key(game_window, 'space', None, running, count=120, delay=30,
                                      current_step=1, total_steps=total_steps):
                    return
            except Exception as e:
                print(f"Error in BF6SpaceBarMacro: {e}")
                time.sleep(1)


# Add more macro classes here...

# Dictionary of all available macros
AVAILABLE_MACROS: Dict[str, Macro] = {
    "bf6_lib_peak": BF6LibPeakMacro(),
    "bf6_siege_cairo": BF6SiegeCairoMacro(),
    "bf6_space_bar": BF6SpaceBarMacro(),
    # Add more macros here...
}
