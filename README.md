# MacroManager

> A simple macro automation tool for games

A customizable macro tool for automating repetitive actions in games. Easy to set up and use!

## ✨ Features

- **Auto-Update**: Automatically checks for updates on startup and installs them with one click
- **Easy-to-use GUI**: Simple interface with real-time status updates
- **Customizable Hotkeys**: Configure your own key bindings
- **Multiple Macros**: Pre-configured macros for Battlefield 6 game modes
- **Live Monitoring**: See what the macro is doing in real-time

## 📋 Requirements

- **Windows OS** (uses Windows API for input simulation)
- **Python 3.8+** ([Download from python.org](https://www.python.org/downloads/))

## 🚀 Quick Setup

1. **Download the repository**

   ```bash
   git clone https://github.com/panteLx/MacroManager.git
   cd MacroManager
   ```

2. **Run the app**

   Just double-click `start_macromanager.bat` or run in terminal:

   ```bash
   start_macromanager.bat
   ```

That's it! The first time you run it, it will automatically:

- Create a virtual environment
- Install all dependencies
- Open the app with a setup wizard

## 🎮 Usage

### Starting the Application

Just run `start_macromanager.bat` - it handles everything automatically!### First-Time Setup

On first launch, you'll be prompted to configure your hotkeys:

- **Start Macro**: Default F1 (customizable)
- **Stop Macro**: Default F2 (customizable)
- **Change Keys**: F12

Settings are saved in `config/macro_config.json` and persist between sessions.

### Using Macros

1. **Launch your game** (e.g., Battlefield 6)
2. **Select a macro** from the dropdown menu
3. **Read the description** to understand what it does
4. **Start the macro**:
   - Click the "Start" button, OR
   - Press your configured start key (default: F1)
5. **Monitor progress** in the status panel and log window
6. **Stop the macro**:
   - Click the "Stop" button, OR
   - Press your configured stop key (default: F2)

### Changing Key Bindings

- Click "Change Keys" button or press F12
- Click "Set New Key" for the binding you want to change
- Press the desired key (avoid ESC and system keys)
- Click "Save Changes"

## Available Macros

### Battlefield 6 - Siege of Cairo AFK

Automates capturing objectives in the Siege of Cairo game mode.

- **Portal Code**: YVNDS
- **Tutorial**: [YouTube](https://youtu.be/LH_Gj87xodI?si=GJvNM4reqZoQxJ7f&t=161)

### Battlefield 6 - Liberation Peak AFK

Automates capturing objectives in the Liberation Peak game mode.

- **Portal Code**: YWVXU
- **Tutorial**: [YouTube](https://youtu.be/TTv9BSTzFTg?si=fdGpfcFno4Y9w3cI&t=61)

### Battlefield 6 - Space Bar AFK

Simple space bar automation macro.

- **Portal Code**: YRV4A
- **Description**: Repeatedly presses space bar

## ⚠️ Disclaimer

**This tool is for educational purposes only.** Using macros in online games may violate the game's terms of service and could result in penalties including account bans. Use at your own risk.

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👨‍💻 Author

**panteLx** - [@panteLx](https://github.com/panteLx)

---

**Having issues?** Check the logs in `logs/macro_manager.log` or open an [Issue](https://github.com/panteLx/MacroManager/issues) on GitHub.
