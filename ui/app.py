"""
GenCAD UI – main application entry-point.

Run with:
    python -m ui.app

or directly:
    python ui/app.py

The app launches a Gradio web interface that shows:
  • Left panel  – interactive 3D canvas (STL viewer with pan/zoom/rotate)
  • Right panel – chatbot area for natural-language CAD commands
"""

import os
import sys

# Make the project root importable when this script is run directly.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import gradio as gr

from ui.cad_engine import CADEngine
from ui.chat_handler import ChatHandler, WELCOME_TEXT

# ---------------------------------------------------------------------------
# Singleton engine and handler (one per server process / session)
# ---------------------------------------------------------------------------

_engine = CADEngine()
_handler = ChatHandler(_engine)

# ---------------------------------------------------------------------------
# Gradio event callbacks
# ---------------------------------------------------------------------------


def on_send(
    user_message: str,
    history: list,
    current_model: str | None,
) -> tuple[str, list, str | None]:
    """Handle a new user message and update chat history + canvas."""
    reply, updated_model = _handler.process_message(user_message, current_model)
    history = history + [
        {"role": "user", "content": user_message},
        {"role": "assistant", "content": reply},
    ]
    return "", history, updated_model


def on_export(_current_model: str | None) -> str | None:
    """Export the current shape to STL and update the canvas component."""
    ok, path = _engine.export_stl()
    return path if ok else None


def on_clear_canvas(history: list) -> tuple[list, None]:
    """Clear canvas without touching chat history."""
    _engine.clear()
    return history + [{"role": "assistant", "content": "✅ Canvas cleared."}], None


# ---------------------------------------------------------------------------
# UI layout (Gradio Blocks)
# ---------------------------------------------------------------------------

_css = """
#canvas-col { background: #1a1a2e; border-radius: 8px; padding: 8px; }
#chat-col   { background: #16213e; border-radius: 8px; padding: 8px; }
footer { display: none !important; }
"""

with gr.Blocks(title="GenCAD – AI-Powered CAD Design") as demo:

    gr.Markdown(
        """
        # 🔧 GenCAD — AI-Powered CAD Design
        Design 3D models using natural language.  
        Type a command in the chatbot on the right — the model will appear on the canvas.
        """
    )

    with gr.Row(equal_height=True):

        # ---- Left panel: 3-D canvas ------------------------------------
        with gr.Column(scale=3, elem_id="canvas-col"):
            gr.Markdown("### 🗂️ CAD Canvas")
            canvas = gr.Model3D(
                label="3D View",
                clear_color=[0.12, 0.14, 0.18, 1.0],
                height=480,
            )
            with gr.Row():
                btn_export = gr.Button("📥 Export STL", variant="secondary", size="sm")
                btn_clear = gr.Button("🗑️ Clear", variant="secondary", size="sm")

        # ---- Right panel: chatbot --------------------------------------
        with gr.Column(scale=2, elem_id="chat-col"):
            gr.Markdown("### 💬 Design Assistant")
            chatbot = gr.Chatbot(
                label="Chat",
                height=380,
                layout="bubble",
            )
            user_input = gr.Textbox(
                placeholder="e.g.  create box 20 10 5   |   create sphere 8   |   help",
                label="Your command",
                lines=2,
                max_lines=4,
                autofocus=True,
            )
            btn_send = gr.Button("Send ➤", variant="primary")

            gr.Markdown(
                """
                **Quick reference**

                | Shape | Command |
                |-------|---------|
                | Box | `create box 20 10 5` |
                | Cylinder | `create cylinder 5 20` |
                | Sphere | `create sphere 8` |
                | Cone | `create cone 10 0 25` |
                | Torus | `create torus 15 4` |

                Type `help` for the full command list.
                """
            )

    # ---- Wire up events ------------------------------------------------

    btn_send.click(
        on_send,
        inputs=[user_input, chatbot, canvas],
        outputs=[user_input, chatbot, canvas],
    )
    user_input.submit(
        on_send,
        inputs=[user_input, chatbot, canvas],
        outputs=[user_input, chatbot, canvas],
    )

    btn_clear.click(
        on_clear_canvas,
        inputs=[chatbot],
        outputs=[chatbot, canvas],
    )

    btn_export.click(
        on_export,
        inputs=[canvas],
        outputs=[canvas],
    )

    # ---- Seed chat with welcome message --------------------------------
    demo.load(
        lambda: [{"role": "assistant", "content": WELCOME_TEXT}],
        outputs=[chatbot],
    )


# ---------------------------------------------------------------------------
# Entry-point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        theme=gr.themes.Soft(
            primary_hue="blue",
            secondary_hue="slate",
            neutral_hue="slate",
        ),
        css=_css,
    )
