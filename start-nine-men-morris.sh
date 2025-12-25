#!/bin/sh

echo ""
echo "========================================"
echo "     Python Environment Launcher"
echo "========================================"
echo ""

# ---------------------------------------------------------
# 1. Detect a valid Python 3 interpreter
# ---------------------------------------------------------

is_valid_python() {
    case "$1" in
        *WindowsApps/python* ) return 1 ;;   # Skip fake Windows Store python
    esac

    "$1" -c "import sys; exit(0 if sys.version_info.major == 3 else 1)" 2>/dev/null
    return $?
}

find_python() {
    CANDIDATES="
python3
python
py -3
"

    for candidate in $CANDIDATES; do
        if command -v $candidate >/dev/null 2>&1; then
            resolved=$(command -v $candidate)
            if is_valid_python "$resolved"; then
                echo "$candidate"
                return
            fi
        fi
    done

    echo ""
}

PY=$(find_python)

if [ -z "$PY" ]; then
    echo "❌ No valid Python 3 installation found."
    echo "   Please install Python from https://www.python.org/downloads/"
    exit 1
fi

echo "✔ Using Python: $(command -v $PY)"
echo ""

# ---------------------------------------------------------
# 2. Paths
# ---------------------------------------------------------

VENV_PATH=".venv"
SCRIPT_PATH="src/main.py"
REQ_FILE="requirements.txt"

# ---------------------------------------------------------
# 3. Create virtual environment if missing
# ---------------------------------------------------------

if [ ! -d "$VENV_PATH" ]; then
    echo "🔧 Creating virtual environment..."
    $PY -m venv "$VENV_PATH" || {
        echo "❌ Failed to create virtual environment"
        exit 1
    }
    echo "✔ Virtual environment created."
    echo ""
fi

# ---------------------------------------------------------
# 4. Activate venv (Windows/Linux/macOS)
# ---------------------------------------------------------

if [ -f "$VENV_PATH/bin/activate" ]; then
    ACTIVATE="$VENV_PATH/bin/activate"
elif [ -f "$VENV_PATH/Scripts/activate" ]; then
    ACTIVATE="$VENV_PATH/Scripts/activate"
else
    echo "❌ Could not find the activate script in the venv."
    exit 1
fi

echo "🔌 Activating virtual environment..."
. "$ACTIVATE"
echo "✔ Virtual environment activated."
echo ""

# ---------------------------------------------------------
# 5. Install dependencies
# ---------------------------------------------------------

if [ -f "$REQ_FILE" ]; then
    echo "📦 Installing dependencies from $REQ_FILE..."
    pip install -r "$REQ_FILE"
    echo "✔ Dependencies installed."
    echo ""
else
    echo "ℹ No requirements.txt found — skipping dependency installation."
    echo ""
fi

# ---------------------------------------------------------
# 6. Run the Python script
# ---------------------------------------------------------

echo "🚀 Starting application..."
echo ""
$PY "$SCRIPT_PATH"
echo ""
echo "========================================"
echo "   Application finished running."
echo "========================================"